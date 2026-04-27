# AI Handoff

This is the fast-start summary for the next AI assistant.

## Last Known State

- Last known branch: `rebuild/v0-clean`
- Latest known product checkpoint: `1aed822 feat: add morning check-in screen`
- Latest docs/process changeset: current commit containing these memory docs.
  Verify the exact hash with `git log -1 --oneline`.
- Current tests: `29 passed`

## What Exists Now

- clean v0.1 scaffold
- PyQt6 pause overlay
- PyQt6 morning check-in
- local SQLite event/check-in store

## What Is Not Present

- dashboard
- settings
- onboarding
- detection
- screenshot capture
- DNS
- SMTP
- service or uninstall protection

## Current Recommended Next Task

Add a lightweight dashboard read-only view.

## Handoff Protocol

1. Read memory docs.
2. Summarize understanding.
3. Confirm branch.
4. Run tests before and after changes when relevant.
5. Update memory docs if changing the project.
6. Do not commit without approval.

If you changed code, architecture, scope, commands, constraints, or project
direction, update the relevant memory docs in the same task before reporting
completion.

Mandatory rule: "If you changed code, architecture, scope, commands, constraints, or project direction, update the relevant memory docs in the same task before reporting completion."

Decision history rule: "If a decision changes or a previous decision is reversed, do not silently overwrite history. Add a new decision entry explaining the change and reference the old decision."

## Recent Work Log

- `69b001c chore: rebuild clean v0.1 scaffold`
- `99a0a4a feat: add PyQt6 pause overlay`
- `1aed822 feat: add morning check-in screen`
- Current docs/process changeset: add durable AI project memory docs.
