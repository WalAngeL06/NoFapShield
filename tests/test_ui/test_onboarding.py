import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication


import pytest


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def test_onboarding_import_smoke():
    from shield.ui import onboarding

    assert hasattr(onboarding, "OnboardingWindow")
    assert hasattr(onboarding, "run_onboarding")
    assert hasattr(onboarding, "_active_onboarding_window")


def test_onboarding_window_instantiates_offscreen(qapp):
    from shield.ui.onboarding import OnboardingWindow

    window = OnboardingWindow()

    assert window is not None
    assert window.current_step() == 0


def test_default_alternative_actions_render(qapp):
    from shield.ui.onboarding import DEFAULT_ACTIONS, OnboardingWindow

    window = OnboardingWindow()

    assert window.alternative_actions() == list(DEFAULT_ACTIONS)


def test_goal_validation_rejects_short_input(qapp):
    from shield.ui.onboarding import OnboardingWindow

    window = OnboardingWindow()
    window._goal_edit.setPlainText(" kısa ")

    assert window.validate_goal() is False
    assert window.current_step() == 0
    assert window._feedback_label.text()


def test_actions_validation_requires_one_action(qapp):
    from shield.ui.onboarding import OnboardingWindow

    window = OnboardingWindow()
    window._actions_edit.setPlainText("\n   \n")

    assert window.validate_actions() is False
    assert window._feedback_label.text()


def test_finish_saves_local_settings_and_completion_flag(qapp):
    from shield.ui.onboarding import OnboardingWindow

    saved: list[dict] = []
    window = OnboardingWindow(save_settings=saved.append)
    window._goal_edit.setPlainText("Daha sakin ve dürüst kalmak istiyorum.")
    window._actions_edit.setPlainText("Yürüyüş\n\nBir bardak su iç")
    window._email_edit.setText("partner@example.com")

    result = window.finish()

    assert result is True
    assert len(saved) == 1
    assert saved[0] == {
        "goal_text": "Daha sakin ve dürüst kalmak istiyorum.",
        "alternative_actions": ["Yürüyüş", "Bir bardak su iç"],
        "accountability_email": "partner@example.com",
        "onboarding_completed": True,
    }


def test_run_onboarding_owns_event_loop_when_no_qapplication(monkeypatch):
    from shield.ui import onboarding

    _FakeOnboardingWindow.instances.clear()

    fake_app = _FakeApplication(exec_result=12)
    fake_qapplication = _FakeQApplication(instance_value=None, created_app=fake_app)
    monkeypatch.setattr(onboarding, "QApplication", fake_qapplication)
    monkeypatch.setattr(onboarding, "OnboardingWindow", _FakeOnboardingWindow)

    result = onboarding.run_onboarding(db_path=":memory:")

    assert result == 12
    assert fake_qapplication.created is True
    assert fake_app.exec_called is True
    assert _FakeOnboardingWindow.instances[0].shown is True
    assert onboarding._active_onboarding_window is None


def test_run_onboarding_returns_without_exec_when_qapplication_exists(monkeypatch):
    from shield.ui import onboarding

    _FakeOnboardingWindow.instances.clear()

    existing_app = _FakeApplication(exec_result=99)
    fake_qapplication = _FakeQApplication(instance_value=existing_app, created_app=None)
    monkeypatch.setattr(onboarding, "QApplication", fake_qapplication)
    monkeypatch.setattr(onboarding, "OnboardingWindow", _FakeOnboardingWindow)

    result = onboarding.run_onboarding(db_path=":memory:")

    assert result == 0
    assert fake_qapplication.created is False
    assert existing_app.exec_called is False
    assert _FakeOnboardingWindow.instances[0].shown is True
    assert onboarding._active_onboarding_window is _FakeOnboardingWindow.instances[0]


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


class _FakeOnboardingWindow:
    instances: list = []

    def __init__(self, save_settings=None) -> None:
        self.save_settings = save_settings
        self.destroyed = _FakeSignal()
        self.shown = False
        self.raised = False
        self.activated = False
        _FakeOnboardingWindow.instances.append(self)

    def show(self) -> None:
        self.shown = True

    def raise_(self) -> None:
        self.raised = True

    def activateWindow(self) -> None:
        self.activated = True
