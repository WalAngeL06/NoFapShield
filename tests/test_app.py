import os
import subprocess
import sys
from pathlib import Path

import pytest

from shield.app import main
from shield.db import EventStore


def _parse_output(output: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for line in output.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        parsed[key] = value
    return parsed


def _patch_default_screen_delegates(monkeypatch) -> list[tuple[str, str]]:
    calls: list[tuple[str, str]] = []

    def fake_dashboard(db_path: str) -> int:
        calls.append(("dashboard", db_path))
        return 41

    def fake_onboarding(db_path: str) -> int:
        calls.append(("onboarding", db_path))
        return 67

    monkeypatch.setattr("shield.app._run_dashboard_screen", fake_dashboard)
    monkeypatch.setattr("shield.app._run_onboarding_screen", fake_onboarding)
    return calls


def test_demo_trigger_cli_prints_event_summary(tmp_path, capsys, monkeypatch):
    db_path = tmp_path / "demo.db"
    overlay_calls: list[None] = []
    default_calls: list[None] = []

    def fake_overlay(db_path=None) -> int:
        del db_path
        overlay_calls.append(None)
        return 0

    monkeypatch.setattr("shield.app._run_overlay_screen", fake_overlay)
    monkeypatch.setattr(
        "shield.app._run_default_screen",
        lambda db_path: default_calls.append(None) or 99,
    )

    result = main(["--demo-trigger", "--db-path", str(db_path)])

    output = capsys.readouterr().out
    parsed = _parse_output(output)
    assert result == 0
    assert parsed["shield.demo_trigger"] == "ok"
    assert parsed["source"] == "demo"
    assert parsed["reason"] == "manual demo trigger"
    assert parsed["score"] == "1.00"
    assert parsed["threshold"] == "0.70"
    assert parsed["session_id"]
    assert "overlay" not in parsed
    assert overlay_calls == []
    assert default_calls == []

    store = EventStore(db_path)
    assert store.count_events() == 1
    row = store.list_events()[0]
    assert row["session_id"] == parsed["session_id"]
    assert row["source"] == parsed["source"]
    assert row["reason"] == parsed["reason"]
    assert row["score"] == float(parsed["score"])
    assert row["threshold"] == float(parsed["threshold"])


def test_demo_trigger_show_overlay_records_event_and_delegates(tmp_path, capsys, monkeypatch):
    db_path = tmp_path / "demo.db"
    with EventStore(db_path) as store:
        store.set_setting("alternative_actions", ["Yuru", "Su ic"])
    received_actions: list[list[str] | None] = []

    def fake_overlay(*, alternative_actions=None, countdown_seconds=15) -> int:
        del countdown_seconds
        received_actions.append(alternative_actions)
        return 17

    monkeypatch.setattr("shield.ui.blur_overlay.run_overlay", fake_overlay)

    result = main(["--demo-trigger", "--show-overlay", "--db-path", str(db_path)])

    output = capsys.readouterr().out
    parsed = _parse_output(output)
    assert result == 17
    assert parsed["shield.demo_trigger"] == "ok"
    assert parsed["source"] == "demo"
    assert parsed["reason"] == "manual demo trigger"
    assert parsed["score"] == "1.00"
    assert parsed["threshold"] == "0.70"
    assert parsed["session_id"]
    assert parsed["overlay"] == "launched"
    assert received_actions == [["Yuru", "Su ic"]]

    store = EventStore(db_path)
    assert store.count_events() == 1
    row = store.list_events()[0]
    assert row["session_id"] == parsed["session_id"]
    assert row["source"] == parsed["source"]
    assert row["reason"] == parsed["reason"]


def test_show_overlay_without_demo_trigger_errors(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--show-overlay"])

    assert exc.value.code == 2
    assert "--show-overlay requires --demo-trigger" in capsys.readouterr().err


def test_default_startup_without_completion_delegates_to_onboarding(tmp_path, monkeypatch):
    db_path = tmp_path / "settings.db"
    calls = _patch_default_screen_delegates(monkeypatch)

    result = main(["--db-path", str(db_path)])

    assert result == 67
    assert calls == [("onboarding", str(db_path))]


def test_default_startup_with_false_completion_delegates_to_onboarding(tmp_path, monkeypatch):
    db_path = tmp_path / "settings.db"
    with EventStore(db_path) as store:
        store.set_setting("onboarding_completed", False)
    calls = _patch_default_screen_delegates(monkeypatch)

    result = main(["--db-path", str(db_path)])

    assert result == 67
    assert calls == [("onboarding", str(db_path))]


@pytest.mark.parametrize("completed_value", [True, "true", "True", "1", 1])
def test_default_startup_with_completed_value_delegates_to_dashboard(
    tmp_path,
    monkeypatch,
    completed_value,
):
    db_path = tmp_path / "settings.db"
    with EventStore(db_path) as store:
        store.set_setting("onboarding_completed", completed_value)
    calls = _patch_default_screen_delegates(monkeypatch)

    result = main(["--db-path", str(db_path)])

    assert result == 41
    assert calls == [("dashboard", str(db_path))]


def test_default_startup_with_malformed_completion_delegates_to_onboarding(tmp_path, monkeypatch):
    db_path = tmp_path / "settings.db"
    with EventStore(db_path) as store:
        store.set_setting("onboarding_completed", {"completed": True})
    calls = _patch_default_screen_delegates(monkeypatch)

    result = main(["--db-path", str(db_path)])

    assert result == 67
    assert calls == [("onboarding", str(db_path))]


def test_default_startup_when_settings_read_fails_delegates_to_onboarding(monkeypatch):
    class BrokenStore:
        def __init__(self, db_path: str) -> None:
            del db_path
            raise RuntimeError("settings unavailable")

    calls = _patch_default_screen_delegates(monkeypatch)
    monkeypatch.setattr("shield.app.EventStore", BrokenStore)

    result = main(["--db-path", "unreadable.db"])

    assert result == 67
    assert calls == [("onboarding", "unreadable.db")]


def test_overlay_screen_delegates_to_ui(monkeypatch):
    monkeypatch.setattr("shield.app._run_overlay_screen", lambda db_path: 23)

    result = main(["--screen", "overlay"])

    assert result == 23


def test_overlay_screen_reads_saved_alternative_actions(tmp_path, monkeypatch):
    db_path = tmp_path / "settings.db"
    with EventStore(db_path) as store:
        store.set_setting("alternative_actions", ["  Yuru  ", "", "Su ic", "Nefes", "Fazla"])
    received_actions: list[list[str] | None] = []

    def fake_overlay(*, alternative_actions=None, countdown_seconds=15) -> int:
        del countdown_seconds
        received_actions.append(alternative_actions)
        return 23

    monkeypatch.setattr("shield.ui.blur_overlay.run_overlay", fake_overlay)

    result = main(["--screen", "overlay", "--db-path", str(db_path)])

    assert result == 23
    assert received_actions == [["Yuru", "Su ic", "Nefes"]]


def test_overlay_screen_falls_back_when_actions_missing(tmp_path, monkeypatch):
    db_path = tmp_path / "settings.db"
    received_actions: list[list[str] | None] = []

    def fake_overlay(*, alternative_actions=None, countdown_seconds=15) -> int:
        del countdown_seconds
        received_actions.append(alternative_actions)
        return 23

    monkeypatch.setattr("shield.ui.blur_overlay.run_overlay", fake_overlay)

    result = main(["--screen", "overlay", "--db-path", str(db_path)])

    assert result == 23
    assert received_actions == [None]


def test_checkin_screen_delegates_to_ui(monkeypatch, tmp_path):
    db_path = tmp_path / "checkin.db"
    received: list[str] = []

    def fake_checkin(path: str) -> int:
        received.append(path)
        return 31

    monkeypatch.setattr("shield.app._run_checkin_screen", fake_checkin)

    result = main(["--screen", "checkin", "--db-path", str(db_path)])

    assert result == 31
    assert received == [str(db_path)]


def test_dashboard_screen_delegates_to_ui(monkeypatch):
    monkeypatch.setattr("shield.app._run_dashboard_screen", lambda db_path: 41)

    result = main(["--screen", "dashboard"])

    assert result == 41


def test_settings_screen_delegates_to_ui(monkeypatch):
    monkeypatch.setattr("shield.app._run_settings_screen", lambda db_path: 53)

    result = main(["--screen", "settings"])

    assert result == 53


def test_onboarding_screen_delegates_to_ui(monkeypatch):
    monkeypatch.setattr("shield.app._run_onboarding_screen", lambda db_path: 67)

    result = main(["--screen", "onboarding"])

    assert result == 67


def test_module_entrypoint_runs_from_outside_repo(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    src_path = repo_root / "src"
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(src_path)
        if not existing_pythonpath
        else os.pathsep.join([str(src_path), existing_pythonpath])
    )

    result = subprocess.run(
        [sys.executable, "-m", "shield.app", "--demo-trigger"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    parsed = _parse_output(result.stdout)
    assert parsed["shield.demo_trigger"] == "ok"
    assert parsed["source"] == "demo"
    assert parsed["reason"] == "manual demo trigger"
    assert parsed["score"] == "1.00"
    assert parsed["threshold"] == "0.70"
    assert parsed["session_id"]
