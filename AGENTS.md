# AGENTS.md - Shield AI Contributor Rules

This repository is often edited with AI coding agents such as Codex, Claude,
Gemini, ChatGPT, Copilot, and other tools. The goal of this file is to make
every agent operate from the same project memory instead of relying on chat
history.

## Required Reading Before Changes

Before making changes, read these files in order:

1. `AGENTS.md`
2. `STATUS.md`
3. `ARCHITECTURE.md`
4. `DECISIONS.md`
5. `TASKS.md`
6. `AI_HANDOFF.md`
7. `README.md`

If any file is missing, note that as a project health issue and recreate or
repair it as part of the current task when appropriate.

## First Response From A New AI

The first response from a new AI assistant should summarize:

1. current architecture
2. current milestone
3. forbidden changes
4. current task
5. test command

Do not edit files before confirming understanding unless the user explicitly
tells you to proceed.

## Branch And Commit Rules

- Work only on the branch requested by the user.
- Current active branch for v0.1 work: `rebuild/v0-clean`.
- Do not modify `main`.
- Do not commit unless the user explicitly approves.
- Tests must pass before proposing or making a commit.

### Git Operation Rules

- AI agents must not run Git write operations unless the user explicitly asks in
  the same message.
- Default rule: no `git add`, `git commit`, `git push`, `git rebase`,
  `git checkout`, `git reset`, or `git clean`.
- AI agents may run read-only Git commands:
  - `git status`
  - `git diff`
  - `git log`
  - `git branch --show-current`
- The preferred workflow is:
  1. AI edits files.
  2. AI runs tests.
  3. AI reports diff summary.
  4. User reviews.
  5. User performs `git add`, `git commit`, and `git push` manually.
- If an AI accidentally enters a rebase/conflict state, it must stop and ask the
  user instead of trying to fix Git history automatically.

## Current Project Direction

Shield is being rebuilt as a small, privacy-first, local-only Windows desktop
app. v0.1 focuses on a calm pause layer and local check-ins, not heavy detection
or system protection.

## Code Placement Rules

- New product code lives under `src/shield/`.
- UI code lives under `src/shield/ui/`.
- The current UI stack is PyQt6.
- Do not reintroduce root-level `core.py`.
- Do not reintroduce root-level `main.py`.
- Do not reintroduce root-level `ui/`.
- Do not add old heavy backend modules back into the root package.

## Forbidden Unless Explicitly Requested

Do not add or reintroduce any of the following without a dedicated approved
task:

- NudeNet or other NSFW model integration
- DNS proxy or DNS interception
- screenshot capture
- `mss`, `dxcam`, OpenCV, Pillow, or image-processing dependencies
- SMTP or accountability email
- NSSM or service installation
- uninstall protection
- hard process protection
- network calls
- telemetry
- cloud sync

## UI Rules

- Do not launch real fullscreen UI from automated tests or noninteractive
  automation.
- UI tests should use offscreen mode, monkeypatching, import tests, or smoke
  tests.
- UI tone must be calm, non-shaming, and minimal.

## Data And Privacy Rules

- v0.1 stores data locally only.
- Do not add network features unless explicitly requested.
- Do not write screenshots or browser history to disk.
- Do not overclaim medical, therapeutic, or addiction-treatment outcomes.

## Testing Rules

Before reporting a task as complete, run the test suite with the available
Python interpreter.

Preferred command:

```powershell
python -m pytest
```

If `python` is unavailable on Windows, use the known local interpreter, for
example:

```powershell
"C:\Users\Serdar Arif\AppData\Local\Programs\Python\Python314\python.exe" -m pytest
```

## Durable Memory Rule

These docs are project memory, not one-time notes.

Mandatory rule: "If you changed code, architecture, scope, commands, constraints, or project direction, update the relevant memory docs in the same task before reporting completion."

If you changed code, architecture, behavior, scope, commands, tests,
constraints, or project direction, update the relevant memory docs in the same
task before reporting completion.

At minimum, consider whether these files need updates:

- `STATUS.md`
- `ARCHITECTURE.md`
- `DECISIONS.md`
- `TASKS.md`
- `AI_HANDOFF.md`
- `README.md`

If a change affects these docs and the agent does not update them, the task is
incomplete.

Decision history rule: "If a decision changes or a previous decision is reversed, do not silently overwrite history. Add a new decision entry explaining the change and reference the old decision."

## Completion Report

At completion, report:

- tests run and result
- files changed
- docs updated
- any skipped or known limitations
- commit hash if committed
- what should be done next
- whether the working tree is clean
