from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

from PyQt6.QtWidgets import QApplication

from ui.blur_overlay import BlurOverlayWindow
from ui.dashboard import DashboardWindow
from ui.morning_checkin import MorningCheckinWindow
from ui.onboarding import OnboardingWindow
from ui.settings import SettingsWindow

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:  # pragma: no cover - runtime integration only
    import core  # type: ignore
except Exception:  # pragma: no cover - standalone fallback

    class _CoreFallback:
        def get_goals(self) -> list[str]:
            return []

        def get_checkin_history(self) -> list[dict]:
            return []

    core = _CoreFallback()  # type: ignore


def _safe_call(name: str, default: Any) -> Any:
    fn = getattr(core, name, None)
    if not callable(fn):
        return default
    try:
        return fn()
    except Exception:
        return default


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
        candidates = [text, text.replace("Z", "+00:00")]
        if "T" in text and " " not in text:
            candidates.append(text.replace("T", " "))
        for candidate in candidates:
            try:
                return datetime.fromisoformat(candidate)
            except Exception:
                continue
    return None


def _extract_datetime(entry: dict[str, Any]) -> datetime | None:
    for key in (
        "created_at",
        "createdAt",
        "timestamp",
        "time",
        "datetime",
        "date",
        "created",
        "updated_at",
        "updatedAt",
    ):
        if key in entry:
            parsed = _parse_datetime(entry.get(key))
            if parsed is not None:
                return parsed
    return None


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
        return self.app.exec()

    def _set_window(self, window, fullscreen: bool = False) -> None:
        self._current_window = window
        if fullscreen:
            window.showFullScreen()
        else:
            window.show()
        window.raise_()
        window.activateWindow()

    def _start_auto_flow(self) -> None:
        if not self._did_onboarding and self._needs_onboarding():
            self._show_onboarding(quit_on_close=False)
            return
        if not self._did_morning_checkin and self._needs_morning_checkin():
            self._show_morning_checkin(quit_on_close=False)
            return
        self._show_dashboard(quit_on_close=True)

    def _needs_onboarding(self) -> bool:
        goals = _safe_call("get_goals", [])
        if isinstance(goals, list):
            return not any(str(goal).strip() for goal in goals)
        if isinstance(goals, str):
            return not goals.strip()
        return True

    def _needs_morning_checkin(self) -> bool:
        history = _safe_call("get_checkin_history", [])
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

    def _show_overlay(self) -> None:
        window = BlurOverlayWindow()
        window.finished.connect(self.app.quit)
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

    def _after_onboarding(self) -> None:
        self._did_onboarding = True
        self._start_auto_flow()

    def _after_morning_checkin(self) -> None:
        self._did_morning_checkin = True
        self._show_dashboard(quit_on_close=True)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Shield desktop UI entrypoint")
    parser.add_argument(
        "--screen",
        choices=(
            "auto",
            "overlay",
            "morning_checkin",
            "onboarding",
            "settings",
            "dashboard",
        ),
        default="auto",
        help="Launch a specific screen or run the default UI flow.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    app = ShieldApp(mode=args.screen)
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
