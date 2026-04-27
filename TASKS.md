# Tasks

This file is the single source of truth for current and next work.

## Current State

- Working branch: `rebuild/v0-clean`
- Tests passing: `61 passed`
- Latest known product checkpoint: settings screen (pending commit)

## Completed Checkpoints

- `69b001c chore: rebuild clean v0.1 scaffold`
- `99a0a4a feat: add PyQt6 pause overlay`
- `1aed822 feat: add morning check-in screen`
- (pending) feat: add read-only dashboard screen
- (pending) feat: add local-only settings screen

## Current Task

No active task. Settings delivered; awaiting user commit.

## Next Recommended Tasks

1. Wire manual demo trigger to overlay flow (use saved alternative actions).
2. Add onboarding.
3. Later: optional local detection.
4. Later: optional DNS/domain heuristics.
5. Later: installer/release packaging.

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
