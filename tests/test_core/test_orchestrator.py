import time
import threading
from unittest.mock import MagicMock, patch
from datetime import datetime
import pytest
from shield.core.orchestrator import Orchestrator
from shield.core.config import Config
from shield.core.interfaces import (
    HybridScore, NSFWScore, DomainScore, TriggerSource, FrictionEvent
)


def make_hybrid_score(final_score: float) -> HybridScore:
    return HybridScore(
        final_score=final_score,
        nsfw=NSFWScore(model_score=final_score, confidence=final_score),
        domain=DomainScore(domain="test.com", match_score=0.0),
        url_score=0.0,
        source=TriggerSource.SCREENSHOT,
        computed_at=datetime.utcnow(),
    )


def test_orchestrator_starts_and_stops():
    config = Config()
    db = MagicMock()
    orch = Orchestrator(config=config, db=db)
    orch.start()
    assert orch.is_running()
    orch.stop()
    assert not orch.is_running()


def test_friction_callback_called_above_threshold():
    config = Config(detection_threshold=0.5)
    db = MagicMock()
    orch = Orchestrator(config=config, db=db)

    received: list[FrictionEvent] = []
    orch.register_friction_callback(received.append)

    score = make_hybrid_score(0.9)
    orch._score_queue.put(score)

    orch.start()
    time.sleep(0.2)
    orch.stop()

    assert len(received) == 1
    assert received[0].threshold_at_trigger == 0.5


def test_friction_callback_not_called_below_threshold():
    config = Config(detection_threshold=0.8)
    db = MagicMock()
    orch = Orchestrator(config=config, db=db)

    received: list[FrictionEvent] = []
    orch.register_friction_callback(received.append)

    score = make_hybrid_score(0.3)
    orch._score_queue.put(score)

    orch.start()
    time.sleep(0.2)
    orch.stop()

    assert len(received) == 0


def test_friction_event_has_session_id():
    config = Config(detection_threshold=0.5)
    db = MagicMock()
    orch = Orchestrator(config=config, db=db)

    received: list[FrictionEvent] = []
    orch.register_friction_callback(received.append)
    orch._score_queue.put(make_hybrid_score(0.9))

    orch.start()
    time.sleep(0.2)
    orch.stop()

    assert received[0].session_id != ""


def test_dns_score_ttl_expires():
    """DNS score should return 0.0 after TTL expires."""
    config = Config(dns_score_ttl=0)  # TTL=0 means always expired
    db = MagicMock()
    orch = Orchestrator(config=config, db=db)

    # Set a DNS score
    from datetime import datetime, timedelta, timezone
    orch._last_dns_score = (1.0, datetime.now(timezone.utc) - timedelta(seconds=5))

    score = orch._current_dns_score()
    assert score.match_score == 0.0


def test_dns_score_valid_within_ttl():
    """DNS score should be returned when within TTL."""
    config = Config(dns_score_ttl=60)
    db = MagicMock()
    orch = Orchestrator(config=config, db=db)

    from datetime import datetime, timezone
    orch._last_dns_score = (1.0, datetime.now(timezone.utc))

    score = orch._current_dns_score()
    assert score.match_score == 1.0


def test_multiple_friction_callbacks():
    config = Config(detection_threshold=0.5)
    db = MagicMock()
    orch = Orchestrator(config=config, db=db)

    results_a: list[FrictionEvent] = []
    results_b: list[FrictionEvent] = []
    orch.register_friction_callback(results_a.append)
    orch.register_friction_callback(results_b.append)
    orch._score_queue.put(make_hybrid_score(0.9))

    orch.start()
    time.sleep(0.2)
    orch.stop()

    assert len(results_a) == 1
    assert len(results_b) == 1


def test_callback_exception_does_not_crash_orchestrator():
    """A crashing callback must not bring down the event loop."""
    config = Config(detection_threshold=0.5)
    db = MagicMock()
    orch = Orchestrator(config=config, db=db)

    def bad_callback(event):
        raise RuntimeError("I crashed")

    orch.register_friction_callback(bad_callback)
    orch._score_queue.put(make_hybrid_score(0.9))

    orch.start()
    time.sleep(0.2)
    orch.stop()

    assert not orch.is_running()  # stopped cleanly, did not hang
