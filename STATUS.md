# Project Status - Shield v0.1

_Last updated: 2026-04-28_

## Current Scope

The repository is a clean v0.1 scaffold. It includes:

- `shield.core.Config`
- `shield.core.FrictionEvent`
- `shield.core.Orchestrator`
- `shield.db.EventStore`
- `python -m shield.app`
- `python -m shield.app --demo-trigger`
- `python -m shield.app --demo-trigger --show-overlay`
- `python -m shield.app --screen overlay`
- `python -m shield.app --screen checkin`
- `python -m shield.app --screen dashboard`
- `python -m shield.app --screen settings`
- `python -m shield.app --screen onboarding`
- durable AI project memory docs for handoff and process continuity

Current tests: `91 passed`.

Completed product checkpoints include the committed read-only dashboard
(`6f50b55`), local settings screen (`78526cd`), demo-overlay flow
(`19ec0c8`), onboarding (`caa9356`), default startup flow (`d9ce5d4`), and
saved overlay actions (`223105a`).
The latest known fix is `9753375 fix: recognize today's dashboard checkin`.

`--demo-trigger --show-overlay` is current committed functionality. It records
the demo event, prints the stable demo output plus `overlay=launched`, and
delegates to the existing pause overlay runner. Default `--demo-trigger` still
does not open the overlay.

`--screen onboarding` is current committed functionality. It provides a
local-only PyQt6 setup flow for a personal goal, alternative actions, optional
local email placeholder, and `onboarding_completed=true`. No email is sent in
v0.1. Saved alternative actions are used by the pause overlay when available.

Bare `python -m shield.app` is current committed functionality. It reads local
`onboarding_completed` state and routes to dashboard when complete or onboarding
when missing, false, malformed, or unreadable.

Saved alternative actions in overlay are current committed functionality.
Overlay launch paths read local
`alternative_actions` from settings/onboarding and pass them into the pause
overlay. Missing, empty, malformed, or unreadable actions fall back to default
action cards.

Next recommended product task: manual UI smoke test.

## Explicitly Out Of Scope

- content classification
- DNS interception
- screenshot capture
- Windows service installation
- uninstall protection
- email sending or accountability delivery
- full desktop UI

## Project Memory Workflow

Project memory docs are now part of the workflow. AI agents must read them
before making changes and update the relevant docs after changing code,
architecture, scope, commands, constraints, or project direction.

Git write operations are user-controlled by default. AI agents should edit,
test, and report unless the user explicitly authorizes Git writes in the same
message.

## Automated Verification

Run:

```bash
python -m pytest
python -m shield.app --demo-trigger
```

## Manual UI Checks

These commands open PyQt6 windows or fullscreen UI. They are manual checks, not
automated test commands.

```bash
python -m shield.app
python -m shield.app --demo-trigger --show-overlay
python -m shield.app --screen overlay
python -m shield.app --screen checkin
python -m shield.app --screen dashboard
python -m shield.app --screen settings
python -m shield.app --screen onboarding
```
