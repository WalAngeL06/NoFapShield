# Shield v0.1 alpha

Shield v0.1 alpha is a local-only, privacy-first pause layer for Windows
desktop self-control.

## What Shield Is

Shield is a local-first desktop friction app. The v0.1 alpha focuses on a calm
pause layer that helps create a deliberate pause during an urge, without
shaming language or cloud services.

This release is intentionally small. It is not a medical tool, does not claim
to treat addiction, and does not claim to fully block or detect pornography.

## What v0.1 Alpha Includes

- Local onboarding for a personal goal, alternative actions, and an optional
  local email placeholder.
- Default startup flow with `python -m shield.app`, routing to onboarding or
  dashboard based on the local `onboarding_completed` setting.
- Fullscreen pause overlay.
- Saved alternative actions in the overlay, with fallback default cards when
  saved actions are missing or malformed.
- Local morning check-in.
- Read-only local dashboard for recent check-ins and trigger events.
- Local settings for goal text, alternative actions, email placeholder, and a
  detection-sensitivity placeholder.
- Demo trigger for recording a synthetic local friction event.
- SQLite local storage for events, check-ins, and settings.
- Current automated verification snapshot: `91 passed`.
- Manual UI smoke test: `PASS` with non-blocking polish notes.

## Current v0.2 Development Snapshot

The current development branch adds a manual local URL/domain trigger prototype
with a user-owned editable local risk list. This is not automatic browser
monitoring, full blocking, or porn detection.

The prototype:

- Classifies a user-supplied URL/domain/string against the active local risk
  list.
- Stores custom risk domains locally in SQLite settings under
  `trigger_risk_domains`.
- Uses only safe placeholder domains such as `risk.example` as fallback
  defaults.
- Ships no real adult domains.
- Records a local friction event when the supplied candidate matches.
- Can delegate to the existing pause overlay when `--show-overlay` is passed.
- Keeps all data local.

Current automated verification snapshot: `138 passed`.

## What v0.1 Alpha Does Not Include

- No content detection.
- No DNS interception or DNS proxy.
- No screenshot capture.
- No cloud sync.
- No telemetry.
- No network calls.
- No SMTP or email sending.
- No accountability delivery.
- No Windows service or NSSM integration.
- No uninstall protection.
- No hard process protection.
- No packaged installer yet.

## Privacy Model

Shield v0.1 alpha stores data in local SQLite only. No data leaves the device in
this release.

The optional `accountability_email` value is a local placeholder only. It is
saved locally so the UI can model the future setting, but v0.1 does not send
email or deliver accountability messages.

The detection-sensitivity setting is also a placeholder. v0.1 has no content
detection, no screen capture, and no monitoring pipeline.

## Setup

From the repository root:

```powershell
pip install -e ".[dev]"
python -m pytest
```

On some Windows machines, the `python` alias points to the Microsoft Store
instead of an installed interpreter. If that happens, use the full path to your
installed Python executable. Example:

```powershell
"C:\Users\YourName\AppData\Local\Programs\Python\Python314\python.exe" -m pytest
```

## Run Commands

Default startup:

```powershell
python -m shield.app
```

Local onboarding:

```powershell
python -m shield.app --screen onboarding
```

Read-only local dashboard:

```powershell
python -m shield.app --screen dashboard
```

Local settings:

```powershell
python -m shield.app --screen settings
```

Local morning check-in:

```powershell
python -m shield.app --screen checkin
```

Fullscreen pause overlay:

```powershell
python -m shield.app --screen overlay
```

Record a synthetic local demo event without opening UI:

```powershell
python -m shield.app --demo-trigger
```

Record a synthetic local demo event and open the overlay:

```powershell
python -m shield.app --demo-trigger --show-overlay
```

Classify a supplied URL/domain/string against the local prototype risk list:

```powershell
python -m shield.app --trigger-url "risk.example"
```

Record a matching local trigger event and open the overlay:

```powershell
python -m shield.app --trigger-url "risk.example" --show-overlay
```

List the active local risk domains:

```powershell
python -m shield.app --list-risk-domains
```

Set a custom local risk list:

```powershell
python -m shield.app --set-risk-domains "risk.example,focus.example"
```

The screen commands open PyQt6 windows, and the overlay command opens fullscreen
UI. Treat them as manual UI checks, not automated test commands.

The `--trigger-url` command is a manual local prototype. The editable risk list
is user-owned and local-only, with placeholder defaults as fallback. It does not
monitor browsers, inspect browser history, intercept DNS, capture screenshots,
call the network, sync to cloud services, send email, add password/login
behavior, install services, harden processes, add packaging, or claim complete
blocking or porn detection.

## Current Known Polish Notes

- Onboarding step 3 spacing needs polish.
- Settings is functional but visually dense.
- Dashboard is functional but can be visually improved.
- These are not v0.1 alpha blockers.

## Development Workflow For AI Agents

AI contributors must read `AGENTS.md` and `AI_HANDOFF.md` before changing the
project.

If an AI changes code, architecture, scope, commands, constraints, or project
direction, it must update the relevant memory docs before reporting completion.

AI agents must not run Git write operations by default. Do not run `git add`,
`git commit`, `git push`, `git rebase`, `git checkout`, `git reset`, or
`git clean` unless the user explicitly asks for that operation in the same
message.
