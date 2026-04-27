import os
from datetime import date, datetime, timezone

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


# ---------------------------------------------------------------------------
# Import smoke
# ---------------------------------------------------------------------------


def test_dashboard_import_smoke():
    from shield.ui import dashboard

    assert hasattr(dashboard, "DashboardWindow")
    assert hasattr(dashboard, "run_dashboard")
    assert hasattr(dashboard, "_active_dashboard_window")


# ---------------------------------------------------------------------------
# Instantiation / empty state
# ---------------------------------------------------------------------------


def test_dashboard_window_instantiates_offscreen(qapp):
    from shield.ui.dashboard import DashboardWindow

    window = DashboardWindow()
    assert window is not None


def test_dashboard_empty_state_labels(qapp):
    from shield.ui.dashboard import DashboardWindow

    window = DashboardWindow()

    assert window._total_checkins_label.text() == "0"
    assert window._total_triggers_label.text() == "0"
    assert window._today_status_label.text() == "—"


# ---------------------------------------------------------------------------
# With injected data
# ---------------------------------------------------------------------------


def test_dashboard_total_checkins_with_data(qapp):
    from shield.ui.dashboard import DashboardWindow

    checkins = [
        {"created_at": "2026-04-27T10:00:00+00:00", "text": "Bugün iyiyim."},
        {"created_at": "2026-04-26T09:00:00+00:00", "text": "Sakin bir gün."},
    ]
    window = DashboardWindow(get_checkins=lambda: checkins)

    assert window._total_checkins_label.text() == "2"


def test_dashboard_total_triggers_with_data(qapp):
    from shield.ui.dashboard import DashboardWindow

    triggers = [
        {
            "session_id": "abc",
            "triggered_at": "2026-04-27T08:00:00+00:00",
            "source": "demo",
            "score": 1.0,
            "threshold": 0.7,
            "reason": "manual demo trigger",
        },
    ]
    window = DashboardWindow(get_triggers=lambda: triggers)

    assert window._total_triggers_label.text() == "1"


def test_dashboard_today_status_when_checkin_done_today(qapp):
    from shield.ui.dashboard import DashboardWindow

    today_iso = datetime.now(timezone.utc).isoformat()
    checkins = [{"created_at": today_iso, "text": "Bugün iyiyim."}]
    window = DashboardWindow(get_checkins=lambda: checkins)

    assert "✓" in window._today_status_label.text()


def test_dashboard_today_status_no_checkin_when_only_old_entry(qapp):
    from shield.ui.dashboard import DashboardWindow

    old_checkins = [{"created_at": "2020-01-01T10:00:00+00:00", "text": "Eski kayıt."}]
    window = DashboardWindow(get_checkins=lambda: old_checkins)

    assert window._today_status_label.text() == "—"


def test_dashboard_checkin_history_shows_items(qapp):
    from shield.ui.dashboard import DashboardWindow

    checkins = [
        {"created_at": "2026-04-27T10:00:00+00:00", "text": "Bugün sakin."},
    ]
    window = DashboardWindow(get_checkins=lambda: checkins)

    assert window._checkin_list.count() == 1


def test_dashboard_trigger_log_shows_items(qapp):
    from shield.ui.dashboard import DashboardWindow

    triggers = [
        {
            "session_id": "x1",
            "triggered_at": "2026-04-27T08:00:00+00:00",
            "source": "demo",
            "score": 1.0,
            "threshold": 0.7,
            "reason": "manual demo trigger",
        },
        {
            "session_id": "x2",
            "triggered_at": "2026-04-26T08:00:00+00:00",
            "source": "demo",
            "score": 1.0,
            "threshold": 0.7,
            "reason": "manual demo trigger",
        },
    ]
    window = DashboardWindow(get_triggers=lambda: triggers)

    assert window._trigger_list.count() == 2


def test_dashboard_checkin_history_empty_state(qapp):
    from shield.ui.dashboard import DashboardWindow

    window = DashboardWindow(get_checkins=lambda: [])

    assert window._checkin_list.count() == 1
    assert "kayıt yok" in window._checkin_list.item(0).text().lower()


def test_dashboard_trigger_log_empty_state(qapp):
    from shield.ui.dashboard import DashboardWindow

    window = DashboardWindow(get_triggers=lambda: [])

    assert window._trigger_list.count() == 1
    assert "kayıt yok" in window._trigger_list.item(0).text().lower()


# ---------------------------------------------------------------------------
# run_dashboard event loop ownership
# ---------------------------------------------------------------------------


def test_run_dashboard_owns_event_loop_when_no_qapplication(monkeypatch):
    from shield.ui import dashboard

    _FakeDashboardWindow.instances.clear()

    fake_app = _FakeApplication(exec_result=7)
    fake_qapplication = _FakeQApplication(instance_value=None, created_app=fake_app)
    monkeypatch.setattr(dashboard, "QApplication", fake_qapplication)
    monkeypatch.setattr(dashboard, "DashboardWindow", _FakeDashboardWindow)

    result = dashboard.run_dashboard(db_path=":memory:")

    assert result == 7
    assert fake_qapplication.created is True
    assert fake_app.exec_called is True
    assert _FakeDashboardWindow.instances[0].shown is True
    assert dashboard._active_dashboard_window is None


def test_run_dashboard_returns_without_exec_when_qapplication_exists(monkeypatch):
    from shield.ui import dashboard

    _FakeDashboardWindow.instances.clear()

    existing_app = _FakeApplication(exec_result=99)
    fake_qapplication = _FakeQApplication(instance_value=existing_app, created_app=None)
    monkeypatch.setattr(dashboard, "QApplication", fake_qapplication)
    monkeypatch.setattr(dashboard, "DashboardWindow", _FakeDashboardWindow)

    result = dashboard.run_dashboard(db_path=":memory:")

    assert result == 0
    assert fake_qapplication.created is False
    assert existing_app.exec_called is False
    assert _FakeDashboardWindow.instances[0].shown is True
    assert dashboard._active_dashboard_window is _FakeDashboardWindow.instances[0]


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


class _FakeDashboardWindow:
    instances: list = []

    def __init__(self, get_checkins=None, get_triggers=None) -> None:
        self.get_checkins = get_checkins
        self.get_triggers = get_triggers
        self.destroyed = _FakeSignal()
        self.shown = False
        self.raised = False
        self.activated = False
        _FakeDashboardWindow.instances.append(self)

    def show(self) -> None:
        self.shown = True

    def raise_(self) -> None:
        self.raised = True

    def activateWindow(self) -> None:
        self.activated = True
