"""
core.py — Root-level bridge between the UI layer and shield.core backend.

UI modules do `import core` and call the functions below.  This module owns
the singletons (Config, DBService, Orchestrator, UninstallProtection) for the
lifetime of the process.
"""
from __future__ import annotations

import bcrypt
from datetime import datetime, timezone
from pathlib import Path

from shield.core.config import Config
from shield.core.orchestrator import Orchestrator
from shield.db import DBService
from shield.system.protection import UninstallProtection

# ---------------------------------------------------------------------------
# Data directory + singletons
# ---------------------------------------------------------------------------

DATA_DIR: Path = Path.home() / ".shield"
DATA_DIR.mkdir(parents=True, exist_ok=True)

_CONFIG_PATH = DATA_DIR / "config.json"

config = Config.from_file(_CONFIG_PATH)
db = DBService(DATA_DIR / "shield.db")
orchestrator = Orchestrator(config, db)

_protection = UninstallProtection(db=db, user_id=1)


def _ensure_user_exists() -> None:
    """Guarantee that user row with id=1 is present (required by FK constraints)."""
    import sqlite3
    conn = sqlite3.connect(str(DATA_DIR / "shield.db"), timeout=10)
    try:
        row = conn.execute("SELECT id FROM users WHERE id = 1").fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO users (password_hash, created_at) VALUES (?, ?)",
                ("", datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
    finally:
        conn.close()


_ensure_user_exists()

# ---------------------------------------------------------------------------
# Public API — called by UI modules
# ---------------------------------------------------------------------------


def get_streak() -> int:
    """Current streak in days for user 1."""
    return db.get_streak(user_id=1).current_days


def get_goals() -> list[str]:
    """Goals stored by onboarding / settings (settings key 'goals')."""
    raw = db.get_setting("goals", [])
    if isinstance(raw, list):
        return [str(g) for g in raw if str(g).strip()]
    return []


def get_checkin_history() -> list[dict]:
    """Morning check-in history (settings key 'checkin_history')."""
    raw = db.get_setting("checkin_history", [])
    return raw if isinstance(raw, list) else []


def get_trigger_log() -> list[dict]:
    """Most recent friction log entries (last 100)."""
    return db.get_logs(user_id=1)


def save_checkin(text: str) -> None:
    """Append a morning check-in entry to the history."""
    history = get_checkin_history()
    history.append({
        "text": text,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    db.set_setting("checkin_history", history)


def update_settings(key: str, value) -> None:
    """Persist a setting.

    Special-cased keys:
    - ``"password"`` → hashed with bcrypt, stored under
      ``UninstallProtection.PASSWORD_HASH_KEY``
    All other keys → stored verbatim in the settings table.
    """
    if key == "password":
        hashed = bcrypt.hashpw(str(value).encode(), bcrypt.gensalt()).decode()
        db.set_setting(UninstallProtection.PASSWORD_HASH_KEY, hashed)
    else:
        db.set_setting(key, value)


def verify_password(pw: str) -> bool:
    """Return True if *pw* matches the stored uninstall password hash."""
    return _protection.verify_password(pw)
