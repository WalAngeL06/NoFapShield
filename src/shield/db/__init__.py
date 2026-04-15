import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from shield.core.interfaces import FrictionEvent, StreakInfo, UserGoal
from shield.db import schema as _schema
from shield.db.models import goal_row_to_goal, streak_row_to_info
from shield.db.streak import compute_streak


class DBService:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_schema()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_schema(self) -> None:
        conn = self._connect()
        try:
            for stmt in _schema.ALL:
                conn.execute(stmt)
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # User management
    # ------------------------------------------------------------------

    def create_user(self, password_hash: str) -> int:
        now = datetime.now(timezone.utc).isoformat()
        conn = self._connect()
        try:
            cur = conn.execute(
                "INSERT INTO users (password_hash, created_at) VALUES (?, ?)",
                (password_hash, now),
            )
            conn.commit()
            return cur.lastrowid
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Streak
    # ------------------------------------------------------------------

    def get_streak(self, user_id: int) -> StreakInfo:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT id, user_id, started_at, last_active, current_days, longest_days "
                "FROM streaks WHERE user_id = ? ORDER BY id DESC LIMIT 1",
                (user_id,),
            ).fetchone()
        finally:
            conn.close()
        if row is None:
            return StreakInfo(
                current_days=0,
                longest_days=0,
                last_reset=datetime.now(timezone.utc),
            )
        return streak_row_to_info(row)

    def update_streak(self, user_id: int) -> StreakInfo:
        now = datetime.now(timezone.utc)
        today = now.date()
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT id, user_id, started_at, last_active, current_days, longest_days "
                "FROM streaks WHERE user_id = ? ORDER BY id DESC LIMIT 1",
                (user_id,),
            ).fetchone()

            if row is None:
                conn.execute(
                    "INSERT INTO streaks "
                    "(user_id, started_at, last_active, current_days, longest_days) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (user_id, now.isoformat(), now.isoformat(), 1, 1),
                )
                conn.commit()
                return StreakInfo(current_days=1, longest_days=1, last_reset=now)

            streak_id = row[0]
            started_at = datetime.fromisoformat(row[2])
            last_active = datetime.fromisoformat(row[3])
            current_days = row[4]
            longest_days = row[5]

            new_current, new_longest = compute_streak(
                current_days, longest_days, last_active.date(), today
            )

            # Same day — nothing to update
            if new_current == current_days and new_longest == longest_days:
                conn.commit()
                return streak_row_to_info(row)

            # Reset: update started_at to now
            if new_current == 1:
                started_at = now

            conn.execute(
                "UPDATE streaks "
                "SET last_active = ?, current_days = ?, longest_days = ?, started_at = ? "
                "WHERE id = ?",
                (
                    now.isoformat(),
                    new_current,
                    new_longest,
                    started_at.isoformat(),
                    streak_id,
                ),
            )
            conn.commit()
            return StreakInfo(
                current_days=new_current,
                longest_days=new_longest,
                last_reset=started_at,
            )
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Friction log
    # ------------------------------------------------------------------

    def record_friction(self, event: FrictionEvent) -> None:
        """Record a friction event to the logs table.

        Note: records with user_id=1 (single-user app). Caller must ensure
        user 1 exists (created via create_user) before calling this method.
        """
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO logs "
                "(user_id, session_id, triggered_at, final_score, threshold, source) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    1,
                    event.session_id,
                    event.triggered_at.isoformat(),
                    event.score.final_score,
                    event.threshold_at_trigger,
                    event.score.source.value,
                ),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def get_setting(self, key: str, default: Any = None) -> Any:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
        finally:
            conn.close()
        if row is None:
            return default
        return json.loads(row[0])

    def set_setting(self, key: str, value: Any) -> None:
        serialized = json.dumps(value)
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, serialized),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Goals
    # ------------------------------------------------------------------

    def get_goals(self) -> list[UserGoal]:
        """Return all goals (questions) in the database."""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT id, text, created_at FROM questions ORDER BY id"
            ).fetchall()
        finally:
            conn.close()
        return [goal_row_to_goal(row) for row in rows]

    # ------------------------------------------------------------------
    # Trigger log
    # ------------------------------------------------------------------

    def get_logs(self, user_id: int, limit: int = 100) -> list[dict]:
        """Return the most recent friction log entries for *user_id*."""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT session_id, triggered_at, final_score, threshold, source "
                "FROM logs WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        finally:
            conn.close()
        return [
            {
                "session_id": r[0],
                "triggered_at": r[1],
                "final_score": r[2],
                "threshold": r[3],
                "source": r[4],
            }
            for r in rows
        ]
