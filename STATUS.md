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
- durable AI project memory docs for handoff and process continuity

## Explicitly Out Of Scope

- content classification
- DNS interception
- screenshot capture
- Windows service installation
- uninstall protection
- email notifications
- full desktop UI

## Project Memory Workflow

Project memory docs are now part of the workflow. AI agents must read them
before making changes and update the relevant docs after changing code,
architecture, scope, commands, constraints, or project direction.

## Verification

Run:

```bash
python -m pytest
python -m shield.app --demo-trigger
python -m shield.app --screen overlay
python -m shield.app --screen checkin
```
