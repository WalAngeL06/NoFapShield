# Architecture

Current branch: `rebuild/v0-clean`

Shield v0.1 is a clean, local-first Python scaffold. The current implementation
keeps product code inside the `src/shield/` package and intentionally avoids the
old root-level architecture.

## Package Layout

- `src/shield/app.py`
  - CLI entrypoint.
  - Dispatches supported demo and UI commands.
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

## Supported Commands

```bash
python -m shield.app --demo-trigger
python -m shield.app --screen overlay
python -m shield.app --screen checkin
python -m shield.app --screen dashboard
python -m shield.app --screen settings
```

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
- SMTP or accountability email
- NSSM or service installation
- uninstall protection

## Memory Maintenance

This architecture document is durable project memory.

If an AI assistant changes code, architecture, scope, commands, constraints, or
project direction, it must update this file or another relevant memory doc in
the same task before reporting completion.

