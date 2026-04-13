# Shield — Backend Architecture Design
**Date:** 2026-04-13  
**Status:** Approved  
**Scope:** Backend only — `detection/`, `dns_proxy/`, `system/`, `privacy/`, `db/`, `core/`  
**Out of scope:** `ui/` — separate agent's responsibility

---

## 1. Project Overview

Shield is a Windows desktop application that helps users break pornographic content addiction by creating a conscious pause at the moment of urge. It runs entirely locally — no data leaves the device.

**Core flow:**
1. **Detection** — Hybrid score from NSFW model + domain/URL heuristics
2. **Friction** — Screen blur + 10–20 second wait triggered above threshold
3. **Redirection** — User's own goals shown, alternative action offered
4. **Privacy** — No images or history leave the device

---

## 2. Folder Structure

```
NoFapShield/
├── pyproject.toml
├── agents/
│   ├── db/CLAUDE.md
│   ├── privacy/CLAUDE.md
│   ├── detection/CLAUDE.md
│   ├── dns_proxy/CLAUDE.md
│   └── system/CLAUDE.md
├── src/shield/
│   ├── core/
│   │   ├── __init__.py          # public API: Orchestrator, Config
│   │   ├── orchestrator.py      # starts/stops all module threads
│   │   ├── config.py            # settings.json read/write
│   │   ├── interfaces.py        # ALL dataclasses defined here
│   │   └── event_loop.py        # main while-loop, FrictionEvent processing
│   ├── detection/
│   │   ├── __init__.py
│   │   ├── classifier.py        # NudeNet wrapper
│   │   ├── screenshot.py        # mss, RAM-only snapshot
│   │   └── scorer.py            # hybrid score calculation
│   ├── dns_proxy/
│   │   ├── __init__.py
│   │   ├── server.py            # 127.0.0.1:53 DNS proxy
│   │   └── blocklist.py         # StevenBlack list management
│   ├── system/
│   │   ├── __init__.py
│   │   ├── service.py           # NSSM install/uninstall
│   │   └── protection.py        # password protection, uninstall guard
│   ├── privacy/
│   │   ├── __init__.py
│   │   └── accountability.py    # SMTP + future notification channels (webhook, Telegram)
│   ├── db/
│   │   ├── __init__.py
│   │   ├── schema.py            # CREATE TABLE definitions
│   │   ├── models.py            # dataclass → SQLite row mapping
│   │   └── streak.py            # streak calculation logic
│   └── ui/                      # empty — separate agent's responsibility
├── tests/
│   ├── test_detection/
│   ├── test_dns_proxy/
│   ├── test_system/
│   ├── test_privacy/
│   ├── test_db/
│   └── test_core/
└── docs/superpowers/specs/
```

**Boundary rule:** No module imports another module. All cross-module contracts go through `core/interfaces.py`.

---

## 3. Dataclass Interfaces (`core/interfaces.py`)

All modules import from this single file. No module defines its own types.

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class TriggerSource(Enum):
    SCREENSHOT = "screenshot"
    DNS = "dns"

@dataclass
class ScreenshotResult:
    """Produced by detection/screenshot.py — RAM buffer, never written to disk"""
    image_bytes: bytes
    captured_at: datetime

@dataclass
class NSFWScore:
    """Produced by detection/classifier.py"""
    model_score: float          # NudeNet output [0.0–1.0]
    confidence: float

@dataclass
class DomainScore:
    """Produced by dns_proxy/server.py"""
    domain: str
    match_score: float          # 1.0 on blocklist hit, 0.0 otherwise

@dataclass
class HybridScore:
    """Calculated by detection/scorer.py"""
    final_score: float          # 0.6×model + 0.3×domain + 0.1×url
    nsfw: NSFWScore
    domain: DomainScore
    url_score: float
    source: TriggerSource
    computed_at: datetime

@dataclass
class FrictionEvent:
    """Consumed by core/event_loop.py, passed to UI callback"""
    score: HybridScore
    triggered_at: datetime
    session_id: str
    threshold_at_trigger: float  # snapshot of config threshold at trigger time

@dataclass
class UserGoal:
    """Provided by db/models.py — for UI display"""
    goal_text: str
    created_at: datetime

@dataclass
class StreakInfo:
    """Calculated by db/streak.py"""
    current_days: int
    longest_days: int
    last_reset: datetime
```

---

## 4. Threading Architecture

**Chosen approach:** Centralized Orchestrator (threading-based, not asyncio).  
Rationale: NudeNet and mss are synchronous blocking libraries; threading is natural. A single orchestrator owns lifecycle for all threads.

```
┌─────────────────────────────────────────────────────┐
│                    Orchestrator                      │
│  start() → launch threads                            │
│  stop()  → set shutdown_event, join threads          │
└──────┬──────────────┬──────────────┬────────────────┘
       │              │              │
       ▼              ▼              ▼
 DetectionThread   DNSThread    SystemThread
 (daemon=True)    (daemon=True) (daemon=True)
 screenshot every  continuous    NSSM health
 3 seconds         listening     check

       │              │
       └──────┬───────┘
              ▼
     Queue[HybridScore]   ← thread-safe
              │
              ▼
         EventLoop (main thread)
    score >= threshold?
         │
         ▼
   Queue[FrictionEvent]
         │
         ▼
    UI Callback  ← registered via Orchestrator.register_friction_callback(cb)
