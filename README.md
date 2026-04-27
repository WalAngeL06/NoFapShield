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

The v0.1 scaffold does not include content classification, network interception,
screenshot capture, Windows service management, uninstall protection, email, or
a full desktop UI.

## Setup

```bash
pip install -e ".[dev]"
python -m pytest
```

## Demo Trigger

```bash
python -m shield.app --demo-trigger
```

The demo trigger emits a synthetic friction event, records it through the local
event store, and prints the event summary. By default the demo uses an in-memory
database; pass `--db-path path/to/shield.db` to persist events.

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
