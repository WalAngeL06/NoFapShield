import os
import subprocess
import sys
from pathlib import Path

import pytest

from shield.app import main
from shield.db import EventStore
from shield.trigger import DEFAULT_RISK_DOMAINS, RISK_DOMAINS_SETTING_KEY


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


def test_trigger_url_no_match_does_not_record_or_open_overlay(tmp_path, capsys, monkeypatch):
    db_path = tmp_path / "trigger.db"
    overlay_calls: list[str | None] = []

    def fake_overlay(db_path=None) -> int:
        overlay_calls.append(db_path)
        return 99

    monkeypatch.setattr("shield.app._run_overlay_screen", fake_overlay)

    result = main(["--trigger-url", "safe.example", "--show-overlay", "--db-path", str(db_path)])

    output = capsys.readouterr().out
    parsed = _parse_output(output)
    assert result == 0
    assert parsed["shield.trigger_url"] == "ok"
    assert parsed["trigger"] == "no_match"
    assert parsed["candidate"] == "safe.example"
    assert "overlay" not in parsed
    assert overlay_calls == []

    with EventStore(db_path) as store:
        assert store.count_events() == 0


def test_trigger_url_match_records_event(tmp_path, capsys, monkeypatch):
    db_path = tmp_path / "trigger.db"
    overlay_calls: list[str | None] = []

    def fake_overlay(db_path=None) -> int:
        overlay_calls.append(db_path)
        return 99

    monkeypatch.setattr("shield.app._run_overlay_screen", fake_overlay)

    result = main(["--trigger-url", "https://Sub.Risk.Example/path", "--db-path", str(db_path)])

    output = capsys.readouterr().out
    parsed = _parse_output(output)
    assert result == 0
    assert parsed["shield.trigger_url"] == "ok"
    assert parsed["trigger"] == "matched"
    assert parsed["candidate"] == "sub.risk.example"
    assert parsed["matched_domain"] == "risk.example"
    assert parsed["event_id"] == "1"
    assert parsed["source"] == "manual_url_trigger"
    assert parsed["reason"] == "local URL/domain trigger matched risk.example"
    assert parsed["session_id"]
    assert "overlay" not in parsed
    assert overlay_calls == []

    with EventStore(db_path) as store:
        rows = store.list_events()
    assert len(rows) == 1
    assert rows[0]["session_id"] == parsed["session_id"]
    assert rows[0]["source"] == "manual_url_trigger"
    assert rows[0]["reason"] == "local URL/domain trigger matched risk.example"


def test_trigger_url_match_show_overlay_delegates_with_saved_actions(
    tmp_path,
    capsys,
    monkeypatch,
):
    db_path = tmp_path / "trigger.db"
    with EventStore(db_path) as store:
        store.set_setting("alternative_actions", ["Yuru", "Su ic"])
    received_actions: list[list[str] | None] = []

    def fake_overlay(*, alternative_actions=None, countdown_seconds=15) -> int:
        del countdown_seconds
        received_actions.append(alternative_actions)
        return 17

    monkeypatch.setattr("shield.ui.blur_overlay.run_overlay", fake_overlay)

    result = main(["--trigger-url", "risk.example", "--show-overlay", "--db-path", str(db_path)])

    output = capsys.readouterr().out
    parsed = _parse_output(output)
    assert result == 17
    assert parsed["trigger"] == "matched"
    assert parsed["overlay"] == "launched"
    assert received_actions == [["Yuru", "Su ic"]]

    with EventStore(db_path) as store:
        assert store.count_events() == 1


def test_trigger_url_invalid_input_is_safe_no_match(tmp_path, capsys, monkeypatch):
    db_path = tmp_path / "trigger.db"
    overlay_calls: list[str | None] = []
    monkeypatch.setattr(
        "shield.app._run_overlay_screen",
        lambda db_path=None: overlay_calls.append(db_path) or 99,
    )

    result = main(["--trigger-url", "not a url", "--show-overlay", "--db-path", str(db_path)])

    output = capsys.readouterr().out
    parsed = _parse_output(output)
    assert result == 0
    assert parsed["shield.trigger_url"] == "ok"
    assert parsed["trigger"] == "invalid"
    assert parsed["candidate"] == "not a url"
    assert "overlay" not in parsed
    assert overlay_calls == []

    with EventStore(db_path) as store:
        assert store.count_events() == 0


