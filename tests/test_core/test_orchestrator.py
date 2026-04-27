from datetime import datetime, timezone

from shield.core import Config, FrictionEvent, Orchestrator, TriggerSource
from shield.db import EventStore


def make_event(score: float = 1.0, threshold: float = 0.7) -> FrictionEvent:
    return FrictionEvent(
        source=TriggerSource.DEMO,
        triggered_at=datetime.now(timezone.utc),
        session_id="test-session",
        score=score,
        threshold_at_trigger=threshold,
        reason="test",
    )


def test_start_stop_tracks_running_state():
    orchestrator = Orchestrator()

    orchestrator.start()
    assert orchestrator.is_running()

    orchestrator.stop()
    assert not orchestrator.is_running()


def test_demo_trigger_records_and_notifies(tmp_path):
    store = EventStore(tmp_path / "shield.db")
    orchestrator = Orchestrator(config=Config(), event_store=store)
    received: list[FrictionEvent] = []
    orchestrator.register_friction_callback(received.append)

    event = orchestrator.trigger_demo()

    assert received == [event]
    rows = store.list_events()
    assert len(rows) == 1
    assert rows[0]["session_id"] == event.session_id
    assert rows[0]["source"] == "demo"


def test_event_below_threshold_is_ignored(tmp_path):
    store = EventStore(tmp_path / "shield.db")
    orchestrator = Orchestrator(event_store=store)
    received: list[FrictionEvent] = []
    orchestrator.register_friction_callback(received.append)

    emitted = orchestrator.trigger(make_event(score=0.1, threshold=0.7))

    assert emitted is False
    assert received == []
    assert store.count_events() == 0


def test_callback_exception_does_not_block_other_callbacks(tmp_path):
    store = EventStore(tmp_path / "shield.db")
    orchestrator = Orchestrator(event_store=store)
    received: list[FrictionEvent] = []

    def broken_callback(event: FrictionEvent) -> None:
        raise RuntimeError("boom")

    orchestrator.register_friction_callback(broken_callback)
    orchestrator.register_friction_callback(received.append)

    event = orchestrator.trigger_demo()

    assert received == [event]
    assert store.count_events() == 1
