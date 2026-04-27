import json

import pytest

from shield.core.config import Config


def test_defaults_are_v01_scaffold_values():
    config = Config()

    assert config.trigger_threshold == 0.7
    assert config.demo_score == 1.0
    assert config.friction_delay_seconds == 15
    assert config.db_path == ":memory:"


def test_load_from_file_ignores_unknown_keys(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps({"trigger_threshold": 0.5, "future_key": "ignored"}),
        encoding="utf-8",
    )

    config = Config.from_file(path)

    assert config.trigger_threshold == 0.5
    assert not hasattr(config, "future_key")


def test_invalid_json_uses_defaults(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{bad json", encoding="utf-8")

    assert Config.from_file(path) == Config()


def test_save_roundtrip(tmp_path):
    original = Config(
        trigger_threshold=0.6,
        demo_score=0.9,
        friction_delay_seconds=20,
        db_path=str(tmp_path / "shield.db"),
    )
    path = tmp_path / "settings.json"

    original.save(path)

    assert Config.from_file(path) == original


def test_probability_fields_are_validated():
    with pytest.raises(ValueError, match="trigger_threshold"):
        Config(trigger_threshold=1.5)

    with pytest.raises(ValueError, match="demo_score"):
        Config(demo_score=-0.1)
