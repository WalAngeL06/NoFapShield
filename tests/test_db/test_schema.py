import sqlite3
import tempfile
from pathlib import Path

from shield.db import DBService


def _tables(db_path: Path) -> set[str]:
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        return {row[0] for row in rows}
    finally:
        conn.close()


def test_all_tables_created():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    DBService(db_path)

    tables = _tables(db_path)
    assert "users" in tables
    assert "streaks" in tables
    assert "logs" in tables
    assert "settings" in tables
    assert "questions" in tables


def test_idempotent_init():
    """Calling DBService twice on the same path must not raise."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    DBService(db_path)
    DBService(db_path)  # second init — CREATE TABLE IF NOT EXISTS must be safe

    tables = _tables(db_path)
    assert len({"users", "streaks", "logs", "settings", "questions"} - tables) == 0
