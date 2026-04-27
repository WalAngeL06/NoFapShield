import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


# ---------------------------------------------------------------------------
# Import smoke
# ---------------------------------------------------------------------------


def test_settings_import_smoke():
    from shield.ui import settings

    assert hasattr(settings, "SettingsWindow")
    assert hasattr(settings, "run_settings")
    assert hasattr(settings, "_active_settings_window")


# ---------------------------------------------------------------------------
# Instantiation / empty state
# ---------------------------------------------------------------------------


def test_settings_window_instantiates_offscreen(qapp):
    from shield.ui.settings import SettingsWindow

    window = SettingsWindow()
    assert window is not None


def test_settings_window_renders_empty_defaults(qapp):
    from shield.ui.settings import SettingsWindow

    window = SettingsWindow()

    assert window._goal_edit.toPlainText() == ""
    assert window._actions_edit.toPlainText() == ""
    assert window._email_edit.text() == ""


# ---------------------------------------------------------------------------
# Loading from provider
# ---------------------------------------------------------------------------


def test_settings_window_loads_from_provider(qapp):
    from shield.ui.settings import SettingsWindow

    stored = {
        "goal_text": "Sakin bir alışkanlık kurmak.",
        "alternative_actions": ["İki dakika yürüyüş", "Bir bardak su iç"],
        "accountability_email": "partner@example.com",
        "detection_sensitivity": 0.5,
    }
    window = SettingsWindow(get_settings=lambda: stored)

    assert window._goal_edit.toPlainText() == "Sakin bir alışkanlık kurmak."
    assert window._actions_edit.toPlainText() == "İki dakika yürüyüş\nBir bardak su iç"
    assert window._email_edit.text() == "partner@example.com"
    assert window._sensitivity_slider.value() == 50


def test_settings_window_loads_partial_provider(qapp):
    from shield.ui.settings import SettingsWindow

    stored = {"goal_text": "Sadece hedef"}
    window = SettingsWindow(get_settings=lambda: stored)

    assert window._goal_edit.toPlainText() == "Sadece hedef"
    assert window._actions_edit.toPlainText() == ""
    assert window._email_edit.text() == ""


# ---------------------------------------------------------------------------
# Saving
# ---------------------------------------------------------------------------


def test_settings_save_calls_provider_with_form_values(qapp):
    from shield.ui.settings import SettingsWindow

    saved: list[dict] = []
    window = SettingsWindow(save_settings=saved.append)

    window._goal_edit.setPlainText("Yeni hedefim")
    window._actions_edit.setPlainText("Eylem 1\nEylem 2")
    window._email_edit.setText("me@example.com")
    window._sensitivity_slider.setValue(70)

    result = window.submit()

    assert result is True
    assert len(saved) == 1
    values = saved[0]
    assert values["goal_text"] == "Yeni hedefim"
    assert values["alternative_actions"] == ["Eylem 1", "Eylem 2"]
    assert values["accountability_email"] == "me@example.com"
    assert values["detection_sensitivity"] == pytest.approx(0.7)


def test_settings_save_strips_blank_action_lines(qapp):
    from shield.ui.settings import SettingsWindow

    saved: list[dict] = []
    window = SettingsWindow(save_settings=saved.append)

    window._actions_edit.setPlainText("  Eylem A  \n\n   \nEylem B\n")
    window.submit()

    assert saved[0]["alternative_actions"] == ["Eylem A", "Eylem B"]


def test_settings_save_shows_success_feedback(qapp):
    from shield.ui.settings import SettingsWindow

    window = SettingsWindow(save_settings=lambda values: None)
    window._goal_edit.setPlainText("Hedef")

    window.submit()

    feedback = window._feedback_label.text().lower()
    assert "kaydedildi" in feedback or "✓" in window._feedback_label.text()


# ---------------------------------------------------------------------------
# Local-only / non-sending labels
# ---------------------------------------------------------------------------


def test_settings_email_field_marked_as_local_only(qapp):
    from shield.ui.settings import SettingsWindow

    window = SettingsWindow()

    helper = window._email_helper.text().lower()
    assert "gönder" in helper or "yerel" in helper


def test_settings_detection_slider_marked_as_inactive(qapp):
    from shield.ui.settings import SettingsWindow

    window = SettingsWindow()

    helper = window._sensitivity_helper.text().lower()
    assert "v0.1" in helper or "aktif değil" in helper


# ---------------------------------------------------------------------------
# run_settings event loop ownership
# ---------------------------------------------------------------------------


def test_run_settings_owns_event_loop_when_no_qapplication(monkeypatch):
    from shield.ui import settings

    _FakeSettingsWindow.instances.clear()

    fake_app = _FakeApplication(exec_result=11)
    fake_qapplication = _FakeQApplication(instance_value=None, created_app=fake_app)
    monkeypatch.setattr(settings, "QApplication", fake_qapplication)
    monkeypatch.setattr(settings, "SettingsWindow", _FakeSettingsWindow)

    result = settings.run_settings(db_path=":memory:")

    assert result == 11
    assert fake_qapplication.created is True
    assert fake_app.exec_called is True
    assert _FakeSettingsWindow.instances[0].shown is True
    assert settings._active_settings_window is None


def test_run_settings_returns_without_exec_when_qapplication_exists(monkeypatch):
    from shield.ui import settings

    _FakeSettingsWindow.instances.clear()

    existing_app = _FakeApplication(exec_result=99)
    fake_qapplication = _FakeQApplication(instance_value=existing_app, created_app=None)
    monkeypatch.setattr(settings, "QApplication", fake_qapplication)
    monkeypatch.setattr(settings, "SettingsWindow", _FakeSettingsWindow)

    result = settings.run_settings(db_path=":memory:")

    assert result == 0
    assert fake_qapplication.created is False
    assert existing_app.exec_called is False
    assert _FakeSettingsWindow.instances[0].shown is True
    assert settings._active_settings_window is _FakeSettingsWindow.instances[0]


# ---------------------------------------------------------------------------
# Fake helpers
# ---------------------------------------------------------------------------


class _FakeApplication:
    def __init__(self, exec_result: int) -> None:
        self.exec_result = exec_result
        self.exec_called = False

    def exec(self) -> int:
        self.exec_called = True
        return self.exec_result


class _FakeQApplication:
    def __init__(self, instance_value, created_app) -> None:
        self.instance_value = instance_value
        self.created_app = created_app
        self.created = False

    def instance(self):
        return self.instance_value

    def __call__(self, args):
        del args
        self.created = True
        return self.created_app


class _FakeSignal:
    def __init__(self) -> None:
        self.callbacks: list = []

    def connect(self, callback) -> None:
        self.callbacks.append(callback)


class _FakeSettingsWindow:
    instances: list = []

    def __init__(self, get_settings=None, save_settings=None) -> None:
        self.get_settings = get_settings
        self.save_settings = save_settings
        self.destroyed = _FakeSignal()
        self.shown = False
        self.raised = False
        self.activated = False
        _FakeSettingsWindow.instances.append(self)

    def show(self) -> None:
        self.shown = True

    def raise_(self) -> None:
        self.raised = True

    def activateWindow(self) -> None:
        self.activated = True
