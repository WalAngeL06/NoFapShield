from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Callable

from shield.core.config import Config
from shield.core.interfaces import FrictionEvent, TriggerSource

logger = logging.getLogger(__name__)

FrictionCallback = Callable[[FrictionEvent], None]


class Orchestrator:
    def __init__(self, config: Config | None = None, event_store=None) -> None:
        self._config = config or Config()
        self._event_store = event_store
        self._friction_callbacks: list[FrictionCallback] = []
        self._running = False

    @property
    def config(self) -> Config:
        return self._config

    def register_friction_callback(self, cb: FrictionCallback) -> None:
        self._friction_callbacks.append(cb)

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def trigger_demo(self) -> FrictionEvent:
        event = FrictionEvent(
            source=TriggerSource.DEMO,
            triggered_at=datetime.now(timezone.utc),
            session_id=str(uuid.uuid4()),
            score=self._config.demo_score,
            threshold_at_trigger=self._config.trigger_threshold,
            reason="manual demo trigger",
        )
        self.trigger(event)
        return event

    def trigger(self, event: FrictionEvent) -> bool:
        if event.score < event.threshold_at_trigger:
            return False

        if self._event_store is not None:
            self._event_store.record_event(event)

        for cb in list(self._friction_callbacks):
            try:
                cb(event)
            except Exception:
                logger.exception("Friction callback failed")
        return True
