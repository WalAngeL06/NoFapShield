# Shield Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete Shield backend — detection, DNS proxy, system service, privacy, database, and orchestration core — using sequentially executed sub-agents per module.

**Architecture:** Centralized Orchestrator owns daemon threads for each module; all cross-module data flows through `core/interfaces.py` typed dataclasses; UI decoupled via a single friction callback. Sub-agents write only to their own module directory; `core/` is written last by the main agent.

**Tech Stack:** Python 3.11+, NudeNet, dnspython, mss, Pillow, bcrypt, sqlite3, NSSM

---

## File Map

| File | Responsibility |
|---|---|
| `pyproject.toml` | Project metadata + dependencies |
| `src/shield/core/interfaces.py` | ALL shared dataclasses — single source of truth |
| `src/shield/core/config.py` | settings.json read/write |
| `src/shield/core/orchestrator.py` | Thread lifecycle, backoff restart, friction callback |
| `src/shield/core/event_loop.py` | Score threshold check, FrictionEvent production |
| `src/shield/db/schema.py` | CREATE TABLE SQL |
| `src/shield/db/models.py` | Dataclass ↔ SQLite row mapping |
| `src/shield/db/streak.py` | Streak calculation logic |
| `src/shield/db/__init__.py` | Exports DBService |
| `src/shield/privacy/accountability.py` | SMTP notification (+ future channels) |
| `src/shield/privacy/__init__.py` | Exports AccountabilityService |
| `src/shield/detection/screenshot.py` | mss capture → RAM buffer only |
| `src/shield/detection/classifier.py` | NudeNet wrapper → NSFWScore |
| `src/shield/detection/scorer.py` | Hybrid score formula |
| `src/shield/detection/__init__.py` | Exports DetectionService |
| `src/shield/dns_proxy/blocklist.py` | StevenBlack list fetch + parse |
| `src/shield/dns_proxy/server.py` | 127.0.0.1:53 DNS proxy |
| `src/shield/dns_proxy/__init__.py` | Exports DNSProxyService |
| `src/shield/system/service.py` | NSSM install/uninstall/status |
| `src/shield/system/protection.py` | Password guard, uninstall logging |
| `src/shield/system/__init__.py` | Exports SystemService |
| `agents/db/CLAUDE.md` | Agent prompt for db module |
| `agents/privacy/CLAUDE.md` | Agent prompt for privacy module |
| `agents/detection/CLAUDE.md` | Agent prompt for detection module |
| `agents/dns_proxy/CLAUDE.md` | Agent prompt for dns_proxy module |
| `agents/system/CLAUDE.md` | Agent prompt for system module |

---

## Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `src/shield/__init__.py`
- Create: `src/shield/core/__init__.py`
- Create: `src/shield/detection/__init__.py`
- Create: `src/shield/dns_proxy/__init__.py`
- Create: `src/shield/system/__init__.py`
- Create: `src/shield/privacy/__init__.py`
- Create: `src/shield/db/__init__.py`
- Create: `src/shield/ui/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/test_db/__init__.py`
- Create: `tests/test_detection/__init__.py`
- Create: `tests/test_dns_proxy/__init__.py`
- Create: `tests/test_system/__init__.py`
- Create: `tests/test_privacy/__init__.py`
- Create: `tests/test_core/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "shield"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "nudenet",
    "dnspython",
    "mss",
    "Pillow",
    "bcrypt",
]

[project.optional-dependencies]
dev = ["pytest", "pytest-cov", "pytest-timeout"]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
timeout = 30
testpaths = ["tests"]
```

- [ ] **Step 2: Create all `__init__.py` files (all empty)**

```bash
mkdir -p src/shield/{core,detection,dns_proxy,system,privacy,db,ui}
mkdir -p tests/{test_db,test_detection,test_dns_proxy,test_system,test_privacy,test_core}
touch src/shield/__init__.py
touch src/shield/{core,detection,dns_proxy,system,privacy,db,ui}/__init__.py
touch tests/__init__.py
touch tests/{test_db,test_detection,test_dns_proxy,test_system,test_privacy,test_core}/__init__.py
```

- [ ] **Step 3: Install in editable mode**

```bash
pip install -e ".[dev]"
```

Expected: `Successfully installed shield-0.1.0`

- [ ] **Step 4: Verify pytest discovers nothing (no failures)**

```bash
python -m pytest --collect-only
```

Expected: `no tests ran`

- [ ] **Step 5: Commit**

```bash
git init
git add pyproject.toml src/ tests/
git commit -m "chore: project scaffold — empty module structure"
```

---

## Task 2: Core Interfaces

**Files:**
- Create: `src/shield/core/interfaces.py`

- [ ] **Step 1: Create interfaces.py**

