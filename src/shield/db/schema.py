USERS = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL
)
"""

STREAKS = """
CREATE TABLE IF NOT EXISTS streaks (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    started_at    TEXT NOT NULL,
    last_active   TEXT NOT NULL,
    current_days  INTEGER NOT NULL DEFAULT 0,
    longest_days  INTEGER NOT NULL DEFAULT 0
)
"""

LOGS = """
CREATE TABLE IF NOT EXISTS logs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id),
    session_id   TEXT NOT NULL,
    triggered_at TEXT NOT NULL,
    final_score  REAL NOT NULL,
    threshold    REAL NOT NULL,
    source       TEXT NOT NULL
)
"""

SETTINGS = """
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
)
"""

QUESTIONS = """
CREATE TABLE IF NOT EXISTS questions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    text       TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""

ALL = [USERS, STREAKS, LOGS, SETTINGS, QUESTIONS]
