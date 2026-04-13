# src/shield/core/event_loop.py
"""
Standalone entry point that wires Config, DBService, and Orchestrator,
then runs until KeyboardInterrupt or SIGTERM.
"""
from __future__ import annotations
import logging
import signal
import threading
from pathlib import Path

logger = logging.getLogger(__name__)


def run(config_path: Path | None = None) -> None:
    """Wire all services and run the Shield event loop.

    Blocks until SIGINT or SIGTERM is received.
    The friction callback is a logging hook only — UI registers its own callback
    via Orchestrator.register_friction_callback().
    """
    from shield.core.config import Config
    from shield.core.orchestrator import Orchestrator
    from shield.db import DBService

    config = Config.from_file(config_path or Path("settings.json"))
    db = DBService(db_path=Path(config.db_path))
    orchestrator = Orchestrator(config=config, db=db)

    def _on_friction(event):
        logger.info(
            "FrictionEvent: score=%.3f threshold=%.3f session=%s",
            event.score.final_score,
            event.threshold_at_trigger,
            event.session_id,
        )

    orchestrator.register_friction_callback(_on_friction)

    stop_event = threading.Event()

    def _handle_signal(sig, frame):
        logger.info("Received signal %s — shutting down", sig)
        stop_event.set()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    logger.info("Shield event loop starting")
    orchestrator.start()
    stop_event.wait()
    orchestrator.stop()
    logger.info("Shield event loop stopped")