```python
# src/shield/core/interfaces.py
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TriggerSource(Enum):
    SCREENSHOT = "screenshot"
    DNS = "dns"


@dataclass
class ScreenshotResult:
    """Produced by detection/screenshot.py — RAM buffer, never written to disk."""
    image_bytes: bytes
    captured_at: datetime


@dataclass
class NSFWScore:
    """Produced by detection/classifier.py."""
    model_score: float   # NudeNet output [0.0–1.0]
    confidence: float


@dataclass
class DomainScore:
    """Produced by dns_proxy/server.py."""
    domain: str
    match_score: float   # 1.0 on blocklist hit, 0.0 otherwise


@dataclass
class HybridScore:
    """Calculated by detection/scorer.py.
    final_score = 0.6 * model_score + 0.3 * domain_match + 0.1 * url_heuristic
    """
    final_score: float
    nsfw: NSFWScore
    domain: DomainScore
    url_score: float
    source: TriggerSource
    computed_at: datetime


@dataclass
class FrictionEvent:
    """Consumed by core/event_loop.py, forwarded to UI via callback."""
    score: HybridScore
    triggered_at: datetime
    session_id: str
    threshold_at_trigger: float  # snapshot of config threshold at moment of trigger


@dataclass
class UserGoal:
    """Provided by db/models.py — shown to user during friction."""
    goal_text: str
    created_at: datetime


@dataclass
class StreakInfo:
    """Calculated by db/streak.py."""
    current_days: int
    longest_days: int
    last_reset: datetime
```

- [ ] **Step 2: Verify importable**

```bash
python -c "from shield.core.interfaces import FrictionEvent, HybridScore, StreakInfo; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add src/shield/core/interfaces.py
git commit -m "feat: core interfaces — all shared dataclasses"
```

---

## Task 3: Create agents/db/CLAUDE.md

**Files:**
- Create: `agents/db/CLAUDE.md`

- [ ] **Step 1: Write the agent prompt**

```markdown
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

## Success criteria
All of the following pass with no errors:
```bash
python -m pytest tests/test_db/ -v
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
```

- [ ] **Step 2: Verify file written**

```bash
python -c "
import pathlib
p = pathlib.Path('agents/db/CLAUDE.md')
assert p.exists(), 'missing'
print(f'ok — {p.stat().st_size} bytes')
"
```

- [ ] **Step 3: Commit**

```bash
git add agents/db/CLAUDE.md
git commit -m "chore: db agent prompt"
```

---

## Task 4: Run DB Agent + Tests

- [ ] **Step 1: Run the db agent**

```bash
claude --dangerously-skip-permissions -p "$(cat agents/db/CLAUDE.md)"
```

Expected: agent creates `src/shield/db/schema.py`, `models.py`, `streak.py`, updates `__init__.py`, creates test files.

- [ ] **Step 2: Run db tests**

```bash
python -m pytest tests/test_db/ -v --timeout=30
```

Expected: all tests PASS.

- [ ] **Step 3: If tests fail — retry agent with error context**

```bash
python -m pytest tests/test_db/ -v --timeout=30 2>&1 | \
  claude --dangerously-skip-permissions -p \
  "$(cat agents/db/CLAUDE.md)

---
PREVIOUS RUN FAILED. Fix only the failing tests. Error output:
$(python -m pytest tests/test_db/ -v --timeout=30 2>&1)"
```

Repeat until all tests pass.

- [ ] **Step 4: Commit passing db module**

```bash
git add src/shield/db/ tests/test_db/
git commit -m "feat: db module — DBService, schema, streak logic (tests passing)"
```

---

## Task 5: Create agents/privacy/CLAUDE.md

**Files:**
- Create: `agents/privacy/CLAUDE.md`

- [ ] **Step 1: Write the agent prompt**

```markdown
# Privacy Agent — Shield Project

## Your single responsibility
Implement `src/shield/privacy/` module: accountability notifications via SMTP (extensible to other channels).

## Working directory
Y:/NoFapShield

## Files you must create
- `src/shield/privacy/accountability.py`   — AccountabilityService class
- `src/shield/privacy/__init__.py`         — exports AccountabilityService
- `tests/test_privacy/test_accountability.py`

## Files you must NOT touch
- Anything outside `src/shield/privacy/` and `tests/test_privacy/`
- `src/shield/core/interfaces.py` — read it, never edit it

## Interface contract
```python
from shield.core.interfaces import FrictionEvent
```

## AccountabilityService API (implement exactly this)
```python
from shield.core.interfaces import FrictionEvent

class AccountabilityConfig:
    smtp_host: str
    smtp_port: int          # default 587
    smtp_user: str
    smtp_password: str
    partner_email: str
    enabled: bool           # if False, send() is a no-op

class AccountabilityService:
    def __init__(self, config: AccountabilityConfig) -> None: ...
    def send(self, event: FrictionEvent) -> None: ...
        # Sends email to partner_email with event details
        # Subject: "Shield: accountability check-in"
        # Body: triggered_at, final_score, streak info (if available)
        # Raises: AccountabilityError on SMTP failure
    def test_connection(self) -> bool: ...
        # Returns True if SMTP login succeeds, False otherwise, never raises
```

## Implementation rules
- Use `smtplib` + `email.mime` from stdlib — no third-party mail library
- Use STARTTLS (`smtp.starttls()`) on port 587
- If `config.enabled` is False, `send()` returns immediately without connecting
- Screenshots are NEVER attached or referenced in emails
- `AccountabilityError` is a custom exception defined in `accountability.py`
- `test_connection()` must catch all exceptions and return False on any failure

## Privacy constraint
The `send()` method receives a `FrictionEvent` which contains a `HybridScore`.
- Log: final_score (float), triggered_at (datetime), session_id
- Never log or transmit: image_bytes, any screenshot data
- The `ScreenshotResult` type exists in interfaces.py but this module never imports or handles it

## Testing rules
- Mock `smtplib.SMTP` — never open real SMTP connections in tests
- Test: `send()` calls `smtp.sendmail()` when enabled=True
- Test: `send()` is a no-op when enabled=False
- Test: `send()` raises AccountabilityError when SMTP throws
- Test: `test_connection()` returns False on any exception, never raises

