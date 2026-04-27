# Tasks

This file is the single source of truth for current and next work.

## Current State

- Working branch: `rebuild/v0-clean`
- Tests passing: `91 passed`
- Latest known committed product checkpoint:
  `223105a feat: use saved alternative actions in overlay`
- Latest known fix:
  `9753375 fix: recognize today's dashboard checkin`

## Completed Checkpoints

- `69b001c chore: rebuild clean v0.1 scaffold`
- `99a0a4a feat: add PyQt6 pause overlay`
- `1aed822 feat: add morning check-in screen`
- `6f50b55 feat: add read-only dashboard`
- `78526cd feat: add local settings screen`
- `19ec0c8 feat: wire demo trigger to overlay flow`
- `caa9356 feat: add onboarding`
- `9753375 fix: recognize today's dashboard checkin`
- `d9ce5d4 feat: add default startup flow`
- `223105a feat: use saved alternative actions in overlay`
- Manual UI smoke test: `PASS` with non-blocking polish notes.

## Current Task

No active task.

## Next Recommended Tasks

1. README/release polish for v0.1 alpha.
2. Later: optional local detection.
3. Later: optional DNS/domain heuristics.
4. Later: installer/release packaging.

## Known Non-Blocking Polish Notes

- Onboarding step 3 spacing feels too spread out.
- Settings is functional but visually dense/amateur.
- Dashboard is functional but could be more polished.
- Overall UI needs visual polish later; this is not a v0.1 alpha release
  blocker.

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
