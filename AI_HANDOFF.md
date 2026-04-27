# AI Handoff

This is the fast-start summary for the next AI assistant.

## Last Known State

- Last known branch: `rebuild/v0-clean`
- Latest known committed product checkpoint:
  `223105a feat: use saved alternative actions in overlay`
- Latest known fix:
  `9753375 fix: recognize today's dashboard checkin`
- Current tests: `91 passed`

## What Exists Now

- clean v0.1 scaffold
- PyQt6 pause overlay (`--screen overlay`)
- PyQt6 morning check-in (`--screen checkin`)
- PyQt6 read-only dashboard (`--screen dashboard`)
- PyQt6 local-only settings (`--screen settings`)
- explicit demo overlay flow (`--demo-trigger --show-overlay`)
- PyQt6 local-only onboarding (`--screen onboarding`)
- default startup routing (`python -m shield.app`)
- overlay action cards use saved local `alternative_actions`
- local SQLite event/check-in/settings store

## What Is Not Present

- detection
- screenshot capture
- DNS
- SMTP sending
- service or uninstall protection

## Current Recommended Next Task

README/release polish for v0.1 alpha.

## Handoff Protocol

1. Read memory docs.
2. Summarize understanding.
3. Confirm branch.
4. Run tests before and after changes when relevant.
5. Update memory docs if changing the project.
6. Do not commit without approval.
7. Do not run `git add`, `git commit`, `git push`, `git rebase`,
   `git checkout`, or `git reset` by default.
8. Ask the user to handle Git writes manually.
9. Only use read-only Git commands unless explicitly authorized.

If you changed code, architecture, scope, commands, constraints, or project
direction, update the relevant memory docs in the same task before reporting
completion.

Mandatory rule: "If you changed code, architecture, scope, commands, constraints, or project direction, update the relevant memory docs in the same task before reporting completion."

Decision history rule: "If a decision changes or a previous decision is reversed, do not silently overwrite history. Add a new decision entry explaining the change and reference the old decision."

## Recent Work Log

- `69b001c chore: rebuild clean v0.1 scaffold`
- `99a0a4a feat: add PyQt6 pause overlay`
- `1aed822 feat: add morning check-in screen`
- Docs/process changeset: add durable AI project memory docs.
- `6f50b55 feat: add read-only dashboard`
- `78526cd feat: add local settings screen`
- `19ec0c8 feat: wire demo trigger to overlay flow`
- `caa9356 feat: add onboarding`
- `9753375 fix: recognize today's dashboard checkin`
- `d9ce5d4 feat: add default startup flow`
- `223105a feat: use saved alternative actions in overlay`
- Manual UI smoke test: `PASS`; no P0 blocker found.

## Manual UI Smoke Notes

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
- overall UI needs visual polish later; this is not a v0.1 alpha release
  blocker