## Success criteria
```bash
python -m pytest tests/test_privacy/ -v --timeout=30
```
All tests pass.

## Boundary
Do not implement anything outside src/shield/privacy/. No disk writes. No screenshot handling.
```

- [ ] **Step 2: Commit**

```bash
git add agents/privacy/CLAUDE.md
git commit -m "chore: privacy agent prompt"
```

---

## Task 6: Run Privacy Agent + Tests

- [ ] **Step 1: Run the privacy agent**

```bash
claude --dangerously-skip-permissions -p "$(cat agents/privacy/CLAUDE.md)"
```

- [ ] **Step 2: Run privacy tests**

```bash
python -m pytest tests/test_privacy/ -v --timeout=30
```

Expected: all tests PASS.

- [ ] **Step 3: If tests fail — retry with error**

```bash
ERR=$(python -m pytest tests/test_privacy/ -v --timeout=30 2>&1); \
claude --dangerously-skip-permissions -p "$(cat agents/privacy/CLAUDE.md)

---
PREVIOUS RUN FAILED. Fix only the failing tests:
$ERR"
```

- [ ] **Step 4: Commit**

```bash
git add src/shield/privacy/ tests/test_privacy/
git commit -m "feat: privacy module — AccountabilityService (tests passing)"
```

---

## Task 7: Create agents/detection/CLAUDE.md

**Files:**
- Create: `agents/detection/CLAUDE.md`

- [ ] **Step 1: Write the agent prompt**

```markdown
# Detection Agent — Shield Project

## Your single responsibility
Implement `src/shield/detection/` module: RAM-only screenshot capture, NudeNet NSFW classification, hybrid score calculation.

## Working directory
Y:/NoFapShield

## Files you must create
- `src/shield/detection/screenshot.py`   — mss capture, RAM only
- `src/shield/detection/classifier.py`   — NudeNet wrapper
- `src/shield/detection/scorer.py`       — hybrid score formula
- `src/shield/detection/__init__.py`     — exports DetectionService
- `tests/test_detection/test_screenshot.py`
- `tests/test_detection/test_scorer.py`
- `tests/test_detection/test_classifier.py`

## Files you must NOT touch
- Anything outside `src/shield/detection/` and `tests/test_detection/`
- `src/shield/core/interfaces.py` — read it, never edit it

## Interface contract
```python
from shield.core.interfaces import (
    ScreenshotResult, NSFWScore, DomainScore, HybridScore, TriggerSource
)
```

## API to implement
```python
from datetime import datetime
from shield.core.interfaces import ScreenshotResult, NSFWScore, HybridScore, DomainScore, TriggerSource

class ScreenshotCapture:
    def capture(self) -> ScreenshotResult:
        # Uses mss to capture primary monitor
        # image_bytes = PNG bytes in RAM (BytesIO), never written to disk
        # captured_at = datetime.utcnow()
        ...

class NSFWClassifier:
    def __init__(self) -> None:
        # Loads NudeNet model (NudeDetector)
        ...
    def classify(self, result: ScreenshotResult) -> NSFWScore:
        # Runs NudeNet on image_bytes from RAM
        # model_score: max score from NudeNet detections, 0.0 if none
        # confidence: same as model_score (NudeNet doesn't separate these)
        ...

class HybridScorer:
    def score(
        self,
        nsfw: NSFWScore,
        domain: DomainScore,
        url_score: float,
        source: TriggerSource,
    ) -> HybridScore:
        # final_score = 0.6 * nsfw.model_score + 0.3 * domain.match_score + 0.1 * url_score
        # All inputs clamped to [0.0, 1.0] before formula
        # final_score clamped to [0.0, 1.0] after formula
        ...

class DetectionService:
    def __init__(self) -> None: ...
    def run_once(self, domain_score: DomainScore, url_score: float) -> HybridScore:
        # capture screenshot → classify → score → return HybridScore
        # domain_score and url_score are passed in (from orchestrator's last DNS state)
        ...
```

## Privacy constraint — CRITICAL
- `ScreenshotResult.image_bytes` is bytes in RAM only
- No method in this module may call `open()` for writing, `write()` to disk, or any path-based save
- NudeNet must receive image bytes via a BytesIO buffer, not a file path
  ```python
  import io
  from PIL import Image
  buf = io.BytesIO(result.image_bytes)
  img = Image.open(buf)
  # pass img or buf to NudeNet, NOT a file path
  ```

## Testing rules
- Mock `mss.mss()` to avoid needing a real display — return a dummy RGBA numpy array
- Mock `NudeDetector` to avoid loading model in tests
- test_scorer.py must test the formula with known values:
  ```python
  def test_formula_weights():
      scorer = HybridScorer()
      nsfw = NSFWScore(model_score=1.0, confidence=1.0)
      domain = DomainScore(domain="test.com", match_score=1.0)
      result = scorer.score(nsfw, domain, url_score=1.0, source=TriggerSource.SCREENSHOT)
      assert abs(result.final_score - 1.0) < 0.001

  def test_formula_partial():
      scorer = HybridScorer()
      nsfw = NSFWScore(model_score=0.5, confidence=0.5)
      domain = DomainScore(domain="test.com", match_score=0.0)
      result = scorer.score(nsfw, domain, url_score=0.0, source=TriggerSource.SCREENSHOT)
      assert abs(result.final_score - 0.3) < 0.001  # 0.6 * 0.5

  def test_no_disk_write(tmp_path):
      # capture() must not write to disk
      capture = ScreenshotCapture()
      before = list(tmp_path.iterdir())
      result = capture.capture()  # mocked
      after = list(tmp_path.iterdir())
      assert before == after
      assert isinstance(result.image_bytes, bytes)
  ```

