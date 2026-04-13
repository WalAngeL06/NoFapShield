# Shield

A Windows desktop application that helps users break pornographic content addiction by creating a conscious pause at the moment of urge. Runs entirely locally — no data leaves the device.

## Architecture

```
detection/   — NudeNet NSFW classifier + mss screenshots (RAM only)
dns_proxy/   — Local DNS proxy (127.0.0.1:53) + StevenBlack blocklist
system/      — NSSM Windows service + password-protected uninstall guard
privacy/     — Accountability partner email notifications (optional)
db/          — SQLite: streaks, logs, settings (WAL mode, thread-safe)
core/        — Orchestrator, Config, shared dataclass interfaces
ui/          — (separate agent)
```

## Detection Score

```
final_score = 0.6 × nsfw_model + 0.3 × domain_match + 0.1 × url_heuristic
```

Friction triggers when `final_score >= detection_threshold` (default: 0.7).

## Module Interfaces

All cross-module data types live in `src/shield/core/interfaces.py`. No module imports another module — all communication goes through typed dataclasses.

Key types: `HybridScore`, `FrictionEvent`, `StreakInfo`, `DomainScore`, `NSFWScore`

## Setup

```bash
pip install -e ".[dev]"
python -m pytest tests/
```

## Privacy

- Screenshots captured in RAM via `mss` — never written to disk permanently
- All logs stored in local SQLite only
- No telemetry, no external API calls
- Accountability email is opt-in and SMTP credentials stay local

## Running

```python
from shield.core import Config, Orchestrator
from shield.db import DBService
from pathlib import Path

config = Config.from_file(Path("settings.json"))
db = DBService(db_path=Path(config.db_path))
orchestrator = Orchestrator(config=config, db=db)
orchestrator.register_friction_callback(your_ui_callback)
orchestrator.start()
```
