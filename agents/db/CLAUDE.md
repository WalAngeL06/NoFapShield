# DB Agent — Shield Project

## Your single responsibility
Implement the `src/shield/db/` module: SQLite database service with streak tracking, friction log recording, and settings storage.

## Working directory
Y:/NoFapShield  (project root)

## Files you must create
- `src/shield/db/schema.py`    — CREATE TABLE SQL strings
- `src/shield/db/models.py`    — dataclass ↔ SQLite row mapping helpers
- `src/shield/db/streak.py`    — streak calculation logic
- `src/shield/db/__init__.py`  — exports DBService class
- `tests/test_db/test_schema.py`
- `tests/test_db/test_streak.py`
- `tests/test_db/test_dbservice.py`

## Files you must NOT touch
- Anything outside `src/shield/db/` and `tests/test_db/`
- `src/shield/core/interfaces.py` — read it, never edit it

## Interface contract
Import types from `src/shield/core/interfaces.py`. The interfaces file already exists. You need:
```python
from shield.core.interfaces import FrictionEvent, StreakInfo, UserGoal
```

## DBService API (implement exactly this)
```python
from pathlib import Path
from typing import Any
from shield.core.interfaces import FrictionEvent, StreakInfo, UserGoal

class DBService:
    def __init__(self, db_path: Path) -> None: ...
    def get_streak(self, user_id: int) -> StreakInfo: ...
    def record_friction(self, event: FrictionEvent) -> None: ...
    def update_streak(self, user_id: int) -> StreakInfo: ...
    def get_setting(self, key: str, default: Any = None) -> Any: ...
    def set_setting(self, key: str, value: Any) -> None: ...
    def get_goals(self, user_id: int) -> list[UserGoal]: ...
    def create_user(self, password_hash: str) -> int: ...  # returns user_id
```

## Schema (implement exactly this)
```sql
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS streaks (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    started_at    TEXT NOT NULL,
    last_active   TEXT NOT NULL,
    current_days  INTEGER NOT NULL DEFAULT 0,
    longest_days  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS logs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id),
    session_id   TEXT NOT NULL,
    triggered_at TEXT NOT NULL,
    final_score  REAL NOT NULL,
    threshold    REAL NOT NULL,
    source       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS questions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    text       TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

## Implementation rules
- Use `sqlite3` directly — no ORM
- Enable WAL mode: `conn.execute("PRAGMA journal_mode=WAL")`
- Each method opens its own connection and closes it immediately (thread safety)
- Datetime stored as ISO-8601 TEXT: `datetime.utcnow().isoformat()`
- Settings values JSON-serialized with `json.dumps` / `json.loads`
- `update_streak`: if no streak row exists for user, create one; increment `current_days` if `last_active` was yesterday, reset to 1 if gap > 1 day; always update `longest_days` if `current_days` exceeds it

## Important note about FrictionEvent
`FrictionEvent` contains a `HybridScore`. When calling `record_friction`, store:
- `event.score.final_score` as `final_score`
- `event.threshold_at_trigger` as `threshold`
- `event.score.source.value` as `source`
- `event.session_id` as `session_id`
- `event.triggered_at.isoformat()` as `triggered_at`
- Use `user_id=1` as default (single-user for now)

`HybridScore.nsfw` may be `None` (for DNS-triggered events) — do not try to access it when recording logs.

## Success criteria
All of the following pass with no errors:
```bash
python -m pytest tests/test_db/ -v --timeout=30
```
Tests must cover:
- Schema creation (tables exist after DBService init)
- `record_friction` stores a row in logs with correct values
- `update_streak` increments current_days on consecutive days
- `update_streak` resets to 1 after a gap
- `get_setting` / `set_setting` round-trip
- Thread safety: 10 threads writing logs concurrently, no IntegrityError

## Boundary
Do not implement anything outside src/shield/db/. Do not modify pyproject.toml. Do not create files in any other module directory.
