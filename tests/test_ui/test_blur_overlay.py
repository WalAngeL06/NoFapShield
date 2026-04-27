import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication


def test_blur_overlay_import_smoke():
    from shield.ui import blur_overlay

    assert hasattr(blur_overlay, "BlurOverlayWindow")
    assert hasattr(blur_overlay, "normalize_alternative_actions")
    assert hasattr(blur_overlay, "run_overlay")
    assert blur_overlay.COUNTDOWN_SECONDS == 15
    assert len(blur_overlay.ACTION_CARDS) == 3


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def test_blur_overlay_window_close_and_key_guards(qapp):
    from shield.ui.blur_overlay import BlurOverlayWindow

    window = BlurOverlayWindow()

    assert window.can_close() is False
    assert window.should_block_key(Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier) is True
    assert window.should_block_key(Qt.Key.Key_F4, Qt.KeyboardModifier.AltModifier) is True
    assert window.should_block_key(Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier) is False

    window.request_internal_close()

    assert window.can_close() is True


def test_normalize_alternative_actions_trims_filters_and_caps():
    from shield.ui.blur_overlay import normalize_alternative_actions

    actions = normalize_alternative_actions([
        "  Yuru  ",
        "",
        "Su ic",
        42,
        "Nefes",
        "Fazla",
    ])

    assert actions == ["Yuru", "Su ic", "Nefes"]


@pytest.mark.parametrize("value", [None, [], ["   "], {"bad": "value"}, "[]", "{bad json"])
def test_normalize_alternative_actions_falls_back_to_defaults(value):
    from shield.ui.blur_overlay import DEFAULT_ALTERNATIVE_ACTIONS, normalize_alternative_actions

    assert normalize_alternative_actions(value) == list(DEFAULT_ALTERNATIVE_ACTIONS)


def test_blur_overlay_window_renders_custom_action_labels(qapp):
    from shield.ui.blur_overlay import ActionCardButton, BlurOverlayWindow

    window = BlurOverlayWindow(alternative_actions=["  Yuru  ", "Su ic"])

    labels = [button.text() for button in window.findChildren(ActionCardButton)]
    assert any("Yuru" in label for label in labels)
    assert any("Su ic" in label for label in labels)


def test_run_overlay_owns_event_loop_when_no_qapplication(monkeypatch):
    from shield.ui import blur_overlay

    _FakeOverlayWindow.instances.clear()

    fake_app = _FakeApplication(exec_result=42)
    fake_qapplication = _FakeQApplication(instance_value=None, created_app=fake_app)
    monkeypatch.setattr(blur_overlay, "QApplication", fake_qapplication)
    monkeypatch.setattr(blur_overlay, "BlurOverlayWindow", _FakeOverlayWindow)

    result = blur_overlay.run_overlay()

    assert result == 42
    assert fake_qapplication.created is True
    assert fake_app.exec_called is True
    assert _FakeOverlayWindow.instances[-1].shown is True
    assert _FakeOverlayWindow.instances[-1].alternative_actions is None


def test_run_overlay_returns_without_exec_when_qapplication_exists(monkeypatch):
    from shield.ui import blur_overlay

    _FakeOverlayWindow.instances.clear()

    existing_app = _FakeApplication(exec_result=99)
    fake_qapplication = _FakeQApplication(instance_value=existing_app, created_app=None)
    monkeypatch.setattr(blur_overlay, "QApplication", fake_qapplication)
    monkeypatch.setattr(blur_overlay, "BlurOverlayWindow", _FakeOverlayWindow)

    result = blur_overlay.run_overlay()

    assert result == 0
    assert fake_qapplication.created is False
    assert existing_app.exec_called is False
    assert _FakeOverlayWindow.instances[-1].shown is True
    assert blur_overlay._active_overlay_window is _FakeOverlayWindow.instances[-1]


def test_run_overlay_passes_custom_actions_without_owning_event_loop(monkeypatch):
    from shield.ui import blur_overlay

    _FakeOverlayWindow.instances.clear()

    existing_app = _FakeApplication(exec_result=99)
    fake_qapplication = _FakeQApplication(instance_value=existing_app, created_app=None)
    monkeypatch.setattr(blur_overlay, "QApplication", fake_qapplication)
    monkeypatch.setattr(blur_overlay, "BlurOverlayWindow", _FakeOverlayWindow)

    result = blur_overlay.run_overlay(alternative_actions=["Yuru", "Su ic"])

    assert result == 0
    assert existing_app.exec_called is False
    assert _FakeOverlayWindow.instances[-1].alternative_actions == ["Yuru", "Su ic"]


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
        self.callback = None

    def connect(self, callback) -> None:
        self.callback = callback


class _FakeOverlayWindow:
    instances = []

    def __init__(self, countdown_seconds, alternative_actions=None) -> None:
        self.countdown_seconds = countdown_seconds
        self.alternative_actions = alternative_actions
        self.destroyed = _FakeSignal()
        self.shown = False
        self.raised = False
        self.activated = False
        self.instances.append(self)

    def showFullScreen(self) -> None:
        self.shown = True

    def raise_(self) -> None:
        self.raised = True

    def activateWindow(self) -> None:
        self.activated = True
