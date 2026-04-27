# AI Handoff

This is the fast-start summary for the next AI assistant.

## Last Known State

- Last known branch: `rebuild/v0-clean`
- Latest known committed product checkpoint:
  `78526cd feat: add local settings screen`
- Current local product change: `feat: wire manual demo trigger to overlay flow`
  implemented locally; user controls Git writes.
- Current tests: `63 passed`

## What Exists Now

- clean v0.1 scaffold
- PyQt6 pause overlay (`--screen overlay`)
- PyQt6 morning check-in (`--screen checkin`)
- PyQt6 read-only dashboard (`--screen dashboard`)
- PyQt6 local-only settings (`--screen settings`)
- explicit demo overlay flow (`--demo-trigger --show-overlay`) in local changes
- local SQLite event/check-in/settings store

## What Is Not Present

- onboarding
- detection
- screenshot capture
- DNS
- SMTP sending
- service or uninstall protection

## Current Recommended Next Task

Review and manually commit the local demo-overlay flow change. After that, add onboarding.

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
- Local, uncommitted: `feat: wire manual demo trigger to overlay flow`