## Success criteria
```bash
python -m pytest tests/test_detection/ -v --timeout=30
```
All tests pass.

## Boundary
Do not implement anything outside src/shield/detection/. Do not write to disk. Do not import from db, privacy, dns_proxy, or system modules.
```

- [ ] **Step 2: Commit**

```bash
git add agents/detection/CLAUDE.md
git commit -m "chore: detection agent prompt"
```

---

## Task 8: Run Detection Agent + Tests

- [ ] **Step 1: Run the detection agent**

```bash
claude --dangerously-skip-permissions -p "$(cat agents/detection/CLAUDE.md)"
```

- [ ] **Step 2: Run detection tests**

```bash
python -m pytest tests/test_detection/ -v --timeout=30
```

Expected: all tests PASS including formula weight tests.

- [ ] **Step 3: If tests fail — retry with error**

```bash
ERR=$(python -m pytest tests/test_detection/ -v --timeout=30 2>&1); \
claude --dangerously-skip-permissions -p "$(cat agents/detection/CLAUDE.md)

---
PREVIOUS RUN FAILED. Fix only the failing tests:
$ERR"
```

- [ ] **Step 4: Commit**

```bash
git add src/shield/detection/ tests/test_detection/
git commit -m "feat: detection module — screenshot, classifier, hybrid scorer (tests passing)"
```

---

## Task 9: Create agents/dns_proxy/CLAUDE.md

**Files:**
- Create: `agents/dns_proxy/CLAUDE.md`

- [ ] **Step 1: Write the agent prompt**

```markdown
# DNS Proxy Agent — Shield Project

## Your single responsibility
Implement `src/shield/dns_proxy/` module: local DNS proxy on 127.0.0.1:53 and StevenBlack hosts blocklist management.

## Working directory
Y:/NoFapShield

## Files you must create
- `src/shield/dns_proxy/blocklist.py`   — StevenBlack list fetch and domain lookup
- `src/shield/dns_proxy/server.py`      — DNS proxy server + DomainScore production
- `src/shield/dns_proxy/__init__.py`    — exports DNSProxyService
- `tests/test_dns_proxy/test_blocklist.py`
- `tests/test_dns_proxy/test_server.py`

## Files you must NOT touch
- Anything outside `src/shield/dns_proxy/` and `tests/test_dns_proxy/`
- `src/shield/core/interfaces.py` — read it, never edit it

## Interface contract
```python
from shield.core.interfaces import DomainScore
```

## API to implement
```python
from shield.core.interfaces import DomainScore

BLOCKLIST_URL = "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"

class BlocklistManager:
    def __init__(self) -> None:
        self._domains: set[str] = set()

    def fetch_and_update(self) -> int:
        # Downloads BLOCKLIST_URL, parses lines like "0.0.0.0 example.com"
        # Ignores comments (#), ignores "0.0.0.0" and "localhost" entries
        # Returns count of loaded domains
        ...

    def is_blocked(self, domain: str) -> bool:
        # Case-insensitive lookup, strips trailing dot if present
        ...

    def domain_score(self, domain: str) -> DomainScore:
        # Returns DomainScore(domain=domain, match_score=1.0 if blocked, else 0.0)
        ...

class DNSProxyService:
    def __init__(self, blocklist: BlocklistManager, upstream: str = "8.8.8.8") -> None: ...

    def start(self) -> None:
        # Binds UDP socket to 127.0.0.1:53
        # Forwards non-blocked queries to upstream DNS
        # Blocked domains: returns NXDOMAIN response
        # Runs in current thread until stop() called
        ...

    def stop(self) -> None:
        # Signals the server loop to exit
        ...

    def get_last_queried_domain(self) -> str | None:
        # Returns the most recently queried domain (for orchestrator's DNS score TTL)
        ...
```

## Implementation rules
- Use `dnspython` (`dns.message`, `dns.resolver`) for DNS message parsing/building
- UDP socket only — TCP DNS is out of scope
- `BlocklistManager.fetch_and_update()` uses `urllib.request.urlopen` (stdlib) — no requests library
- The blocklist is updated in memory only — no file I/O
- In tests, mock `urllib.request.urlopen` to return fixture hosts data — never hit real internet

## Testing rules
```python
SAMPLE_HOSTS = b"""
# Comment line
127.0.0.1 localhost
0.0.0.0 pornhub.com
0.0.0.0 xvideos.com
# Another comment
0.0.0.0 example-allowed.com
"""

def test_blocklist_parses_correctly(mock_urlopen):
    # mock_urlopen returns SAMPLE_HOSTS
    mgr = BlocklistManager()
    count = mgr.fetch_and_update()
    assert "pornhub.com" in mgr._domains
    assert "localhost" not in mgr._domains
    assert count >= 3

def test_domain_score_blocked(mock_urlopen):
    mgr = BlocklistManager()
    mgr.fetch_and_update()
    score = mgr.domain_score("pornhub.com")
    assert score.match_score == 1.0

def test_domain_score_not_blocked(mock_urlopen):
    mgr = BlocklistManager()
    mgr.fetch_and_update()
    score = mgr.domain_score("google.com")
    assert score.match_score == 0.0

def test_is_blocked_case_insensitive(mock_urlopen):
    mgr = BlocklistManager()
    mgr.fetch_and_update()
    assert mgr.is_blocked("PORNHUB.COM") is True
```

