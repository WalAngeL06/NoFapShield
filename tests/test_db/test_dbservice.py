import sqlite3
import tempfile
import threading
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from shield.core.interfaces import (
    DomainScore,
    FrictionEvent,
    HybridScore,
    NSFWScore,
    TriggerSource,
)
from shield.db import DBService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_db() -> tuple[DBService, Path]:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    return DBService(db_path), db_path


def make_screenshot_event(session_id: str = "sess-001") -> FrictionEvent:
    score = HybridScore(
        final_score=0.85,
        domain=DomainScore(domain="example.com", match_score=1.0),
        url_score=0.5,
        source=TriggerSource.SCREENSHOT,
        computed_at=datetime.utcnow(),
        nsfw=NSFWScore(model_score=0.9, confidence=0.95),
    )
    return FrictionEvent(
        score=score,
        triggered_at=datetime.utcnow(),
        session_id=session_id,
        threshold_at_trigger=0.7,
    )


def make_dns_event(session_id: str = "sess-dns") -> FrictionEvent:
    score = HybridScore(
        final_score=0.6,
        domain=DomainScore(domain="bad.com", match_score=1.0),
        url_score=0.0,
        source=TriggerSource.DNS,
        computed_at=datetime.utcnow(),
        nsfw=None,
    )
    return FrictionEvent(
        score=score,
        triggered_at=datetime.utcnow(),
        session_id=session_id,
        threshold_at_trigger=0.5,
    )


def _read_logs(db_path: Path) -> list[tuple]:
    conn = sqlite3.connect(str(db_path))
    try:
        return conn.execute("SELECT * FROM logs ORDER BY id").fetchall()
    finally:
        conn.close()


def _insert_streak(db_path: Path, user_id: int, last_active: datetime,
                   current_days: int, longest_days: int) -> None:
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "INSERT INTO streaks "
            "(user_id, started_at, last_active, current_days, longest_days) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, last_active.isoformat(), last_active.isoformat(),
             current_days, longest_days),
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# record_friction
# ---------------------------------------------------------------------------

def test_record_friction_screenshot_stores_row():
    db, db_path = make_db()
    db.create_user("hash123")
    event = make_screenshot_event()

    db.record_friction(event)

    rows = _read_logs(db_path)
    assert len(rows) == 1
    row = rows[0]
    # id=0, user_id=1, session_id=2, triggered_at=3, final_score=4, threshold=5, source=6
    assert row[2] == event.session_id
    assert row[4] == pytest.approx(0.85)
    assert row[5] == pytest.approx(0.7)
    assert row[6] == "screenshot"


def test_record_friction_dns_event():
    db, db_path = make_db()
    db.create_user("hash123")
    event = make_dns_event()

    db.record_friction(event)

    rows = _read_logs(db_path)
    assert len(rows) == 1
    assert rows[0][6] == "dns"


def test_record_friction_multiple_events():
    db, db_path = make_db()
    db.create_user("hash")

    db.record_friction(make_screenshot_event("a"))
    db.record_friction(make_screenshot_event("b"))
    db.record_friction(make_dns_event("c"))

    rows = _read_logs(db_path)
    assert len(rows) == 3
    assert {r[2] for r in rows} == {"a", "b", "c"}


# ---------------------------------------------------------------------------
# Streak
# ---------------------------------------------------------------------------

def test_get_streak_returns_default_when_none():
    db, _ = make_db()
    db.create_user("hash")
    info = db.get_streak(1)
    assert info.current_days == 0
    assert info.longest_days == 0


def test_update_streak_creates_first_row():
    db, _ = make_db()
    db.create_user("hash")
    info = db.update_streak(1)
    assert info.current_days == 1
    assert info.longest_days == 1


def test_update_streak_same_day_idempotent():
    db, _ = make_db()
    db.create_user("hash")
    first = db.update_streak(1)
    second = db.update_streak(1)
    assert second.current_days == first.current_days
    assert second.longest_days == first.longest_days


def test_update_streak_consecutive_day_increments():
    db, db_path = make_db()
    db.create_user("hash")

    yesterday = datetime.utcnow() - timedelta(days=1)
    _insert_streak(db_path, user_id=1, last_active=yesterday,
                   current_days=5, longest_days=10)

    info = db.update_streak(1)
    assert info.current_days == 6
    assert info.longest_days == 10


def test_update_streak_extends_longest():
    db, db_path = make_db()
    db.create_user("hash")

    yesterday = datetime.utcnow() - timedelta(days=1)
    _insert_streak(db_path, user_id=1, last_active=yesterday,
                   current_days=10, longest_days=10)

    info = db.update_streak(1)
    assert info.current_days == 11
    assert info.longest_days == 11


def test_update_streak_resets_after_gap():
    db, db_path = make_db()
    db.create_user("hash")

    five_days_ago = datetime.utcnow() - timedelta(days=5)
    _insert_streak(db_path, user_id=1, last_active=five_days_ago,
                   current_days=7, longest_days=15)

    info = db.update_streak(1)
    assert info.current_days == 1
    assert info.longest_days == 15  # longest preserved


def test_update_streak_two_day_gap_resets():
    db, db_path = make_db()
    db.create_user("hash")

    two_days_ago = datetime.utcnow() - timedelta(days=2)
    _insert_streak(db_path, user_id=1, last_active=two_days_ago,
                   current_days=3, longest_days=3)

    info = db.update_streak(1)
    assert info.current_days == 1


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def test_get_setting_missing_returns_none():
    db, _ = make_db()
    assert db.get_setting("nope") is None


def test_get_setting_missing_returns_default():
    db, _ = make_db()
    assert db.get_setting("nope", "fallback") == "fallback"


def test_set_get_setting_roundtrip_dict():
    db, _ = make_db()
    db.set_setting("cfg", {"threshold": 0.75, "tags": ["a", "b"]})
    assert db.get_setting("cfg") == {"threshold": 0.75, "tags": ["a", "b"]}


def test_set_get_setting_roundtrip_scalar():
    db, _ = make_db()
    db.set_setting("num", 42)
    assert db.get_setting("num") == 42


def test_set_setting_overwrites():
    db, _ = make_db()
    db.set_setting("key", "v1")
    db.set_setting("key", "v2")
    assert db.get_setting("key") == "v2"


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------

def test_thread_safety_concurrent_writes():
    db, db_path = make_db()
    db.create_user("hash")

    errors: list[Exception] = []

    def write_log(idx: int) -> None:
        try:
            db.record_friction(make_screenshot_event(session_id=f"sess-{idx:03d}"))
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=write_log, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Thread errors: {errors}"

    conn = sqlite3.connect(str(db_path))
    try:
        count = conn.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
    finally:
        conn.close()

    assert count == 10
