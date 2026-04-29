# Shield v0.1 Alpha Release Checklist

This document is the release gate for the v0.1 alpha tag. It records the
current verification snapshot, release scope, explicit exclusions, and manual
steps to complete before tagging.

## 1. Release Target

- Tag: `v0.1.0-alpha`
- Release title suggestion: `Shield v0.1.0-alpha — Local-only pause layer MVP`
- Release type: alpha / developer preview / local-only MVP

This is not a packaged installer release unless packaging is added later.
Running v0.1 alpha currently requires a local Python environment from the
repository checkout.

## Release Publication Status

- Tag pushed: `v0.1.0-alpha`
- GitHub Release published: `Shield v0.1.0-alpha — Local-only pause layer MVP`
- Target commit:
  `3aa3980 chore: refresh memory docs after release checklist commit`
- Release type: pre-release / alpha / developer preview
- Tests before tag: `91 passed`
- Manual UI smoke: `PASS`
- Working tree was clean before tag.
- No packaged installer yet.

## 2. Current Verification Snapshot

- Automated tests: `91 passed`
- Manual UI smoke: `PASS`
- No P0 blocker found.

Manual commands checked:

```powershell
python -m shield.app
python -m shield.app --screen onboarding
python -m shield.app --screen dashboard
python -m shield.app --screen settings
python -m shield.app --screen checkin
python -m shield.app --demo-trigger --show-overlay
```

## 3. Included In v0.1 Alpha

- Local onboarding.
- Default startup flow.
- Fullscreen pause overlay.
- Saved alternative actions in overlay.
- Morning check-in.
- Read-only dashboard.
- Local settings.
- Demo trigger.
- Local SQLite storage.
- Memory docs / AI handoff workflow.

## 4. Explicitly Not Included

- No content detection.
- No DNS interception/proxy.
- No screenshot capture.
- No cloud sync.
- No telemetry.
- No network calls.
- No SMTP/email sending.
- No accountability delivery.
- No Windows service/NSSM.
- No uninstall protection.
- No hard process protection.
- No packaged installer yet.
- No medical/addiction cure claim.

## 5. Known Non-Blocking Polish Notes

These polish notes are not blocking v0.1 alpha:

- Onboarding step 3 spacing feels too spread out.
- Settings is functional but visually dense/amateur.
- Dashboard is functional but could be more polished.
- Overall UI needs visual polish later.

## 6. Pre-Tag Checklist

- [x] Tests pass.
- [x] Manual UI smoke pass.
- [x] README polished.
- [x] Release checklist present.
- [x] Privacy/limitations clear in README.
- [x] No prohibited scope added.
- [x] Working tree clean before tag.
- [ ] Branch pushed to origin.
- [x] Optional: final review no findings.

## 7. Suggested Release Notes Draft

Copy-pasteable draft:

````markdown
# Shield v0.1.0-alpha

## Summary

Shield v0.1.0-alpha is a local-only pause layer MVP for Windows desktop
self-control. It focuses on calm friction, local check-ins, and a simple
developer-preview workflow. It is not a packaged installer release.

## What Works

- Local onboarding for a personal goal, alternative actions, and an optional
  local email placeholder.
- Default startup with `python -m shield.app`, routing to onboarding or the
  dashboard based on local onboarding state.
- Fullscreen pause overlay.
- Saved alternative actions in the overlay.
- Morning check-in screen.
- Read-only local dashboard.
- Local settings screen.
- Demo trigger for a synthetic local friction event.
- Local SQLite storage for events, check-ins, and settings.
- Durable memory docs and AI handoff workflow.

## What Is Intentionally Not Included

- No content detection.
- No DNS interception or DNS proxy.
- No screenshot capture.
- No cloud sync.
- No telemetry.
- No network calls.
- No SMTP or email sending.
- No accountability delivery.
- No Windows service or NSSM integration.
- No uninstall protection.
- No hard process protection.
- No packaged installer yet.
- No medical, addiction treatment, or cure claim.

## Known Limitations

- Onboarding step 3 spacing needs polish.
- Settings is functional but visually dense.
- Dashboard is functional but can be visually improved.
- Overall UI polish is planned for later.
- This alpha must be run from a local Python environment.

## How To Run Locally

```powershell
pip install -e ".[dev]"
python -m pytest
python -m shield.app
```

Useful manual commands:

```powershell
python -m shield.app --screen onboarding
python -m shield.app --screen dashboard
python -m shield.app --screen settings
python -m shield.app --screen checkin
python -m shield.app --screen overlay
python -m shield.app --demo-trigger
python -m shield.app --demo-trigger --show-overlay
```

## Verification Status

- Automated tests: 91 passed.
- Manual UI smoke: PASS.
- No P0 blocker found.
````

## 8. Manual Tag Commands

These were the intended manual tag commands. `v0.1.0-alpha` is now published,
so do not rerun them for the same tag.

```powershell
git status
git log --oneline -8
git tag -a v0.1.0-alpha -m "Shield v0.1.0-alpha"
git push origin v0.1.0-alpha
```

For future releases, run equivalent commands manually only after the working
tree is clean, the branch is pushed, and final verification is complete.

## 9. Next After Release

- Windows packaging / installer planning.
- UI visual polish.
- Optional local detection later.
- Optional DNS/domain heuristics later.