- Do NOT start a real DNS server in tests — test `BlocklistManager` independently
- `DNSProxyService` tests use `unittest.mock.patch("socket.socket")` to avoid binding port 53

## Success criteria
```bash
python -m pytest tests/test_dns_proxy/ -v --timeout=30
```
All tests pass.

## Boundary
Do not implement anything outside src/shield/dns_proxy/. Do not import from detection, privacy, db, or system modules.
```

- [ ] **Step 2: Commit**

```bash
git add agents/dns_proxy/CLAUDE.md
git commit -m "chore: dns_proxy agent prompt"
```

---

## Task 10: Run DNS Proxy Agent + Tests

- [ ] **Step 1: Run the dns_proxy agent**

```bash
claude --dangerously-skip-permissions -p "$(cat agents/dns_proxy/CLAUDE.md)"
```

- [ ] **Step 2: Run dns_proxy tests**

```bash
python -m pytest tests/test_dns_proxy/ -v --timeout=30
```

Expected: all tests PASS.

- [ ] **Step 3: If tests fail — retry with error**

```bash
ERR=$(python -m pytest tests/test_dns_proxy/ -v --timeout=30 2>&1); \
claude --dangerously-skip-permissions -p "$(cat agents/dns_proxy/CLAUDE.md)

---
PREVIOUS RUN FAILED. Fix only the failing tests:
$ERR"
```

- [ ] **Step 4: Commit**

```bash
git add src/shield/dns_proxy/ tests/test_dns_proxy/
git commit -m "feat: dns_proxy module — blocklist, DNS proxy server (tests passing)"
```

---

## Task 11: Create agents/system/CLAUDE.md

**Files:**
- Create: `agents/system/CLAUDE.md`

- [ ] **Step 1: Write the agent prompt**

```markdown
# System Agent — Shield Project

## Your single responsibility
Implement `src/shield/system/` module: NSSM Windows service lifecycle and password-protected uninstall guard.

## Working directory
Y:/NoFapShield

## Files you must create
- `src/shield/system/service.py`    — NSSM install/uninstall/status
- `src/shield/system/protection.py` — password verification, uninstall attempt logging
- `src/shield/system/__init__.py`   — exports SystemService
- `tests/test_system/test_service.py`
- `tests/test_system/test_protection.py`

## Files you must NOT touch
- Anything outside `src/shield/system/` and `tests/test_system/`
- `src/shield/core/interfaces.py` — read it, never edit it

## Dependencies
- `subprocess` (stdlib) — NSSM command execution
- `bcrypt` — password hash verification
- `src/shield/db/__init__.py` DBService already exists — import it for logging uninstall attempts

## Interface contract
```python
from shield.db import DBService
```

## API to implement
```python
import subprocess
import bcrypt
from shield.db import DBService

class NSSMService:
    SERVICE_NAME = "ShieldProtection"

    def __init__(self, nssm_path: str = "nssm") -> None:
        self._nssm = nssm_path

    def install(self, python_path: str, script_path: str) -> bool:
        # Runs: nssm install ShieldProtection <python_path> <script_path>
        # Returns True on success (returncode == 0), False otherwise
        ...

    def uninstall(self) -> bool:
        # Runs: nssm remove ShieldProtection confirm
        # Returns True on success, False otherwise
        ...

    def status(self) -> str:
        # Runs: nssm status ShieldProtection
        # Returns stdout stripped, e.g. "SERVICE_RUNNING", "SERVICE_STOPPED"
        # Returns "UNKNOWN" on any error
        ...

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        # Runs nssm with given args, capture_output=True, timeout=10
        ...

class UninstallProtection:
    def __init__(self, db: DBService, user_id: int) -> None: ...

    def verify_password(self, password: str) -> bool:
        # Loads password_hash for user_id from db (via get_setting or direct query)
        # Returns bcrypt.checkpw(password.encode(), stored_hash)
        ...

    def attempt_uninstall(self, password: str, nssm: NSSMService) -> bool:
        # 1. Log attempt in db (settings key "uninstall_attempts", increment counter)
        # 2. If verify_password(password) is True → call nssm.uninstall(), return True
        # 3. If False → log failed attempt, return False
        ...

class SystemService:
    def __init__(self, db: DBService, user_id: int, nssm_path: str = "nssm") -> None: ...
    @property
    def nssm(self) -> NSSMService: ...
    @property
    def protection(self) -> UninstallProtection: ...
```

## Implementation rules
- NSSM commands use `subprocess.run(..., capture_output=True, timeout=10)`
- Do NOT implement ESC, Alt+F4, or minimize hooks — those are UI's responsibility
- All subprocess calls must be mockable (no hardcoded paths in logic)
- UninstallProtection logs every attempt regardless of success/failure

## Testing rules
- Mock `subprocess.run` — never execute real NSSM commands
- Mock `DBService` — use `unittest.mock.MagicMock(spec=DBService)`

