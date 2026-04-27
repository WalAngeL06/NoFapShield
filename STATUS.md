# Project Status - Shield v0.1

_Last updated: 2026-04-27_

## Current Scope

The repository is a clean v0.1 scaffold. It includes:

- `shield.core.Config`
- `shield.core.FrictionEvent`
- `shield.core.Orchestrator`
- `shield.db.EventStore`
- `python -m shield.app --demo-trigger`
- `python -m shield.app --screen overlay`
- `python -m shield.app --screen checkin`

## Explicitly Out Of Scope

- content classification
- DNS interception
- screenshot capture
- Windows service installation
- uninstall protection
- email notifications
- full desktop UI

## Verification

Run:

```bash
python -m pytest
python -m shield.app --demo-trigger
python -m shield.app --screen overlay
python -m shield.app --screen checkin
```
