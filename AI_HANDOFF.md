# AI Handoff

This is the fast-start summary for the next AI assistant.

## Last Known State

- Last known branch: `rebuild/v0-clean`
- Published release:
  `v0.1.0-alpha` / `Shield v0.1.0-alpha — Local-only pause layer MVP`
- Release target commit:
  `3aa3980 chore: refresh memory docs after release checklist commit`
- Latest known committed docs checkpoint:
  `1717458 docs: plan local trigger MVP for v0.2`
- Latest known committed product checkpoint:
  `9ee4fc7 feat: add local trigger allowlist`
- Latest known test/config checkpoint:
  `b76abd2 test: use ignored pytest basetemp`
- Latest known fix:
  `9753375 fix: recognize today's dashboard checkin`
- Current tests: `170 passed`
- Manual UI smoke: `PASS`
- Release type: pre-release / alpha / developer preview
- Packaged installer: not included yet
- Current task: No active task.

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
- manual local URL/domain trigger prototype (`--trigger-url`)
- local editable risk list setting: `trigger_risk_domains`
- local allowlist setting for false positives: `trigger_allow_domains`
- local risk-list CLI helpers: `--list-risk-domains` and `--set-risk-domains`
- local allowlist CLI helpers: `--list-allow-domains` and
  `--set-allow-domains`
- default user-local SQLite persistence for trigger settings and events when
  `--db-path` is omitted
- local placeholder trigger risk list fallback: `risk.example`,
  `blocked.example`, `relapse.example`

## What Is Not Present

- content detection
- automatic content blocking
- browser monitoring or browser history scraping
- screenshot capture
- DNS interception/proxy
- cloud sync, telemetry, or network calls
- SMTP/email sending
- accountability delivery
- Windows service or NSSM integration
- uninstall protection or hard process protection
- password or login flow
- packaged installer

## Current Recommended Next Task

Add settings UI for local risk/allow list editing.

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
- `c812f41 docs: polish README for v0.1 alpha`
- `aa69ee6 docs: add v0.1 alpha release checklist`
- `3aa3980 chore: refresh memory docs after release checklist commit`
- `v0.1.0-alpha` tag pushed and GitHub Release published as
  `Shield v0.1.0-alpha — Local-only pause layer MVP`
- `cffb7f9 docs: record v0.1 alpha release`
- `b175e75 docs: plan Windows packaging path`
- `1717458 docs: plan local trigger MVP for v0.2`
- `c8e8c4a feat: add local URL/domain trigger prototype`
- `b76abd2 test: use ignored pytest basetemp`
- `712e62f feat: add editable local trigger risk list`
- `9ee4fc7 feat: add local trigger allowlist`
- Local URL/domain trigger prototype for v0.2 is committed functionality. It is
  manual/CLI-only and does not add automatic browser monitoring, DNS/proxy,
  screenshot capture, network calls, cloud sync, telemetry, SMTP/email sending,
  services, NSSM, uninstall protection, hard process protection,
  password/login, packaging implementation, or complete blocking/porn
  detection claims.
- Local editable risk-list expansion is committed functionality. It stores
  user-owned domains in local SQLite setting `trigger_risk_domains`, adds
  `--list-risk-domains` and `--set-risk-domains`, preserves placeholder
  defaults as fallback, and ships no real adult domains.
- Local allowlist / false-positive handling is committed functionality. It
  stores user-owned allow domains in local SQLite setting
  `trigger_allow_domains`, adds `--list-allow-domains` and
  `--set-allow-domains`, checks allow domains before risk domains, records no
  friction event for allowlisted candidates, launches no overlay for
  allowlisted candidates, and ships no real adult domains.
- Documented trigger settings commands are durable by default through a
  user-local SQLite database. Explicit `--db-path` still fully controls the
  database path for tests and development.

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