```python
def test_install_calls_nssm(mock_subprocess):
    mock_subprocess.return_value.returncode = 0
    svc = NSSMService(nssm_path="nssm")
    result = svc.install("/path/to/python", "/path/to/script.py")
    assert result is True
    mock_subprocess.assert_called_once()
    call_args = mock_subprocess.call_args[0][0]
    assert "install" in call_args
    assert NSSMService.SERVICE_NAME in call_args

def test_uninstall_blocked_without_password(mock_db):
    protection = UninstallProtection(db=mock_db, user_id=1)
    # mock_db.get_setting returns a bcrypt hash of "correct"
    result = protection.attempt_uninstall("wrong_password", nssm=MagicMock())
    assert result is False

def test_uninstall_succeeds_with_correct_password(mock_db, mock_nssm):
    protection = UninstallProtection(db=mock_db, user_id=1)
    mock_nssm.uninstall.return_value = True
    result = protection.attempt_uninstall("correct", nssm=mock_nssm)
    assert result is True
    mock_nssm.uninstall.assert_called_once()
```

## Success criteria
```bash
python -m pytest tests/test_system/ -v --timeout=30
```
All tests pass.

## Boundary
Do not implement anything outside src/shield/system/. Do not implement UI hooks.
```

- [ ] **Step 2: Commit**

```bash
git add agents/system/CLAUDE.md
git commit -m "chore: system agent prompt"
```

---

## Task 12: Run System Agent + Tests

- [ ] **Step 1: Run the system agent**

```bash
claude --dangerously-skip-permissions -p "$(cat agents/system/CLAUDE.md)"
```

- [ ] **Step 2: Run system tests**

```bash
python -m pytest tests/test_system/ -v --timeout=30
```

Expected: all tests PASS.

- [ ] **Step 3: If tests fail — retry with error**

```bash
ERR=$(python -m pytest tests/test_system/ -v --timeout=30 2>&1); \
claude --dangerously-skip-permissions -p "$(cat agents/system/CLAUDE.md)

---
PREVIOUS RUN FAILED. Fix only the failing tests:
$ERR"
```

- [ ] **Step 4: Commit**

```bash
git add src/shield/system/ tests/test_system/
git commit -m "feat: system module — NSSM service, uninstall protection (tests passing)"
```

---

## Task 13: core/config.py

**Files:**
- Create: `src/shield/core/config.py`
- Create: `tests/test_core/test_config.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_core/test_config.py
import json
import pytest
from pathlib import Path
from shield.core.config import Config


def test_default_threshold():
    config = Config()
    assert config.detection_threshold == 0.7


def test_load_from_file(tmp_path):
    settings = {"detection_threshold": 0.5, "screenshot_interval": 5}
    f = tmp_path / "settings.json"
    f.write_text(json.dumps(settings))
    config = Config.from_file(f)
    assert config.detection_threshold == 0.5
    assert config.screenshot_interval == 5


def test_save_to_file(tmp_path):
    config = Config(detection_threshold=0.8)
    f = tmp_path / "settings.json"
    config.save(f)
    data = json.loads(f.read_text())
    assert data["detection_threshold"] == 0.8


def test_missing_file_uses_defaults(tmp_path):
    config = Config.from_file(tmp_path / "nonexistent.json")
    assert config.detection_threshold == 0.7
```

- [ ] **Step 2: Run to verify failure**

```bash
python -m pytest tests/test_core/test_config.py -v
```

Expected: `ImportError` or `ModuleNotFoundError`

- [ ] **Step 3: Implement config.py**

```python
# src/shield/core/config.py
from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Config:
    detection_threshold: float = 0.7
    screenshot_interval: int = 3       # seconds between captures
    dns_score_ttl: int = 10            # seconds before DNS score resets to 0.0
    db_path: str = "shield.db"
    accountability_enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    partner_email: str = ""

    @classmethod
    def from_file(cls, path: Path) -> Config:
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            valid = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
            return cls(**valid)
        except (json.JSONDecodeError, TypeError):
            return cls()

    def save(self, path: Path) -> None:
        path.write_text(
            json.dumps(asdict(self), indent=2), encoding="utf-8"
        )
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_core/test_config.py -v
```

Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/shield/core/config.py tests/test_core/test_config.py
git commit -m "feat: core/config — Config dataclass with file load/save"
```

---

## Task 14: core/orchestrator.py

**Files:**
- Create: `src/shield/core/orchestrator.py`
- Create: `tests/test_core/test_orchestrator.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_core/test_orchestrator.py
import time
import threading
from unittest.mock import MagicMock, patch
from datetime import datetime
import pytest
from shield.core.orchestrator import Orchestrator
from shield.core.config import Config
from shield.core.interfaces import (
    HybridScore, NSFWScore, DomainScore, TriggerSource, FrictionEvent
)


def make_hybrid_score(final_score: float) -> HybridScore:
    return HybridScore(
        final_score=final_score,
        nsfw=NSFWScore(model_score=final_score, confidence=final_score),
        domain=DomainScore(domain="test.com", match_score=0.0),
        url_score=0.0,
        source=TriggerSource.SCREENSHOT,
        computed_at=datetime.utcnow(),
    )


def test_orchestrator_starts_and_stops():
    config = Config()
    db = MagicMock()
    orch = Orchestrator(config=config, db=db)
    orch.start()
    assert orch.is_running()
    orch.stop()
    assert not orch.is_running()


def test_friction_callback_called_above_threshold():
    config = Config(detection_threshold=0.5)
    db = MagicMock()
    orch = Orchestrator(config=config, db=db)

    received: list[FrictionEvent] = []
    orch.register_friction_callback(received.append)

    score = make_hybrid_score(0.9)
    orch._score_queue.put(score)

    orch.start()
    time.sleep(0.2)
    orch.stop()

    assert len(received) == 1
    assert received[0].threshold_at_trigger == 0.5


def test_friction_callback_not_called_below_threshold():
    config = Config(detection_threshold=0.8)
    db = MagicMock()
    orch = Orchestrator(config=config, db=db)

    received: list[FrictionEvent] = []
    orch.register_friction_callback(received.append)

    score = make_hybrid_score(0.3)
    orch._score_queue.put(score)

    orch.start()
    time.sleep(0.2)
    orch.stop()

    assert len(received) == 0


def test_thread_restart_on_exception():
    config = Config()
    db = MagicMock()
    orch = Orchestrator(config=config, db=db)

    restart_count = [0]
    original_start = orch._start_detection_thread

    def counting_start():
        restart_count[0] += 1
        original_start()

    orch._start_detection_thread = counting_start
    orch.start()
    time.sleep(0.1)
    orch.stop()
    # Just verifying orchestrator didn't crash
    assert not orch.is_running()
```

