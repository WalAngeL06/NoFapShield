# Architecture

Current branch: `rebuild/v0-clean`

Shield v0.1 is a clean, local-first Python scaffold. The current implementation
keeps product code inside the `src/shield/` package and intentionally avoids the
old root-level architecture.

## Package Layout

- `src/shield/app.py`
  - CLI entrypoint.
  - Dispatches default startup, supported demo commands, and UI commands.
- `src/shield/trigger.py`
  - Pure local URL/domain trigger helpers.
  - Contains placeholder prototype risk domains, editable risk-list and
    allowlist parsing, settings loading helpers, and matcher functions for the
    manual `--trigger-url` flow.
- `src/shield/core/`
  - Lightweight dataclasses, config, and orchestration helpers.
  - Contains `Config`, `FrictionEvent`, trigger source types, and
    `Orchestrator`.
- `src/shield/db/`
  - Local SQLite event store.
  - Stores demo friction events, morning check-in text, and key/value
    settings locally.
- `src/shield/ui/`
  - PyQt6 UI screens.
  - `src/shield/ui/blur_overlay.py` is the PyQt6 pause overlay.
  - `src/shield/ui/morning_checkin.py` is the PyQt6 morning check-in screen.
  - `src/shield/ui/dashboard.py` is the PyQt6 read-only dashboard.
  - `src/shield/ui/settings.py` is the PyQt6 local-only settings screen.
  - `src/shield/ui/onboarding.py` is the PyQt6 local-only onboarding screen.

## Supported Commands

```bash
python -m shield.app
python -m shield.app --demo-trigger
python -m shield.app --demo-trigger --show-overlay
python -m shield.app --trigger-url "risk.example"
python -m shield.app --trigger-url "risk.example" --show-overlay
python -m shield.app --list-risk-domains
python -m shield.app --set-risk-domains "risk.example,focus.example"
python -m shield.app --list-allow-domains
python -m shield.app --set-allow-domains "safe.example.com"
python -m shield.app --screen overlay
python -m shield.app --screen checkin
python -m shield.app --screen dashboard
python -m shield.app --screen settings
python -m shield.app --screen onboarding
```

With no explicit command, `python -m shield.app` reads the local
`onboarding_completed` setting from the SQLite settings store. Completed values
route to the dashboard; missing, false, malformed, or unreadable values route to
onboarding.

At the app entrypoint, `--db-path` explicitly controls the SQLite database path.
When `--db-path` is omitted and the default `Config().db_path` is `:memory:`,
Shield resolves a durable user-local app data database instead:
`LOCALAPPDATA\NoFapShield\shield.db` on Windows or
`~/.local/share/nofapshield/shield.db` on other platforms. This keeps documented
trigger settings commands durable across separate CLI invocations while letting
tests and development runs use an isolated `--db-path`.

`--demo-trigger` records and prints a synthetic friction event without opening
UI by default. `--demo-trigger --show-overlay` records and prints the same event,
then delegates to the existing PyQt6 overlay runner. Overlay launch paths read
local `alternative_actions` settings and pass them to the overlay when present;
the overlay falls back to default action cards otherwise.

`--trigger-url` is a manual local v0.2 prototype. It classifies a supplied
URL/domain/string against the active local risk list, records a local
`manual_url_trigger` friction event on match, and can delegate to the existing
overlay path with `--show-overlay`. The active risk list is read from the local
SQLite setting `trigger_risk_domains`; invalid, empty, missing, or malformed
settings fall back to the safe placeholder defaults. `--list-risk-domains`
prints the active list, and `--set-risk-domains` stores a normalized custom
local list in the resolved local SQLite database. The local allowlist is read
from `trigger_allow_domains`; it has no placeholder defaults and overrides risk
matches for local false-positive handling. `--list-allow-domains` prints the
allowlist, and `--set-allow-domains` stores a normalized custom allowlist in the
same resolved local SQLite database. No real adult domains are shipped. It does
not monitor browsers, inspect browser history, intercept DNS, capture
screenshots, call the network, or claim complete blocking or porn detection.

`--screen onboarding` saves goal text, alternative actions, optional local email
placeholder, and an onboarding completion flag through the local settings store.
It does not send email.

## Explicitly Forbidden Current Architecture

The current architecture must not reintroduce:

- root-level `core.py`
- root-level `main.py`
- root-level `ui/`
- old heavy backend modules

## Intentionally Out Of Scope For v0.1

The current v0.1 architecture intentionally does not include:

- NSFW model detection
- DNS proxy
- screenshot capture
- SMTP
- email sending
- accountability delivery
- local `accountability_email` placeholder storage exists in settings/onboarding
- NSSM or service installation
- uninstall protection

## Memory Maintenance

This architecture document is durable project memory.

If an AI assistant changes code, architecture, scope, commands, constraints, or
project direction, it must update this file or another relevant memory doc in
the same task before reporting completion.