```

**Orchestrator API:**
```python
class Orchestrator:
    def __init__(self, config: Config, db: DBService): ...
    def register_friction_callback(self, cb: Callable[[FrictionEvent], None]): ...
    def start(self) -> None: ...   # launch all threads
    def stop(self) -> None: ...    # graceful shutdown, 5s timeout
    def is_running(self) -> bool: ...
```

**Key implementation details:**
- `shutdown_event: threading.Event` — all threads check `while not shutdown_event.is_set()`
- `score_queue: Queue[HybridScore]` — detection and DNS threads write here
- `friction_queue: Queue[FrictionEvent]` — event_loop writes here, UI callback consumes
- DNS score TTL: `last_dns_score: tuple[float, datetime]` held in orchestrator; expires to 0.0 after 10 seconds
- Thread exception handling: logged, thread restarted with exponential backoff
  ```python
  restart_delay = [1, 5, 30]  # seconds — increasing wait across 3 attempts
  ```

---

## 5. Database Schema

```sql
CREATE TABLE users (
    id            INTEGER PRIMARY KEY,
    password_hash TEXT NOT NULL,    -- bcrypt
    created_at    TEXT NOT NULL
);

CREATE TABLE streaks (
    id            INTEGER PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    started_at    TEXT NOT NULL,
    last_active   TEXT NOT NULL,
    current_days  INTEGER NOT NULL DEFAULT 0,
    longest_days  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE logs (
    id           INTEGER PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id),
    session_id   TEXT NOT NULL,
    triggered_at TEXT NOT NULL,
    final_score  REAL NOT NULL,
    threshold    REAL NOT NULL,     -- threshold_at_trigger value
    source       TEXT NOT NULL      -- TriggerSource.value
);

CREATE TABLE settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL             -- JSON serialized
);

CREATE TABLE questions (
    id         INTEGER PRIMARY KEY,
    text       TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

**DBService API** (exported from `db/__init__.py`):
```python
class DBService:
    def __init__(self, db_path: Path): ...
    def get_streak(self, user_id: int) -> StreakInfo: ...
    def record_friction(self, event: FrictionEvent) -> None: ...
    def update_streak(self, user_id: int) -> StreakInfo: ...
    def get_setting(self, key: str, default: Any) -> Any: ...
    def set_setting(self, key: str, value: Any) -> None: ...
    def get_goals(self, user_id: int) -> list[UserGoal]: ...
```

**Implementation decisions:**
- Direct `sqlite3` — no ORM, no extra dependency
- WAL mode enabled — threads can read concurrently
- Thread safety: each call opens and immediately closes its own connection

---

## 6. Sub-agent Execution Model

**Dependency order** (each agent must find the previous agent's interfaces ready):

```
db agent → privacy agent → detection agent → dns_proxy agent → system agent
                                                                      ↓
                                                              core/ (written by main agent)
```

**Execution protocol per agent:**
```bash
# 1. Run agent
claude --dangerously-skip-permissions -p "$(cat agents/MODULE/CLAUDE.md)"

# 2. Run tests
python -m pytest tests/test_MODULE/ -v

# 3. Pass → next agent
# 4. Fail → return error to same agent, fix, re-run tests
```

**No agent writes to another agent's directory.** Each CLAUDE.md defines explicit boundaries.

---

## 7. Test Coverage

| Module | What is tested |
|---|---|
| `db` | Streak calculation, friction log recording, WAL thread safety |
| `detection` | Score formula `0.6×model + 0.3×domain + 0.1×url`, threshold check |
| `dns_proxy` | Blocklist hit/miss, TTL expiry returns 0.0 |
| `privacy` | Screenshot never written to disk (tmp dir mock) |
| `system` | NSSM commands called with correct parameters (mock subprocess) |
| `core` | Orchestrator start/stop, friction callback triggered, backoff behavior |

---

## 8. Dependencies (`pyproject.toml`)

```toml
[project]
name = "shield"
requires-python = ">=3.11"

[project.dependencies]
nudenet = "*"
dnspython = "*"
mss = "*"
Pillow = "*"
bcrypt = "*"

[project.optional-dependencies]
dev = ["pytest", "pytest-cov", "pytest-timeout"]
```

`pytest-timeout` is required: DNS proxy and thread tests can hang indefinitely without it.

---

## 9. Critical Constraints

1. **Detection and privacy code never moves to the UI layer.** False positives alienate users; data leaks destroy trust.
2. **Screenshots stay in RAM only.** `ScreenshotResult.image_bytes` is never passed to any write call.
3. **All cross-module data flows through `core/interfaces.py`.** Modules do not import each other.
4. **UI is decoupled via callback.** `Orchestrator.register_friction_callback()` is the only surface UI touches.
5. **`ui/` directory is empty.** It is a separate agent's responsibility.
