from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtWidgets import QApplication

# Ensure project root is on sys.path so `import core` resolves correctly
_ROOT_DIR = Path(__file__).resolve().parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

import core  # noqa: E402 — must follow sys.path setup
from shield.core.interfaces import FrictionEvent  # noqa: E402

from ui.blur_overlay import BlurOverlayWindow  # noqa: E402
from ui.dashboard import DashboardWindow  # noqa: E402
from ui.morning_checkin import MorningCheckinWindow  # noqa: E402
from ui.onboarding import OnboardingWindow  # noqa: E402
from ui.settings import SettingsWindow  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Thread-safe bridge: Orchestrator callback → Qt main thread
# ---------------------------------------------------------------------------

class _FrictionBridge(QObject):
    """Receives friction events on a background thread; emits a Qt signal
    that is delivered to the main thread via the event queue."""

    triggered = pyqtSignal()

    def on_event(self, event: FrictionEvent) -> None:  # called from EventLoop thread
        logger.info(
            "Friction event — score=%.3f session=%s",
            event.score.final_score,
            event.session_id,
        )
        self.triggered.emit()


# ---------------------------------------------------------------------------
# Helpers for UI flow decisions
# ---------------------------------------------------------------------------

def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, time.min)
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value))
        except Exception:
            return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        for candidate in (text, text.replace("Z", "+00:00")):
            try:
                return datetime.fromisoformat(candidate)
            except Exception:
                continue
    return None


def _extract_datetime(entry: dict[str, Any]) -> datetime | None:
    for key in ("created_at", "createdAt", "timestamp", "time",
                "datetime", "date", "created", "updated_at", "updatedAt"):
        if key in entry:
            parsed = _parse_datetime(entry.get(key))
            if parsed is not None:
                return parsed
    return None


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

class ShieldApp:
    def __init__(self, mode: str) -> None:
        self.mode = mode
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.app.setApplicationName("Shield")
        self.app.setOrganizationName("Shield")
        self.app.setQuitOnLastWindowClosed(False)

        self._current_window = None
        self._did_onboarding = False
        self._did_morning_checkin = False
        self._overlay_window: BlurOverlayWindow | None = None

        # Wire Orchestrator → UI
        self._bridge = _FrictionBridge()
        self._bridge.triggered.connect(
            self._show_overlay, Qt.ConnectionType.QueuedConnection
        )
        core.orchestrator.register_friction_callback(self._bridge.on_event)
        core.orchestrator.start()
        logger.info("Orchestrator started.")

    def run(self) -> int:
        if self.mode == "overlay":
            self._show_overlay()
        elif self.mode == "morning_checkin":
            self._show_morning_checkin(quit_on_close=True)
        elif self.mode == "onboarding":
            self._show_onboarding(quit_on_close=True)
        elif self.mode == "settings":
            self._show_settings(quit_on_close=True)
        elif self.mode == "dashboard":
            self._show_dashboard(quit_on_close=True)
        else:
            self._start_auto_flow()

        exit_code = self.app.exec()
        core.orchestrator.stop()
        logger.info("Orchestrator stopped.")
        return exit_code

    # ------------------------------------------------------------------
    # Window management
    # ------------------------------------------------------------------

    def _set_window(self, window, fullscreen: bool = False) -> None:
        self._current_window = window
        if fullscreen:
            window.showFullScreen()
        else:
            window.show()
        window.raise_()
        window.activateWindow()

    # ------------------------------------------------------------------
    # Auto flow
    # ------------------------------------------------------------------

    def _start_auto_flow(self) -> None:
        if not self._did_onboarding and self._needs_onboarding():
            self._show_onboarding(quit_on_close=False)
            return
        if not self._did_morning_checkin and self._needs_morning_checkin():
            self._show_morning_checkin(quit_on_close=False)
            return
        self._show_dashboard(quit_on_close=True)

    def _needs_onboarding(self) -> bool:
        goals = core.get_goals()
        return not any(str(g).strip() for g in goals)

    def _needs_morning_checkin(self) -> bool:
        history = core.get_checkin_history()
        if not isinstance(history, list):
            return True
        today = date.today()
        for item in history:
            if not isinstance(item, dict):
                continue
            when = _extract_datetime(item)
            if when is not None and when.date() == today:
                return False
        return True

    # ------------------------------------------------------------------
    # Screen factories
    # ------------------------------------------------------------------

    def _show_overlay(self) -> None:
        if self._overlay_window is not None and self._overlay_window.isVisible():
            return  # already showing
        window = BlurOverlayWindow()
        self._overlay_window = window
        window.finished.connect(lambda: setattr(self, "_overlay_window", None))
        self._set_window(window, fullscreen=True)

    def _show_onboarding(self, quit_on_close: bool) -> None:
        window = OnboardingWindow()
        if quit_on_close:
            window.destroyed.connect(lambda *_: self.app.quit())
        else:
            window.destroyed.connect(lambda *_: self._after_onboarding())
        self._set_window(window, fullscreen=True)

    def _show_morning_checkin(self, quit_on_close: bool) -> None:
        window = MorningCheckinWindow()
        if quit_on_close:
            window.destroyed.connect(lambda *_: self.app.quit())
        else:
            window.destroyed.connect(lambda *_: self._after_morning_checkin())
        self._set_window(window, fullscreen=True)

    def _show_settings(self, quit_on_close: bool) -> None:
        window = SettingsWindow()
        if quit_on_close:
            window.destroyed.connect(lambda *_: self.app.quit())
        self._set_window(window, fullscreen=True)

    def _show_dashboard(self, quit_on_close: bool) -> None:
        window = DashboardWindow()
        if quit_on_close:
            window.destroyed.connect(lambda *_: self.app.quit())
        self._set_window(window, fullscreen=False)

    # ------------------------------------------------------------------
    # Flow transitions
    # ------------------------------------------------------------------

    def _after_onboarding(self) -> None:
        self._did_onboarding = True
        self._start_auto_flow()

    def _after_morning_checkin(self) -> None:
        self._did_morning_checkin = True
        self._show_dashboard(quit_on_close=True)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Shield desktop UI")
    parser.add_argument(
        "--screen",
        choices=("auto", "overlay", "morning_checkin", "onboarding", "settings", "dashboard"),
        default="auto",
        help="Launch a specific screen or run the automatic flow.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    app = ShieldApp(mode=args.screen)
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
