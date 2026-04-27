from datetime import datetime, timezone

from shield.core import FrictionEvent, TriggerSource
from shield.db import EventStore


def make_event(session_id: str = "session-1") -> FrictionEvent:
    return FrictionEvent(
        source=TriggerSource.DEMO,
        triggered_at=datetime.now(timezone.utc),
        session_id=session_id,
        score=1.0,
        threshold_at_trigger=0.7,
        reason="manual demo trigger",
    )


def test_record_event_roundtrip(tmp_path):
    store = EventStore(tmp_path / "shield.db")
    event = make_event()

    store.record_event(event)

    rows = store.list_events()
    assert rows == [
        {
            "session_id": event.session_id,
            "triggered_at": event.triggered_at.isoformat(),
            "source": "demo",
            "score": 1.0,
            "threshold": 0.7,
            "reason": "manual demo trigger",
        }
    ]


def test_list_events_returns_newest_first(tmp_path):
    store = EventStore(tmp_path / "shield.db")
    store.record_event(make_event("older"))
    store.record_event(make_event("newer"))

    rows = store.list_events()

    assert [row["session_id"] for row in rows] == ["newer", "older"]
