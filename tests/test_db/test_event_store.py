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


def test_checkin_roundtrip(tmp_path):
    store = EventStore(tmp_path / "shield.db")

    store.save_checkin("Bugün kendime sakin bir not yazıyorum.")

    rows = store.get_checkin_history()
    assert len(rows) == 1
    assert rows[0]["text"] == "Bugün kendime sakin bir not yazıyorum."
    assert rows[0]["created_at"]


def test_set_and_get_setting_roundtrip(tmp_path):
    store = EventStore(tmp_path / "shield.db")

    store.set_setting("goal_text", "Sakin bir alışkanlık.")
    store.set_setting("alternative_actions", ["Yürüyüş", "Su"])
    store.set_setting("detection_sensitivity", 0.5)

    assert store.get_setting("goal_text") == "Sakin bir alışkanlık."
    assert store.get_setting("alternative_actions") == ["Yürüyüş", "Su"]
    assert store.get_setting("detection_sensitivity") == 0.5


def test_get_setting_returns_default_when_missing(tmp_path):
    store = EventStore(tmp_path / "shield.db")

    assert store.get_setting("missing") is None
    assert store.get_setting("missing", default="fallback") == "fallback"


def test_set_setting_overwrites_existing_value(tmp_path):
    store = EventStore(tmp_path / "shield.db")

    store.set_setting("goal_text", "Önceki hedef")
    store.set_setting("goal_text", "Güncel hedef")

    assert store.get_setting("goal_text") == "Güncel hedef"


def test_list_settings_returns_all_settings(tmp_path):
    store = EventStore(tmp_path / "shield.db")

    store.set_setting("goal_text", "Hedef")
    store.set_setting("detection_sensitivity", 0.7)

    values = store.list_settings()

    assert values == {"goal_text": "Hedef", "detection_sensitivity": 0.7}


def test_settings_persist_across_instances(tmp_path):
    db_path = tmp_path / "shield.db"
    first = EventStore(db_path)
    first.set_setting("goal_text", "Kalıcı hedef")
    first.close()

    second = EventStore(db_path)
    assert second.get_setting("goal_text") == "Kalıcı hedef"
    second.close()
