from pathlib import Path


def test_no_legacy_root_entrypoints_or_ui_package():
    repo_root = Path(__file__).resolve().parents[1]

    assert not (repo_root / "core.py").exists()
    assert not (repo_root / "main.py").exists()
    assert not (repo_root / "ui").exists()
    assert not (repo_root / "shield").exists()
