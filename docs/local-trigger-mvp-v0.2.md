# Local Trigger MVP Plan For v0.2

This document defines the safest small step from Shield v0.1's manual/demo
trigger flow to a real local trigger foundation. It started as the v0.2 MVP
plan and now also records the current local prototype status. The implemented
prototype remains manual/CLI-only and does not add detection, monitoring,
blocking, DNS interception, browser watching, networking, services, or
hardening.

Implementation status: the first manual/CLI local URL/domain trigger prototype
has been added locally on `rebuild/v0-clean` and is pending user review/commit.
It uses placeholder local risk domains only and remains manual, local-only, and
non-monitoring.

## 1. Problem Statement

- v0.1 proves the local UI, data, and overlay flow.
- v0.1 does not detect, block, or monitor content.
- v0.2 should add the first minimal local trigger path.
- The goal is not full porn blocking yet. The goal is a safe trigger
  foundation that can be tested without adding invasive monitoring.

## 2. Product Goal For v0.2

Given a candidate URL, domain, or string, Shield can classify it locally against
a small local risk list.

If the input matches, Shield should:

- Record a local friction event.
- Open the existing pause overlay when explicitly requested.
- Keep all data on the device.

No browser monitoring should be included in the MVP unless it is explicitly
added in a later phase.

## 3. Recommended MVP Scope

Start with:

- A local domain/URL matcher core.
- A small local risk list stored in the repo or in local config.
- A CLI/manual trigger command, for example:

```powershell
python -m shield.app --trigger-url "example.com"
python -m shield.app --trigger-url "example.com" --show-overlay
```

- Event logging through the existing `EventStore`.
- Overlay delegation through the existing overlay path.
- Tests only for automated verification; do not launch real fullscreen UI in
  automated tests.

This scope keeps v0.2 close to the proven v0.1 flow while adding one local
classification step.

## 4. Explicit Non-Goals For v0.2 MVP

- No DNS interception or proxy.
- No screenshot capture.
- No NSFW image model.
- No browser history scraping.
- No always-on background service.
- No Windows service or NSSM integration.
- No uninstall protection.
- No hard process protection.
- No network, cloud, or telemetry.
- No SMTP or email sending.
- No password/login flow.
- No medical or addiction-treatment claims.
- No claim of complete blocking.

## 5. Candidate Trigger Approaches

### A. CLI/Manual URL Trigger

- Value: exercises real local matching, event logging, and overlay delegation.
- Risk: low; it is explicit and user/test driven.
- Privacy impact: low; only the supplied candidate string is processed locally.
- Implementation complexity: low.
- Immediate v0.2 fit: yes. This is the recommended MVP path because it avoids
  invasive monitoring while proving the trigger engine.

### B. Browser Extension Later

- Value: could provide accurate active-tab URL context with user consent.
- Risk: medium; browser extension UX, permissions, and distribution need care.
- Privacy impact: medium; URL visibility is sensitive even if kept local.
- Implementation complexity: medium.
- Immediate v0.2 fit: not yet. Evaluate after the local matcher and CLI trigger
  path are stable.

### C. Local Browser URL Watcher Later

- Value: could trigger from browser state without requiring a browser extension.
- Risk: medium-high; implementation may rely on fragile browser/window
  inspection and can feel like monitoring.
- Privacy impact: medium-high; local browsing context is sensitive.
- Implementation complexity: medium-high.
- Immediate v0.2 fit: no. It should wait until the local trigger contract is
  proven and privacy boundaries are documented.

### D. DNS/Proxy Later

- Value: can catch domain-level requests outside browser UI.
- Risk: high; DNS/proxy behavior changes networking and can break normal use.
- Privacy impact: high; network metadata is sensitive.
- Implementation complexity: high.
- Immediate v0.2 fit: no. It is explicitly out of scope for the MVP.

### E. Screenshot/NSFW Model Much Later, If Ever

- Value: could detect visual content independently of URL.
- Risk: very high; accuracy, privacy, dependencies, and user trust are major
  concerns.
- Privacy impact: very high; screenshots and image processing are sensitive.
- Implementation complexity: high.
- Immediate v0.2 fit: no. This should remain out of scope unless a future
  dedicated milestone explicitly approves it.

## 6. Proposed v0.2 Implementation Phases

### Phase 1: Pure Local Matcher Module

- Add a local matcher for domains, URLs, and candidate strings.
- Test exact domain matches.
- Test subdomain matches.
- Test URL parsing and normalization.
- Test malformed input safe behavior.

### Phase 2: CLI Trigger Command

- Add `--trigger-url`.
- Log matched trigger events through `EventStore`.
- Support optional overlay delegation with `--show-overlay`.
- In tests, monkeypatch overlay launching instead of opening real UI.

### Phase 3: Settings Integration

- Consider local risk-list editing or import if appropriate.
- Consider how existing detection-sensitivity placeholder should map to local
  matcher behavior, if at all.
- Consider an allowlist concept for local false-positive handling.

### Phase 4: Evaluate Browser Extension Or URL Watcher

- Compare browser extension and desktop URL watcher options after the CLI path
  is stable.
- Prefer explicit consent and clear local-only behavior.
- Keep DNS/proxy and screenshot/model approaches out of scope unless a future
  decision changes project direction.

## 7. Data / Privacy Model

- Use a local risk list only.
- Do not perform remote lookups.
- Do not add telemetry.
- Do not upload browsing history.
- Store trigger events in local SQLite only.
- Keep false-positive handling clear and local, for example through a future
  allowlist or editable local list.

## 8. Testing Strategy

Add tests for:

- Exact domain match.
- Subdomain match.
- URL normalization.
- Malformed URL safe behavior.
- Allowlist behavior if the allowlist concept is included.
- CLI trigger records a local event.
- CLI trigger with `--show-overlay` delegates without launching real UI in
  tests.
- No network calls.

## 9. UX Behavior

- Triggered flows should use the existing calm overlay.
- Copy should remain non-shaming.
- Fallback alternative actions should still work.
- Saved alternative actions should still appear in the overlay.
- Trigger events should appear in the dashboard.

## 10. Risks And Decisions Needed

- False positives can erode trust quickly.
- Maintaining risk lists requires an explicit ownership model.
- Decide whether to ship any default risky domains in the repo.
- Decide whether v0.2 should use user-owned local lists only.
- Decide whether a browser extension is cleaner than desktop monitoring for
  future automatic triggers.

## 11. Recommended Next Implementation Task

Expand local trigger configuration / editable local risk list.
