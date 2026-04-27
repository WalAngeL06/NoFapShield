# AGENTS.md — Shield AI Contributor Rules

This repository is often edited with AI coding agents such as Codex, Claude, Gemini, or ChatGPT. The goal of this file is to make every agent operate from the same project memory instead of relying on chat history.

## Required first step for every AI agent

Before editing files, read these files in order:

1. `AGENTS.md`
2. `STATUS.md`
3. `ARCHITECTURE.md`
4. `DECISIONS.md`
5. `TASKS.md`
6. `AI_HANDOFF.md`
7. `README.md`

Then summarize:

- current branch and milestone
- current architecture
- current task
- files allowed to change
- files or features that are explicitly forbidden
- test command

Do not edit files until the user approves the summarized plan.

## Branch rule

Work on `rebuild/v0-clean` unless the user explicitly says otherwise.

Never modify `main` directly.

## Current project direction

Shield is being rebuilt as a small, privacy-first, local-only Windows desktop app. v0.1 focuses on a calm pause layer and local check-ins, not heavy detection or system protection.

## Forbidden unless explicitly requested

Do not add or reintroduce any of the following without a dedicated approved task:

- root-level `core.py`
- root-level `main.py`
- root-level `ui/`
- NudeNet or other NSFW model integration
- DNS proxy
- screenshot capture
- `mss`, `dxcam`, OpenCV, Pillow, or image-processing dependencies
- SMTP/accountability email
- NSSM/service installation
- uninstall protection
- hard process protection
- network calls
- telemetry
- cloud sync

## UI rules

- UI lives under `src/shield/ui/`.
- The current UI stack is PyQt6.
- Do not launch real fullscreen windows in automated tests.
- UI tests should use offscreen mode, monkeypatching, or smoke tests.
- Tone must be calm, non-shaming, and minimal.

## Data and privacy rules

- v0.1 stores data locally only.
- Do not add network features unless explicitly requested.
- Do not write screenshots or browser history to disk.
- Do not overclaim medical, therapeutic, or addiction-treatment outcomes.

## Testing rules

Before reporting a task as complete, run the test suite with the available Python interpreter.

Preferred command:

```powershell
python -m pytest
```

If `python` is unavailable on Windows, use the known local interpreter, for example:

```powershell
"C:\Users\Serdar Arif\AppData\Local\Programs\Python\Python314\python.exe" -m pytest
```

## Commit rule

Do not commit unless the user explicitly approves.

When approved:

```powershell
git status
git add .
git commit -m "<clear conventional commit message>"
git push origin rebuild/v0-clean
```

## Documentation maintenance rule — mandatory

Project memory must not become stale.

Every AI agent that changes code, architecture, behavior, scope, commands, tests, or project direction must update the relevant memory docs in the same task.

Update these files when applicable:

- `STATUS.md` — when feature status, test count, current milestone, or known gaps change.
- `ARCHITECTURE.md` — when module structure, data flow, CLI commands, or storage boundaries change.
- `DECISIONS.md` — when a design decision is made, reversed, or clarified.
- `TASKS.md` — when current/next tasks change.
- `AI_HANDOFF.md` — after every completed AI task, including what changed, tests run, commit hash if any, and next recommended task.
- `README.md` — when user-facing install/run commands change.

If a change affects these docs and the agent does not update them, the task is incomplete.

## Handoff rule

At the end of each task, report:

- tests run and result
- files changed
- whether docs were updated
- commit hash if committed
- what should be done next

The next AI agent must be able to continue without relying on the previous chat transcript.
