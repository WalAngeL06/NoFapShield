# Shield

Shield v0.1 is a clean local-first scaffold for a future desktop friction app.
This version intentionally contains only the project spine:

- config loading and saving
- typed friction events
- an in-process orchestrator
- a small SQLite event store
- a CLI demo trigger
- a fullscreen friction overlay screen
- a local-only morning check-in screen
- a read-only local dashboard screen
- a local-only settings screen
- a local-only onboarding screen
- a local default startup flow

The v0.1 scaffold does not include content classification, network interception,
screenshot capture, Windows service management, uninstall protection, email
sending, SMTP/accountability delivery, or a full desktop UI. The optional
`accountability_email` value is stored locally only as a placeholder.

## Setup

```bash
pip install -e ".[dev]"
python -m pytest
```

## Default Startup

```bash
python -m shield.app
```

With no explicit command, Shield reads the local `onboarding_completed` setting.
If onboarding is complete, it opens the dashboard. Otherwise, it opens
onboarding. This routing is local-only.

## Demo Trigger

```bash
python -m shield.app --demo-trigger
python -m shield.app --demo-trigger --show-overlay
```

The demo trigger emits a synthetic friction event, records it through the local
event store, and prints the event summary. By default the demo uses an in-memory
database; pass `--db-path path/to/shield.db` to persist events. The default
demo trigger does not open the overlay. Add `--show-overlay` to record and print
the same event summary, print `overlay=launched`, and then launch the pause
overlay.

## Overlay

```bash
python -m shield.app --screen overlay
```

The overlay is a local fullscreen friction screen with a 15-second countdown
before action choices are shown.

## Morning Check-in

```bash
python -m shield.app --screen checkin
```

The morning check-in stores the user's note in the configured local SQLite
database only.

## Dashboard

```bash
python -m shield.app --screen dashboard
```

The dashboard is a read-only view of recent check-ins and trigger events stored
in the local SQLite database. No data leaves the device.

## Settings

```bash
python -m shield.app --screen settings
```

The settings screen edits a personal goal, locally saved alternative actions, an
optional accountability email, and a detection-sensitivity preference. All
values are stored locally in SQLite. Saved alternative actions are not wired
into the pause overlay yet; that is planned future work. The email field is a
local placeholder and is not sent anywhere in v0.1. The detection-sensitivity
slider is also a placeholder; v0.1 has no detection.

## Onboarding

```bash
python -m shield.app --screen onboarding
```

The onboarding screen is a local-only setup flow for a personal goal,
alternative actions, and an optional accountability email placeholder. It saves
values to local SQLite settings, including `onboarding_completed=true`. No email
is sent in v0.1, and saved alternative actions are not wired into the pause
overlay yet.

## AI Workflow

AI contributors must read `AGENTS.md` and `AI_HANDOFF.md` before changing the
project. If an AI changes code, architecture, scope, commands, constraints, or
project direction, it must update the relevant memory docs before reporting
completion.