def test_trigger_url_uses_custom_risk_domains_from_settings(tmp_path, capsys, monkeypatch):
    db_path = tmp_path / "trigger.db"
    with EventStore(db_path) as store:
        store.set_setting(RISK_DOMAINS_SETTING_KEY, ["focus.example"])
    monkeypatch.setattr("shield.app._run_overlay_screen", lambda db_path=None: 99)

    result = main(["--trigger-url", "https://sub.focus.example/path", "--db-path", str(db_path)])

    parsed = _parse_output(capsys.readouterr().out)
    assert result == 0
    assert parsed["trigger"] == "matched"
    assert parsed["candidate"] == "sub.focus.example"
    assert parsed["matched_domain"] == "focus.example"
    assert parsed["source"] == "manual_url_trigger"

    with EventStore(db_path) as store:
        rows = store.list_events()
    assert len(rows) == 1
    assert rows[0]["reason"] == "local URL/domain trigger matched focus.example"


def test_trigger_url_custom_risk_domains_override_placeholder_defaults(
    tmp_path,
    capsys,
    monkeypatch,
):
    db_path = tmp_path / "trigger.db"
    with EventStore(db_path) as store:
        store.set_setting(RISK_DOMAINS_SETTING_KEY, ["focus.example"])
    overlay_calls: list[str | None] = []
    monkeypatch.setattr(
        "shield.app._run_overlay_screen",
        lambda db_path=None: overlay_calls.append(db_path) or 99,
    )

    result = main(["--trigger-url", "risk.example", "--show-overlay", "--db-path", str(db_path)])

    parsed = _parse_output(capsys.readouterr().out)
    assert result == 0
    assert parsed["trigger"] == "no_match"
    assert parsed["candidate"] == "risk.example"
    assert "overlay" not in parsed
    assert overlay_calls == []
    with EventStore(db_path) as store:
        assert store.count_events() == 0


def test_trigger_url_ignores_invalid_custom_entries(tmp_path, capsys):
    db_path = tmp_path / "trigger.db"
    with EventStore(db_path) as store:
        store.set_setting(RISK_DOMAINS_SETTING_KEY, ["bad_domain.test", "focus.example"])

    result = main(["--trigger-url", "focus.example", "--db-path", str(db_path)])

    parsed = _parse_output(capsys.readouterr().out)
    assert result == 0
    assert parsed["trigger"] == "matched"
    assert parsed["matched_domain"] == "focus.example"


def test_trigger_url_all_invalid_custom_entries_fall_back_to_defaults(tmp_path, capsys):
    db_path = tmp_path / "trigger.db"
    with EventStore(db_path) as store:
        store.set_setting(RISK_DOMAINS_SETTING_KEY, ["bad_domain.test"])

    result = main(["--trigger-url", "risk.example", "--db-path", str(db_path)])

    parsed = _parse_output(capsys.readouterr().out)
    assert result == 0
    assert parsed["trigger"] == "matched"
    assert parsed["matched_domain"] == "risk.example"


def test_trigger_url_reads_newline_separated_risk_domain_setting(tmp_path, capsys):
    db_path = tmp_path / "trigger.db"
    with EventStore(db_path) as store:
        store.set_setting(RISK_DOMAINS_SETTING_KEY, "focus.example\nrest.example")

    result = main(["--trigger-url", "rest.example", "--db-path", str(db_path)])

    parsed = _parse_output(capsys.readouterr().out)
    assert result == 0
    assert parsed["trigger"] == "matched"
    assert parsed["matched_domain"] == "rest.example"


def test_list_risk_domains_prints_fallback_defaults(tmp_path, capsys):
    db_path = tmp_path / "settings.db"

    result = main(["--list-risk-domains", "--db-path", str(db_path)])

    parsed = _parse_output(capsys.readouterr().out)
    assert result == 0
    assert parsed["shield.risk_domains"] == "ok"
    assert parsed["domains"] == ",".join(DEFAULT_RISK_DOMAINS)
    assert parsed["count"] == str(len(DEFAULT_RISK_DOMAINS))