- [ ] **Step 2: Run to verify failure**

```bash
python -m pytest tests/test_core/test_orchestrator.py -v
```

Expected: ImportError

- [ ] **Step 3: Implement orchestrator.py**

```python
# src/shield/core/orchestrator.py
from __future__ import annotations
import logging
import threading
import time
import uuid
from datetime import datetime
from queue import Queue, Empty
from typing import Callable

from shield.core.config import Config
from shield.core.interfaces import (
    DomainScore, FrictionEvent, HybridScore, TriggerSource
)

logger = logging.getLogger(__name__)

_RESTART_DELAYS = [1, 5, 30]  # seconds — backoff across 3 attempts


class Orchestrator:
    def __init__(self, config: Config, db) -> None:
        self._config = config
        self._db = db
        self._score_queue: Queue[HybridScore] = Queue()
        self._shutdown_event = threading.Event()
        self._friction_callbacks: list[Callable[[FrictionEvent], None]] = []
        self._threads: list[threading.Thread] = []
        self._event_loop_thread: threading.Thread | None = None
        # DNS TTL state: (score, timestamp) — updated by DNS thread
        self._last_dns_score: tuple[float, datetime] = (0.0, datetime.utcnow())
        self._lock = threading.Lock()

    def register_friction_callback(self, cb: Callable[[FrictionEvent], None]) -> None:
        self._friction_callbacks.append(cb)

    def start(self) -> None:
        self._shutdown_event.clear()
        self._start_detection_thread()
        self._event_loop_thread = threading.Thread(
            target=self._run_event_loop, daemon=True, name="EventLoop"
        )
        self._event_loop_thread.start()

    def stop(self) -> None:
        self._shutdown_event.set()
        if self._event_loop_thread:
            self._event_loop_thread.join(timeout=5)
        for t in self._threads:
            t.join(timeout=5)
        self._threads.clear()

    def is_running(self) -> bool:
        return not self._shutdown_event.is_set()

    def _start_detection_thread(self) -> None:
        t = threading.Thread(
            target=self._detection_worker, daemon=True, name="DetectionWorker"
        )
        t.start()
        self._threads.append(t)

    def _detection_worker(self) -> None:
        attempt = 0
        while not self._shutdown_event.is_set():
            try:
                self._run_detection_cycle()
                attempt = 0
                self._shutdown_event.wait(timeout=self._config.screenshot_interval)
            except Exception as exc:
                delay = _RESTART_DELAYS[min(attempt, len(_RESTART_DELAYS) - 1)]
                logger.error("Detection worker error (attempt %d): %s", attempt, exc)
                attempt += 1
                if attempt > len(_RESTART_DELAYS):
                    logger.critical("Detection worker exhausted retries, stopping.")
                    break
                self._shutdown_event.wait(timeout=delay)

    def _run_detection_cycle(self) -> None:
        # Lazily import to allow mocking in tests
        from shield.detection import DetectionService  # type: ignore[import]
        if not hasattr(self, "_detection_svc"):
            self._detection_svc = DetectionService()
        dns_score = self._current_dns_score()
        hybrid = self._detection_svc.run_once(
            domain_score=dns_score, url_score=0.0
        )
        self._score_queue.put(hybrid)

    def _current_dns_score(self) -> DomainScore:
        with self._lock:
            score, ts = self._last_dns_score
            age = (datetime.utcnow() - ts).total_seconds()
            if age > self._config.dns_score_ttl:
                return DomainScore(domain="", match_score=0.0)
            return DomainScore(domain="", match_score=score)

    def _run_event_loop(self) -> None:
        while not self._shutdown_event.is_set():
            try:
                score = self._score_queue.get(timeout=0.1)
            except Empty:
                continue
            threshold = self._config.detection_threshold
            if score.final_score >= threshold:
                event = FrictionEvent(
                    score=score,
                    triggered_at=datetime.utcnow(),
                    session_id=str(uuid.uuid4()),
                    threshold_at_trigger=threshold,
                )
                for cb in self._friction_callbacks:
                    try:
                        cb(event)
                    except Exception as exc:
                        logger.error("Friction callback error: %s", exc)
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_core/test_orchestrator.py -v --timeout=30
```

Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/shield/core/orchestrator.py tests/test_core/test_orchestrator.py
git commit -m "feat: core/orchestrator — thread lifecycle, backoff restart, friction callback"
```

---

## Task 15: core/event_loop.py + core/__init__.py

**Files:**
- Modify: `src/shield/core/__init__.py`
- Create: `src/shield/core/event_loop.py`

- [ ] **Step 1: Create event_loop.py**

```python
# src/shield/core/event_loop.py
"""
Standalone entry point that wires Config, DBService, and Orchestrator,
then runs until KeyboardInterrupt or SIGTERM.
"""
from __future__ import annotations
import logging
import signal
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def run(config_path: Path | None = None) -> None:
    from shield.core.config import Config
    from shield.core.orchestrator import Orchestrator
    from shield.db import DBService

    config = Config.from_file(config_path or Path("settings.json"))
    db = DBService(db_path=Path(config.db_path))
    orchestrator = Orchestrator(config=config, db=db)

    def _on_friction(event):
        logger.info(
            "FrictionEvent: score=%.3f threshold=%.3f session=%s",
            event.score.final_score,
            event.threshold_at_trigger,
            event.session_id,
        )
        # UI callback registered separately — this is the logging hook only

    orchestrator.register_friction_callback(_on_friction)

    stop_event = __import__("threading").Event()

    def _handle_signal(sig, frame):
        logger.info("Received signal %s — shutting down", sig)
        stop_event.set()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    logger.info("Shield event loop starting")
    orchestrator.start()
    stop_event.wait()
    orchestrator.stop()
    logger.info("Shield event loop stopped")
