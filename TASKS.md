# Tasks

This file is the single source of truth for current and next work.

## Current State

- Working branch: `rebuild/v0-clean`
- Tests passing: `72 passed`
- Latest known committed product checkpoint:
  `19ec0c8 feat: wire demo trigger to overlay flow`
- Current local product change: `feat: add onboarding` implemented locally; user
  controls Git writes.

## Completed Checkpoints

- `69b001c chore: rebuild clean v0.1 scaffold`
- `99a0a4a feat: add PyQt6 pause overlay`
- `1aed822 feat: add morning check-in screen`
- `6f50b55 feat: add read-only dashboard`
- `78526cd feat: add local settings screen`
- `19ec0c8 feat: wire demo trigger to overlay flow`

## Current Task

Add onboarding.

- Status: implemented locally, not committed by the AI.

## Next Recommended Tasks

1. Review and manually commit the local onboarding change.
2. Later: optional local detection.
3. Later: optional DNS/domain heuristics.
4. Later: installer/release packaging.

## Rules For Updating This File

- Mark completed work.
- Move the next task forward.
- Add blockers or risks when discovered.
- Do not leave a stale current task after finishing work.
- Git operations are user-controlled.
- Future AI agents should not run Git write operations unless explicitly
  requested.
- If code, architecture, scope, commands, constraints, or project direction
  changed, update the relevant memory docs in the same task before reporting
  completion.