def test_list_risk_domains_prints_custom_active_domains(tmp_path, capsys):
    db_path = tmp_path / "settings.db"
    with EventStore(db_path) as store:
        store.set_setting(RISK_DOMAINS_SETTING_KEY, ["Focus.Example", "bad_domain.test"])

    result = main(["--list-risk-domains", "--db-path", str(db_path)])

    parsed = _parse_output(capsys.readouterr().out)
    assert result == 0
    assert parsed["domains"] == "focus.example"
    assert parsed["count"] == "1"


def test_set_risk_domains_saves_comma_separated_normalized_domains(tmp_path, capsys):
    db_path = tmp_path / "settings.db"

    result = main(
        [
            "--set-risk-domains",
            "Risk.Example, focus.example, risk.example, bad_domain.test",
            "--db-path",
            str(db_path),
        ]
    )

    parsed = _parse_output(capsys.readouterr().out)
    assert result == 0
    assert parsed["shield.risk_domains"] == "ok"
    assert parsed["action"] == "set"
    assert parsed["status"] == "saved"
    assert parsed["domains"] == "risk.example,focus.example"
    assert parsed["count"] == "2"

    with EventStore(db_path) as store:
        assert store.get_setting(RISK_DOMAINS_SETTING_KEY) == ["risk.example", "focus.example"]


def test_set_risk_domains_with_no_valid_domains_does_not_wipe_existing(tmp_path, capsys):
    db_path = tmp_path / "settings.db"
    with EventStore(db_path) as store:
        store.set_setting(RISK_DOMAINS_SETTING_KEY, ["focus.example"])

    result = main(["--set-risk-domains", "bad_domain.test, not a url", "--db-path", str(db_path)])

    parsed = _parse_output(capsys.readouterr().out)
    assert result == 0
    assert parsed["shield.risk_domains"] == "ok"
    assert parsed["action"] == "set"
    assert parsed["status"] == "no_valid_domains"
    assert "domains" not in parsed

    with EventStore(db_path) as store:
        assert store.get_setting(RISK_DOMAINS_SETTING_KEY) == ["focus.example"]


def test_trigger_url_with_screen_errors(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--trigger-url", "risk.example", "--screen", "dashboard"])

    assert exc.value.code == 2
    assert "--trigger-url cannot be used with --screen" in capsys.readouterr().err


def test_trigger_url_with_screen_and_show_overlay_errors(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--trigger-url", "risk.example", "--screen", "dashboard", "--show-overlay"])

    assert exc.value.code == 2
    assert "--trigger-url cannot be used with --screen" in capsys.readouterr().err


def test_show_overlay_without_demo_trigger_errors(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--show-overlay"])

    assert exc.value.code == 2
    assert "--show-overlay requires --demo-trigger" in capsys.readouterr().err


@pytest.mark.parametrize(
    "args",
    [
        ["--list-risk-domains", "--screen", "dashboard"],
        ["--list-risk-domains", "--trigger-url", "risk.example"],
        ["--list-risk-domains", "--demo-trigger"],
        ["--list-risk-domains", "--show-overlay"],
        ["--set-risk-domains", "focus.example", "--screen", "dashboard"],
        ["--set-risk-domains", "focus.example", "--trigger-url", "risk.example"],
        ["--set-risk-domains", "focus.example", "--demo-trigger"],
        ["--set-risk-domains", "focus.example", "--show-overlay"],
    ],
)
def test_risk_domain_commands_reject_other_actions(args, capsys):
    with pytest.raises(SystemExit) as exc:
        main(args)

    assert exc.value.code == 2
    assert "cannot be combined" in capsys.readouterr().err


def test_list_and_set_risk_domains_cannot_be_combined(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--list-risk-domains", "--set-risk-domains", "focus.example"])

    assert exc.value.code == 2
    assert "--list-risk-domains cannot be used with --set-risk-domains" in capsys.readouterr().err


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
