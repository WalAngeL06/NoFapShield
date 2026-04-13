import json
import pytest
from pathlib import Path
from shield.core.config import Config


def test_default_threshold():
    config = Config()
    assert config.detection_threshold == 0.7


def test_default_screenshot_interval():
    config = Config()
    assert config.screenshot_interval == 3


def test_load_from_file(tmp_path):
    settings = {"detection_threshold": 0.5, "screenshot_interval": 5}
    f = tmp_path / "settings.json"
    f.write_text(json.dumps(settings))
    config = Config.from_file(f)
    assert config.detection_threshold == 0.5
    assert config.screenshot_interval == 5


def test_save_to_file(tmp_path):
    config = Config(detection_threshold=0.8)
    f = tmp_path / "settings.json"
    config.save(f)
    data = json.loads(f.read_text())
    assert data["detection_threshold"] == 0.8


def test_missing_file_uses_defaults(tmp_path):
    config = Config.from_file(tmp_path / "nonexistent.json")
    assert config.detection_threshold == 0.7


def test_invalid_json_uses_defaults(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text("not valid json {{{")
    config = Config.from_file(f)
    assert config.detection_threshold == 0.7


def test_unknown_keys_ignored(tmp_path):
    settings = {"detection_threshold": 0.6, "unknown_key": "ignored"}
    f = tmp_path / "settings.json"
    f.write_text(json.dumps(settings))
    config = Config.from_file(f)
    assert config.detection_threshold == 0.6


def test_roundtrip(tmp_path):
    original = Config(detection_threshold=0.6, screenshot_interval=5, dns_score_ttl=15)
    f = tmp_path / "settings.json"
    original.save(f)
    loaded = Config.from_file(f)
    assert loaded.detection_threshold == 0.6
    assert loaded.screenshot_interval == 5
    assert loaded.dns_score_ttl == 15
