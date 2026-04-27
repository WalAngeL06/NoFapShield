import os
import subprocess
import sys
from pathlib import Path

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


def test_demo_trigger_cli_prints_event_summary(tmp_path, capsys):
    db_path = tmp_path / "demo.db"

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

    store = EventStore(db_path)
    assert store.count_events() == 1
    row = store.list_events()[0]
    assert row["session_id"] == parsed["session_id"]
    assert row["source"] == parsed["source"]
    assert row["reason"] == parsed["reason"]
    assert row["score"] == float(parsed["score"])
    assert row["threshold"] == float(parsed["threshold"])


def test_cli_without_command_prints_help(capsys):
    result = main([])

    output = capsys.readouterr().out
    assert result == 0
    assert "--demo-trigger" in output


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
