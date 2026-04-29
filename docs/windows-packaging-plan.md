# Windows Packaging Plan

This plan describes a future path for turning Shield into a downloadable
Windows app. It is planning only. It does not add a packaged executable,
PyInstaller/Nuitka configuration, installer scripts, service behavior, or any
new product capability.

## 1. Current Release Baseline

- `v0.1.0-alpha` is already tagged and published.
- The current release is not packaged.
- The current release requires a local Python environment.
- Tests: `91 passed`.
- Manual UI smoke: `PASS`.
- The current app is local-only.

## 2. Packaging Goals

- Produce a Windows executable for future releases.
- Eventually attach build artifacts to GitHub Releases.
- Keep v0.1 privacy and scope promises intact.
- Avoid service, uninstall-protection, and hardening behavior in initial
  packaging.

## 3. Candidate Packaging Paths

### PyInstaller

Pros:

- Common first path for Python desktop apps.
- Supports one-folder and one-file builds.
- Works with many PyQt6 apps when Qt plugins are collected correctly.
- Usually fast enough to iterate on local packaging issues.

Cons:

- PyQt6 plugin discovery can be fragile.
- Build output can be large.
- One-file builds can have slower startup and more antivirus false-positive
  risk.
- Packaging rules may need adjustment as resources are added.

PyQt6 considerations:

- Must verify Qt platform plugins are included.
- Must manually smoke test every PyQt6 screen from the packaged build.
- Fullscreen overlay behavior must be tested on Windows from the `dist` output.

Likely risk: medium. PyInstaller is the lowest-friction first attempt, but Qt
plugin and antivirus behavior need explicit testing.

### Nuitka

Pros:

- Can produce more native-looking compiled output.
- May improve startup/runtime behavior for some apps.
- Can be a good later option if PyInstaller output is unstable.

Cons:

- More complex toolchain and longer build times.
- Windows compiler setup adds moving parts.
- PyQt6 packaging still needs careful plugin/resource handling.
- Debugging packaging issues may be slower than with PyInstaller.

PyQt6 considerations:

- Qt plugin collection still matters.
- Build configuration may need more explicit options.
- Fullscreen overlay and local data paths require the same manual validation.

Likely risk: medium-high for the first packaging pass because it adds compiler
and configuration complexity before the raw executable path has been proven.

### Plain Source Checkout

Pros:

- Already works for the v0.1 alpha developer preview.
- Keeps debugging straightforward.
- No packaging-specific failure mode.

Cons:

- Requires local Python and dependency installation.
- Not a downloadable app experience for non-developers.
- Windows Python path and Store-alias issues remain user-visible.

PyQt6 considerations:

- Current source workflow remains the baseline for comparing packaged behavior.

Likely risk: low as a fallback, but it does not meet the future download goal.

Recommended first path:

- Start with a PyInstaller one-folder build.
- Try a one-file build only later if the one-folder build is stable.
- Add an installer only after the raw executable build is stable.

## 4. PyQt6 Packaging Considerations

- Confirm Qt platform plugins are bundled, especially the Windows platform
  plugin.
- Track image/icon resources explicitly if they are added later.
- Manually test fullscreen overlay behavior from the packaged output.
- Expect possible Windows Defender false positives, especially for unsigned
  artifacts.
- Plan code signing later, after the raw build path is stable.
- Avoid UPX initially unless there is a clear, documented reason to use it.

## 5. Proposed Packaging Phases

### Phase 1: Local One-Folder Executable

- Add a local one-folder executable build.
- Do not add an installer.
- Manually smoke test from the `dist` folder.

### Phase 2: GitHub Release Asset Zip

- Zip the verified one-folder output.
- Attach the zip to a GitHub Release.
- Include clear install and run instructions.

### Phase 3: Installer Planning

- Compare Inno Setup, WiX, and NSIS.
- Plan app icon handling.
- Plan Start Menu shortcut behavior.
- Plan a normal uninstall entry.
- Do not add uninstall protection.

### Phase 4: Optional Code Signing

- Evaluate code signing after raw executable and release asset flow are stable.
- Document signing requirements, costs, and release workflow impact before
  adopting it.

## 6. Packaging Smoke Test Checklist

- [ ] App launches.
- [ ] Onboarding opens.
- [ ] Default startup routes correctly.
- [ ] Dashboard opens.
- [ ] Settings opens.
- [ ] Check-in opens.
- [ ] Overlay opens.
- [ ] Saved alternative actions appear in overlay.
- [ ] Local SQLite path works.
- [ ] No network calls added.
- [ ] No service installed.
- [ ] Uninstall is normal and transparent.

## 7. Risks / Blockers

- PyQt6 plugin missing issues.
- Fullscreen overlay behavior may differ in a packaged app.
- Unsigned executables can trigger false positives.
- Windows Python path issues should disappear after packaging, but source
  checkout remains affected by local interpreter configuration.
- Data file path handling must be verified outside the source tree.
- Release artifact size may be large.

## 8. Explicit Non-Goals For First Packaging Pass

- No content detection.
- No DNS interception.
- No screenshot capture.
- No service or NSSM integration.
- No uninstall protection.
- No hard process protection.
- No telemetry or cloud sync.
- No network calls.
- No SMTP or email sending.
- No password or login flow.
- No paid or production installer claims.

## 9. Suggested Next Implementation Task

Add PyInstaller one-folder build script/spec as a separate task.
