# Tasks

This file is the single source of truth for current and next work.

## Current State

- Working branch: `rebuild/v0-clean`
- Tests passing: `170 passed`
- Published release:
  `v0.1.0-alpha` / `Shield v0.1.0-alpha — Local-only pause layer MVP`
- Release target commit:
  `3aa3980 chore: refresh memory docs after release checklist commit`
- Latest known committed release docs checkpoint:
  `1717458 docs: plan local trigger MVP for v0.2`
- Latest known product checkpoint:
  `712e62f feat: add editable local trigger risk list`
- Latest known test/config checkpoint:
  `b76abd2 test: use ignored pytest basetemp`
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
- `c812f41 docs: polish README for v0.1 alpha`
- `aa69ee6 docs: add v0.1 alpha release checklist`
- `3aa3980 chore: refresh memory docs after release checklist commit`
- `v0.1.0-alpha` tag pushed and GitHub Release published as a pre-release /
  alpha / developer preview.
- `cffb7f9 docs: record v0.1 alpha release`
- `b175e75 docs: plan Windows packaging path`
- `1717458 docs: plan local trigger MVP for v0.2`
- `c8e8c4a feat: add local URL/domain trigger prototype`
- `b76abd2 test: use ignored pytest basetemp`
- `712e62f feat: add editable local trigger risk list`

## Current Task

Add local trigger allowlist / false-positive handling is implemented locally and
pending user review/commit. The current targeted fix makes default local trigger
settings durable by resolving a user-local SQLite database when `--db-path` is
omitted, while preserving explicit `--db-path` behavior:

- `src/shield/trigger.py`
- `src/shield/app.py`
- `tests/test_trigger.py`
- `tests/test_app.py`
- `README.md`
- `ARCHITECTURE.md`
- `docs/local-trigger-mvp-v0.2.md`
- `STATUS.md`
- `TASKS.md`
- `AI_HANDOFF.md`

## Next Recommended Tasks

1. Add settings UI for local risk/allow list editing.
2. Later: Add PyInstaller one-folder build script/spec.
3. Later: installer planning after raw executable build is stable.
4. Later: UI visual polish.
5. Later: optional browser extension or URL watcher evaluation.

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