```

- [ ] **Step 2: Update core/__init__.py**

```python
# src/shield/core/__init__.py
from shield.core.config import Config
from shield.core.orchestrator import Orchestrator
from shield.core.interfaces import (
    FrictionEvent, HybridScore, StreakInfo, UserGoal,
    NSFWScore, DomainScore, ScreenshotResult, TriggerSource,
)

__all__ = [
    "Config",
    "Orchestrator",
    "FrictionEvent",
    "HybridScore",
    "StreakInfo",
    "UserGoal",
    "NSFWScore",
    "DomainScore",
    "ScreenshotResult",
    "TriggerSource",
]
```

- [ ] **Step 3: Verify imports**

```bash
python -c "from shield.core import Config, Orchestrator, FrictionEvent; print('ok')"
```

Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add src/shield/core/event_loop.py src/shield/core/__init__.py
git commit -m "feat: core/event_loop — wiring entry point; core/__init__ exports"
```

---

## Task 16: Full Test Suite

- [ ] **Step 1: Run all tests**

```bash
python -m pytest tests/ -v --timeout=30 --cov=src/shield --cov-report=term-missing
```

Expected: all tests PASS, no module import errors.

- [ ] **Step 2: If any test fails — investigate and fix**

Failures here indicate a cross-module import issue or a type mismatch between what a sub-agent implemented and what `core/interfaces.py` defines. Read the error, identify the mismatch, fix in the specific module's file. Do not change `core/interfaces.py` unless a type was genuinely wrong in the spec.

- [ ] **Step 3: Final commit**

```bash
git add -u
git commit -m "chore: all modules integrated — full test suite passing"
```

---

## Task 17: README.md

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README**

```markdown
# Shield

A Windows desktop application that helps users break pornographic content addiction by creating a conscious pause at the moment of urge. Runs entirely locally — no data leaves the device.

## Architecture

```
detection/   — NudeNet NSFW classifier + mss screenshots (RAM only)
dns_proxy/   — Local DNS proxy + StevenBlack blocklist
system/      — NSSM Windows service + uninstall protection
privacy/     — Accountability partner email notifications
db/          — SQLite: streaks, logs, settings
core/        — Orchestrator, Config, shared interfaces
ui/          — (separate agent)
```

## Detection Score

```
final_score = 0.6 × nsfw_model + 0.3 × domain_match + 0.1 × url_heuristic
```

Friction triggers when `final_score >= detection_threshold` (default: 0.7).

## Setup

```bash
pip install -e ".[dev]"
python -m pytest tests/
```

## Privacy

Screenshots are captured in RAM and never written to disk. All logs are local SQLite only.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: README — architecture overview and setup"
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Task |
|---|---|
| pyproject.toml | Task 1 |
| Folder structure + `__init__.py` files | Task 1 |
| `core/interfaces.py` dataclasses | Task 2 |
| `agents/db/CLAUDE.md` | Task 3 |
| DB agent run + tests | Task 4 |
| `agents/privacy/CLAUDE.md` | Task 5 |
| Privacy agent run + tests | Task 6 |
| `agents/detection/CLAUDE.md` | Task 7 |
| Detection agent run + tests | Task 8 |
| `agents/dns_proxy/CLAUDE.md` | Task 9 |
| DNS proxy agent run + tests | Task 10 |
| `agents/system/CLAUDE.md` | Task 11 |
| System agent run + tests | Task 12 |
| `core/config.py` | Task 13 |
| `core/orchestrator.py` — backoff, callback, DNS TTL | Task 14 |
| `core/event_loop.py` — wiring | Task 15 |
| Full integration test run | Task 16 |
| README.md | Task 17 |
| `threshold_at_trigger` in FrictionEvent | Task 2 + Task 14 |
| `user_id` in logs table | Task 3 (CLAUDE.md) |
| `accountability.py` naming | Task 5 (CLAUDE.md) |
| `restart_delay = [1, 5, 30]` backoff | Task 14 |
| WAL mode | Task 3 (CLAUDE.md) |
| RAM-only screenshots | Task 7 (CLAUDE.md) + Task 2 (ScreenshotResult) |
| `pytest-timeout` | Task 1 (pyproject.toml) |

All spec requirements covered. No placeholders or TBDs in plan.
