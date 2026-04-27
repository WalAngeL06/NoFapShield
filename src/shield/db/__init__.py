from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from shield.core.interfaces import FrictionEvent

FRICTION_SCHEMA = """
CREATE TABLE IF NOT EXISTS friction_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    triggered_at TEXT NOT NULL,
    source TEXT NOT NULL,
    score REAL NOT NULL,
    threshold REAL NOT NULL,
    reason TEXT NOT NULL
)
"""

CHECKIN_SCHEMA = """
CREATE TABLE IF NOT EXISTS checkins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    text TEXT NOT NULL
)
"""

SETTINGS_SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
)
"""

SCHEMAS = (FRICTION_SCHEMA, CHECKIN_SCHEMA, SETTINGS_SCHEMA)


class EventStore:
    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.db_path = str(db_path)
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        for schema in SCHEMAS:
            self._conn.execute(schema)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> EventStore:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def record_event(self, event: FrictionEvent) -> None:
        self._conn.execute(
            "INSERT INTO friction_events "
            "(session_id, triggered_at, source, score, threshold, reason) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                event.session_id,
                event.triggered_at.isoformat(),
                event.source.value,
                event.score,
                event.threshold_at_trigger,
                event.reason,
            ),
        )
        self._conn.commit()

    def record_friction(self, event: FrictionEvent) -> None:
        self.record_event(event)

    def list_events(self, limit: int = 100) -> list[dict]:
        rows = self._conn.execute(
            "SELECT session_id, triggered_at, source, score, threshold, reason "
            "FROM friction_events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_logs(self, user_id: int | None = None, limit: int = 100) -> list[dict]:
        return self.list_events(limit=limit)

    def count_events(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM friction_events").fetchone()
        return int(row[0])

    def save_checkin(self, text: str) -> None:
        self._conn.execute(
            "INSERT INTO checkins (created_at, text) VALUES (?, ?)",
            (datetime.now(timezone.utc).isoformat(), text),
        )
        self._conn.commit()

    def get_checkin_history(self, limit: int = 100) -> list[dict]:
        rows = self._conn.execute(
            "SELECT created_at, text FROM checkins ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]

    def set_setting(self, key: str, value: Any) -> None:
        self._conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, json.dumps(value)),
        )
        self._conn.commit()

    def get_setting(self, key: str, default: Any = None) -> Any:
        row = self._conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            return default
        return json.loads(row["value"])

    def list_settings(self) -> dict[str, Any]:
        rows = self._conn.execute("SELECT key, value FROM settings").fetchall()
        return {row["key"]: json.loads(row["value"]) for row in rows}


DBService = EventStore

__all__ = ["DBService", "EventStore"]
