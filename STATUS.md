# Project Status - Shield v0.1

_Last updated: 2026-04-29_

## Current Scope

The repository is a clean v0.1 scaffold. It includes:

- `shield.core.Config`
- `shield.core.FrictionEvent`
- `shield.core.Orchestrator`
- `shield.db.EventStore`
- `python -m shield.app`
- `python -m shield.app --demo-trigger`
- `python -m shield.app --demo-trigger --show-overlay`
- `python -m shield.app --trigger-url`
- `python -m shield.app --trigger-url --show-overlay`
- `python -m shield.app --screen overlay`
- `python -m shield.app --screen checkin`
- `python -m shield.app --screen dashboard`
- `python -m shield.app --screen settings`
- `python -m shield.app --screen onboarding`
- durable AI project memory docs for handoff and process continuity

Current tests: `113 passed`.

Published release: `v0.1.0-alpha`.

- GitHub Release title:
  `Shield v0.1.0-alpha — Local-only pause layer MVP`
- Release type: pre-release / alpha / developer preview
- Target commit:
  `3aa3980 chore: refresh memory docs after release checklist commit`
- Tests before tag: `91 passed`
- Manual UI smoke: `PASS`
- Working tree was clean before tag
- No packaged installer yet

Current task: No active task.

Latest known product checkpoint:
`c8e8c4a feat: add local URL/domain trigger prototype`.

Latest known test/config checkpoint:
`b76abd2 test: use ignored pytest basetemp`.

The v0.2 manual local URL/domain trigger prototype is committed functionality.
It is local-only, uses a small placeholder risk list, records matching events
through `EventStore`, and can delegate to the existing pause overlay when
`--show-overlay` is passed. It does not add automatic browser monitoring,
DNS/proxy behavior, screenshot capture, network calls, cloud sync, telemetry,
SMTP/email sending, services, NSSM, uninstall protection, hard process
protection, password/login, packaging implementation, or complete
blocking/porn detection claims.

Completed product checkpoints include the committed read-only dashboard
(`6f50b55`), local settings screen (`78526cd`), demo-overlay flow
(`19ec0c8`), onboarding (`caa9356`), default startup flow (`d9ce5d4`), and
saved overlay actions (`223105a`), and manual local URL/domain trigger
prototype (`c8e8c4a`).
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

`--trigger-url` is current committed v0.2 prototype functionality. It
classifies a user-supplied URL/domain/string against the local placeholder risk
list (`risk.example`, `blocked.example`, `relapse.example`). Matching inputs
record a local `manual_url_trigger` friction event. Non-matches and malformed
inputs do not record events or open the overlay. `--trigger-url --show-overlay`
delegates to the existing overlay launch path and uses saved alternative
actions when available.

Manual UI smoke test: `PASS` with non-blocking polish notes.

Checked:

- `python -m shield.app`
- `python -m shield.app --screen onboarding`
- `python -m shield.app --screen dashboard`
- `python -m shield.app --screen settings`
- `python -m shield.app --screen checkin`
- `python -m shield.app --demo-trigger --show-overlay`

Observed:

- onboarding opens, transitions between steps, and closes after save
- default startup routes to dashboard after onboarding completion
- dashboard, settings, check-in, and overlay open
- saved alternative actions are wired into overlay launch paths
- no P0 blocker found

Known non-blocking polish notes:

- onboarding step 3 spacing feels too spread out
- settings is functional but visually dense/amateur
- dashboard is functional but could be more polished
- overall UI needs visual polish later, but this does not block v0.1 alpha

Latest committed docs checkpoint:
`1717458 docs: plan local trigger MVP for v0.2`.

README/release polish for v0.1 alpha was committed in
`c812f41 docs: polish README for v0.1 alpha`.

The v0.1 alpha release checklist is committed current documentation at
`docs/release-checklist-v0.1.md` and defines the release target, verification
snapshot, explicit exclusions, pre-tag checklist, draft release notes, and
manual tag commands.

Next recommended task: Expand local trigger configuration / editable local risk
list.

## Explicitly Out Of Scope

- content detection or content classification
- automatic content blocking
- DNS interception
- screenshot capture
- browser monitoring or browser history scraping
- cloud sync
- telemetry
- network calls
- SMTP
- Windows service installation
- NSSM integration
- uninstall protection
- hard process protection
- email sending or accountability delivery
- password or login flow
- packaged installer
- packaging implementation
- complete blocking or porn detection claims
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
