# src/shield/core/orchestrator.py
from __future__ import annotations
import logging
import threading
import time
import uuid
from datetime import datetime
from queue import Queue, Empty
from typing import Callable

from shield.core.config import Config
from shield.core.interfaces import (
    DomainScore, FrictionEvent, HybridScore, TriggerSource
)

logger = logging.getLogger(__name__)

_RESTART_DELAYS = [1, 5, 30]  # seconds — backoff across 3 attempts


class Orchestrator:
    def __init__(self, config: Config, db) -> None:
        self._config = config
        self._db = db
        self._score_queue: Queue[HybridScore] = Queue()
        self._shutdown_event = threading.Event()
        self._friction_callbacks: list[Callable[[FrictionEvent], None]] = []
        self._threads: list[threading.Thread] = []
        self._event_loop_thread: threading.Thread | None = None
        # DNS TTL state: (match_score, timestamp)
        self._last_dns_score: tuple[float, datetime] = (0.0, datetime.utcnow())
        self._dns_lock = threading.Lock()

    def register_friction_callback(self, cb: Callable[[FrictionEvent], None]) -> None:
        self._friction_callbacks.append(cb)

    def start(self) -> None:
        self._shutdown_event.clear()
        self._start_detection_thread()
        self._event_loop_thread = threading.Thread(
            target=self._run_event_loop, daemon=True, name="EventLoop"
        )
        self._event_loop_thread.start()

    def stop(self) -> None:
        self._shutdown_event.set()
        if self._event_loop_thread:
            self._event_loop_thread.join(timeout=5)
        for t in self._threads:
            t.join(timeout=5)
        self._threads.clear()

    def is_running(self) -> bool:
        return not self._shutdown_event.is_set()

    def _start_detection_thread(self) -> None:
        t = threading.Thread(
            target=self._detection_worker, daemon=True, name="DetectionWorker"
        )
        t.start()
        self._threads.append(t)

    def _detection_worker(self) -> None:
        attempt = 0
        while not self._shutdown_event.is_set():
            try:
                self._run_detection_cycle()
                attempt = 0
                self._shutdown_event.wait(timeout=self._config.screenshot_interval)
            except Exception as exc:
                delay = _RESTART_DELAYS[min(attempt, len(_RESTART_DELAYS) - 1)]
                logger.error("Detection worker error (attempt %d): %s", attempt, exc)
                attempt += 1
                if attempt > len(_RESTART_DELAYS):
                    logger.critical("Detection worker exhausted retries, stopping.")
                    break
                self._shutdown_event.wait(timeout=delay)

    def _run_detection_cycle(self) -> None:
        # Lazy import to allow mocking in tests
        from shield.detection import DetectionService  # type: ignore[import]
        if not hasattr(self, "_detection_svc"):
            self._detection_svc = DetectionService()
        dns_score = self._current_dns_score()
        hybrid = self._detection_svc.run_once(
            domain_score=dns_score, url_score=0.0
        )
        self._score_queue.put(hybrid)

    def _current_dns_score(self) -> DomainScore:
        with self._dns_lock:
            score, ts = self._last_dns_score
            age = (datetime.utcnow() - ts).total_seconds()
            if age > self._config.dns_score_ttl:
                return DomainScore(domain="", match_score=0.0)
            return DomainScore(domain="", match_score=score)

    def update_dns_score(self, domain: str, match_score: float) -> None:
        """Called by DNS thread to update the current domain score."""
        with self._dns_lock:
            self._last_dns_score = (match_score, datetime.utcnow())

    def _run_event_loop(self) -> None:
        while not self._shutdown_event.is_set():
            try:
                score = self._score_queue.get(timeout=0.1)
            except Empty:
                continue
            threshold = self._config.detection_threshold
            if score.final_score >= threshold:
                event = FrictionEvent(
                    score=score,
                    triggered_at=datetime.utcnow(),
                    session_id=str(uuid.uuid4()),
                    threshold_at_trigger=threshold,
                )
                for cb in self._friction_callbacks:
                    try:
                        cb(event)
                    except Exception as exc:
                        logger.error("Friction callback error: %s", exc)
