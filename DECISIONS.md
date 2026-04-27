# Architecture Decisions

This file is append-only project memory. Do not silently rewrite decision
history.

If a decision changes or a previous decision is reversed, add a new decision
entry explaining the change and reference the old decision.

## Decision 001: Clean Rebuild On `rebuild/v0-clean`

- Status: Accepted
- Date: 2026-04-27

### Context

The previous implementation had become tangled with root-level entrypoints,
heavy feature experiments, and unclear boundaries.

### Decision

Rebuild v0.1 on `rebuild/v0-clean` instead of continuing the old tangled
implementation.

### Consequences

- Product code belongs under `src/shield/`.
- Root-level `core.py`, `main.py`, and `ui/` must not return.
- Legacy modules are not preserved as compatibility shims.

## Decision 002: v0.1 Starts With Manual/Demo Trigger Only

- Status: Accepted
- Date: 2026-04-27

### Context

Detection features raise privacy, accuracy, dependency, and platform risks.

### Decision

v0.1 starts with a manual/demo trigger and local event persistence only.

### Consequences

- `python -m shield.app --demo-trigger` is the supported trigger path.
- No content detection is included in v0.1.
- Future detection must be added deliberately and documented.

## Decision 003: UI Stack Is PyQt6

- Status: Accepted
- Date: 2026-04-27

### Context

The pause overlay first explored a native Win32 approach, but the project needs
a maintainable Python UI stack.

### Decision

Use PyQt6 for UI screens instead of raw Win32 APIs.

### Consequences

- PyQt6 is a runtime dependency.
- UI code lives under `src/shield/ui/`.
- Tests must not launch real fullscreen windows.

## Decision 004: Detection, Privacy Expansion, And System Hardening Are Postponed

- Status: Accepted
- Date: 2026-04-27

### Context

Features such as NSFW detection, DNS interception, screenshot capture, service
installation, and uninstall protection have high privacy and platform impact.

### Decision

Postpone detection, privacy-sensitive monitoring, and system hardening until a
future milestone explicitly scopes them.

### Consequences

- No NudeNet, DNS proxy, screenshot capture, SMTP, NSSM, uninstall protection,
  or hard process protection in the current scope.
- Documentation must avoid claiming those features exist.

## Decision 005: AI Project Memory Must Be Maintained

- Status: Accepted
- Date: 2026-04-27

### Context

Multiple AI coding tools may continue the project. Without durable memory, they
can lose branch, scope, architecture, and safety constraints.

### Decision

Every AI that changes code, architecture, scope, commands, constraints, or
project direction must update the relevant memory docs before reporting
completion.

### Consequences

- `AGENTS.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `TASKS.md`,
  `AI_HANDOFF.md`, `STATUS.md`, and `README.md` must stay current.
- Updating the docs is part of the task, not optional cleanup.

## Decision 006: Decisions Are Append-Only

- Status: Accepted
- Date: 2026-04-27

### Context

Silent edits to past decisions hide why the project changed direction.

### Decision

Decision history is append-only. If a decision is reversed or materially
changed, add a new decision entry and reference the old decision.

### Consequences

- Do not delete old decisions to make history look cleaner.
- New agents can understand both the original rationale and later changes.

