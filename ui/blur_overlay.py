from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QElapsedTimer, QEvent, QPoint, QRect, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QFont, QKeyEvent, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsBlurEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

APP_BG = "#0a0a0a"
BORDER = "#252525"
TEXT = "#ececec"
MUTED = "#a0a0a0"

COUNTDOWN_SECONDS = 15
ACTIVITY_SECONDS = 120

ALTERNATIVE_ACTIONS = (
    ("Derin nefes al", "30 saniye boyunca sadece nefesine odaklan."),
    ("Kisa yuruyus", "Kendini baska bir odaya ya da pencereye tasi."),
    ("Bir not yaz", "Ne hissettigini uc kisa cumleyle kaydet."),
)


_ROOT_DIR = Path(__file__).resolve().parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

try:
    import core  # type: ignore
except Exception:  # pragma: no cover - optional integration only
    core = None


def _safe_goals() -> list[str]:
    if core is None:
        return []
    try:
        goals = core.get_goals()
        if isinstance(goals, list):
            return [str(goal) for goal in goals if str(goal).strip()]
    except Exception:
        pass
    return []


class RoundedPanel(QFrame):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("RoundedPanel")


class ActionCard(QPushButton):
    def __init__(self, title: str, subtitle: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumHeight(94)
        self.setText(f"{title}\n{subtitle}")
        self.setStyleSheet(
            """
            QPushButton {
                text-align: left;
                border: 1px solid #2c2c2c;
                border-radius: 18px;
                padding: 18px 18px 16px 18px;
                color: #ededed;
                background: rgba(18, 18, 18, 0.92);
                font-size: 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                border-color: #454545;
                background: rgba(24, 24, 24, 0.96);
            }
            QPushButton:pressed {
                background: rgba(32, 32, 32, 0.98);
            }
            """
        )


class CountdownRing(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._progress = 0.0
        self._seconds_left = COUNTDOWN_SECONDS
        self._headline = "Bir duraklama ani"
        self._subline = "Secenekler birazdan gorunur."
        self.setMinimumSize(320, 320)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def set_state(self, seconds_left: float, duration: float, headline: str, subline: str) -> None:
        duration = max(0.001, duration)
        self._progress = max(0.0, min(1.0, 1.0 - (seconds_left / duration)))
        self._seconds_left = max(0, math.ceil(seconds_left))
        self._headline = headline
        self._subline = subline
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        side = min(self.width(), self.height())
        cx = self.width() / 2.0
        cy = self.height() / 2.0
        radius = side * 0.33

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

        glow_pen = QPen(QColor(255, 255, 255, 22), 26, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(glow_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPoint(int(cx), int(cy)), int(radius), int(radius))

        track_pen = QPen(QColor("#242424"), 14, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.drawArc(QRect(int(cx - radius), int(cy - radius), int(radius * 2), int(radius * 2)), 0, 360 * 16)

        progress_pen = QPen(QColor("#dedede"), 14, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(progress_pen)
        painter.drawArc(
            QRect(int(cx - radius), int(cy - radius), int(radius * 2), int(radius * 2)),
            90 * 16,
            int(-360 * self._progress * 16),
        )

        inner_path = QPainterPath()
        inner_path.addEllipse(QPoint(int(cx), int(cy)), int(radius * 0.73), int(radius * 0.73))
        painter.fillPath(inner_path, QColor("#101010"))

        painter.setPen(QColor(TEXT))
        headline_font = QFont("Segoe UI", 13)
        headline_font.setWeight(QFont.Weight.Medium)
        painter.setFont(headline_font)
        painter.drawText(
            QRect(0, int(cy - 66), self.width(), 24),
            int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter),
            self._headline,
        )

        seconds_font = QFont("Segoe UI", 48)
        seconds_font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(seconds_font)
        painter.drawText(
            QRect(0, int(cy - 26), self.width(), 62),
            int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter),
            str(self._seconds_left),
        )

        painter.setFont(QFont("Segoe UI", 11))
        painter.setPen(QColor(MUTED))
        painter.drawText(
            QRect(24, int(cy + 38), self.width() - 48, 42),
            int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap),
            self._subline,
        )


class OverlayRoot(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        self.bg_label.setStyleSheet("background: #0a0a0a;")

        self.tint = QWidget(self)
        self.tint.setStyleSheet("background: rgba(10, 10, 10, 190);")

        self.content = QWidget(self)
        self.content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.content.setStyleSheet("background: transparent;")

    def resizeEvent(self, event) -> None:  # noqa: N802
        self.bg_label.setGeometry(self.rect())
        self.tint.setGeometry(self.rect())
        self.content.setGeometry(self.rect())
        super().resizeEvent(event)


class BlurOverlayWindow(QMainWindow):
    siteCloseRequested = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Shield")
        self._allow_close = False
        self._countdown_running = False
        self._activity_running = False
        self._state = "countdown"
        self._countdown_start = QElapsedTimer()
        self._activity_start = QElapsedTimer()
        self._background_capture = QPixmap()
        self._screen = None
        self._goals = _safe_goals()

        self._configure_window()
        self._build_ui()
        self._bind_timers()

    def _configure_window(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet(
            f"""
            QMainWindow, QWidget {{
                background: {APP_BG};
                color: {TEXT};
            }}
            QLabel {{
                color: {TEXT};
            }}
            QPushButton#primaryButton {{
                background: #f0f0f0;
                color: #0b0b0b;
                border: 1px solid #f0f0f0;
                border-radius: 18px;
                padding: 16px 18px;
                font-size: 17px;
                font-weight: 700;
            }}
            QPushButton#primaryButton:hover {{
                background: #ffffff;
            }}
            QPushButton#primaryButton:pressed {{
                background: #d9d9d9;
            }}
            """
        )

    def _build_ui(self) -> None:
        self.root = OverlayRoot(self)
        self.setCentralWidget(self.root)

        self.stack = QStackedWidget(self.root.content)
        self.stack.setStyleSheet("background: transparent;")

        self.countdown_page = self._build_countdown_page()
        self.choice_page = self._build_choice_page()
        self.activity_page = self._build_activity_page()

        self.stack.addWidget(self.countdown_page)
        self.stack.addWidget(self.choice_page)
        self.stack.addWidget(self.activity_page)
        self.stack.setCurrentWidget(self.countdown_page)

        outer = QVBoxLayout(self.root.content)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self.stack)

    def _build_countdown_page(self) -> QWidget:
        page = QWidget()
        page.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        page.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(page)
        layout.setContentsMargins(60, 54, 60, 54)
        layout.setSpacing(18)

        header = QLabel("Bir duraklama ani")
        header.setFont(self._font(28, QFont.Weight.DemiBold))
        header.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        sub = QLabel("Ekran kisa bir sure icin yumusatiliyor. Sonra secenekler gorunecek.")
        sub.setFont(self._font(13, QFont.Weight.Normal))
        sub.setWordWrap(True)
        sub.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        sub.setStyleSheet(f"color: {MUTED};")

        layout.addStretch(1)
        layout.addWidget(header)
        layout.addWidget(sub)
        layout.addSpacing(8)

        ring_row = QHBoxLayout()
        ring_row.setContentsMargins(0, 0, 0, 0)
        ring_row.addStretch(1)
        self.countdown_ring = CountdownRing()
        ring_row.addWidget(self.countdown_ring)
        ring_row.addStretch(1)
        layout.addLayout(ring_row)
        layout.addStretch(1)

        footer = QLabel("Kisa bir bekleme, sonra tarafsiz secenekler.")
        footer.setFont(self._font(12, QFont.Weight.Normal))
        footer.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        footer.setStyleSheet(f"color: {MUTED};")
        layout.addWidget(footer)

        return page

    def _build_choice_page(self) -> QWidget:
        page = QWidget()
        page.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        page.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(page)
        layout.setContentsMargins(60, 52, 60, 48)
        layout.setSpacing(16)

        header = QLabel("Bir sonraki adimi sec")
        header.setFont(self._font(28, QFont.Weight.DemiBold))
        header.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        sub = QLabel("Burada amac yargilamak degil, bir sonraki 2 dakikayi kolaylastirmak.")
        sub.setFont(self._font(13, QFont.Weight.Normal))
        sub.setWordWrap(True)
        sub.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        sub.setStyleSheet(f"color: {MUTED};")

        layout.addStretch(1)
        layout.addWidget(header)
        layout.addWidget(sub)

        if self._goals:
            goals_panel = RoundedPanel()
            goals_panel.setStyleSheet(
                f"""
                RoundedPanel {{
                    background: rgba(18, 18, 18, 0.88);
                    border: 1px solid {BORDER};
                    border-radius: 20px;
                }}
                """
            )
            goals_layout = QVBoxLayout(goals_panel)
            goals_layout.setContentsMargins(20, 18, 20, 18)
            goals_layout.setSpacing(8)

            goals_title = QLabel("Hedeflerin")
            goals_title.setFont(self._font(12, QFont.Weight.DemiBold))
            goals_title.setStyleSheet(f"color: {MUTED};")
            goals_layout.addWidget(goals_title)
            for goal in self._goals[:3]:
                goal_label = QLabel(f"- {goal}")
                goal_label.setFont(self._font(14, QFont.Weight.Normal))
                goal_label.setWordWrap(True)
                goals_layout.addWidget(goal_label)
            layout.addWidget(goals_panel)

        primary_button = QPushButton("Siteyi kapat")
        primary_button.setObjectName("primaryButton")
        primary_button.setCursor(Qt.CursorShape.PointingHandCursor)
        primary_button.setMinimumHeight(58)
        primary_button.clicked.connect(self._site_close_clicked)
        layout.addWidget(primary_button)

        card_grid = QGridLayout()
        card_grid.setHorizontalSpacing(14)
        card_grid.setVerticalSpacing(14)
        self.choice_cards: list[ActionCard] = []
        for index, (title, subtitle) in enumerate(ALTERNATIVE_ACTIONS):
            card = ActionCard(title, subtitle)
            card.clicked.connect(lambda _checked=False, t=title: self._alternative_clicked(t))
            self.choice_cards.append(card)
            if index == 2:
                card_grid.addWidget(card, 1, 0, 1, 2)
            else:
                row, col = divmod(index, 2)
                card_grid.addWidget(card, row, col)

        layout.addLayout(card_grid)

        hint = QLabel("Seceneklerden biri secildiginde 2 dakikalik odak ekrani acilir.")
        hint.setFont(self._font(11, QFont.Weight.Normal))
        hint.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        hint.setStyleSheet(f"color: {MUTED};")
        layout.addWidget(hint)
        layout.addStretch(1)

        return page

    def _build_activity_page(self) -> QWidget:
        page = QWidget()
        page.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        page.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(page)
        layout.setContentsMargins(60, 52, 60, 48)
        layout.setSpacing(16)

        header = QLabel("Bu sureyi sadece buna ayir")
        header.setFont(self._font(28, QFont.Weight.DemiBold))
        header.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        sub = QLabel("Kisa bir odak arasi. Sure dolunca pencere kendiliginden kapanacak.")
        sub.setFont(self._font(13, QFont.Weight.Normal))
        sub.setWordWrap(True)
        sub.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        sub.setStyleSheet(f"color: {MUTED};")

        layout.addStretch(1)
        layout.addWidget(header)
        layout.addWidget(sub)
        layout.addSpacing(12)

        ring_row = QHBoxLayout()
        ring_row.addStretch(1)
        self.activity_ring = CountdownRing()
        ring_row.addWidget(self.activity_ring)
        ring_row.addStretch(1)
        layout.addLayout(ring_row)

        self.activity_detail = QLabel("2 dakika boyunca sadece sectigin eyleme odaklan.")
        self.activity_detail.setFont(self._font(12, QFont.Weight.Normal))
        self.activity_detail.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.activity_detail.setStyleSheet(f"color: {MUTED};")
        layout.addWidget(self.activity_detail)
        layout.addStretch(1)

        return page

    def _bind_timers(self) -> None:
        self.frame_timer = QTimer(self)
        self.frame_timer.setInterval(33)
        self.frame_timer.timeout.connect(self._tick)
        self.frame_timer.start()

    def _font(self, size: int, weight: QFont.Weight) -> QFont:
        font = QFont("Segoe UI", size)
        font.setWeight(weight)
        return font

    def capture_background(self) -> None:
        app = QApplication.instance()
        if app is None:
            return
        screen = app.screenAt(QCursor.pos()) or app.primaryScreen()
        if screen is None:
            return
        self._screen = screen
        try:
            self._background_capture = screen.grabWindow(0)
        except Exception:
            self._background_capture = QPixmap()

        if not self._background_capture.isNull():
            self.root.bg_label.setPixmap(self._background_capture)
            blur = QGraphicsBlurEffect(self.root.bg_label)
            blur.setBlurRadius(36.0)
            self.root.bg_label.setGraphicsEffect(blur)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.raise_()
        self.activateWindow()
        self.setFocus()

        if self._screen is not None:
            self.setGeometry(self._screen.geometry())
        if self._background_capture.isNull():
            QTimer.singleShot(0, self.capture_background)
        self._start_countdown()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self._screen is not None and self.isFullScreen():
            self.setGeometry(self._screen.geometry())

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            event.ignore()
            return
        if event.key() == Qt.Key.Key_F4 and event.modifiers() & Qt.KeyboardModifier.AltModifier:
            event.ignore()
            return
        if event.key() in (Qt.Key.Key_Meta, Qt.Key.Key_Alt):
            event.ignore()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event) -> None:  # noqa: N802
        if self._allow_close:
            event.accept()
            self.finished.emit()
        else:
            event.ignore()

    def changeEvent(self, event) -> None:  # noqa: N802
        if event.type() == QEvent.Type.WindowStateChange and self.isMinimized():
            QTimer.singleShot(0, self._restore_fullscreen)
        super().changeEvent(event)

    def _restore_fullscreen(self) -> None:
        if self._allow_close:
            return
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        self.setFocus()

    def _start_countdown(self) -> None:
        self._state = "countdown"
        self.stack.setCurrentWidget(self.countdown_page)
        self._countdown_start.restart()
        self._countdown_running = True
        self._activity_running = False
        self.countdown_ring.set_state(
            COUNTDOWN_SECONDS,
            COUNTDOWN_SECONDS,
            "Bir duraklama ani",
            "Secenekler birazdan gorunur.",
        )

    def _start_choice_screen(self) -> None:
        self._state = "choice"
        self.stack.setCurrentWidget(self.choice_page)

    def _start_activity(self, action_title: str) -> None:
        self._state = "activity"
        self.stack.setCurrentWidget(self.activity_page)
        self._activity_start.restart()
        self._activity_running = True
        self._countdown_running = False
        self.activity_detail.setText(f"Secilen eylem: {action_title}")
        self.activity_ring.set_state(
            ACTIVITY_SECONDS,
            ACTIVITY_SECONDS,
            "Odak arasi",
            "2 dakika tamamlanana kadar bu ekran acik kalacak.",
        )

    def _tick(self) -> None:
        if self._state == "countdown" and self._countdown_running:
            elapsed = self._countdown_start.elapsed() / 1000.0
            remaining = max(0.0, COUNTDOWN_SECONDS - elapsed)
            self.countdown_ring.set_state(
                remaining,
                COUNTDOWN_SECONDS,
                "Bir duraklama ani",
                "Secenekler birazdan gorunur.",
            )
            if remaining <= 0.0:
                self._countdown_running = False
                self._start_choice_screen()
            return

        if self._state == "activity" and self._activity_running:
            elapsed = self._activity_start.elapsed() / 1000.0
            remaining = max(0.0, ACTIVITY_SECONDS - elapsed)
            self.activity_ring.set_state(
                remaining,
                ACTIVITY_SECONDS,
                "Odak arasi",
                "2 dakika tamamlanana kadar bu ekran acik kalacak.",
            )
            if remaining <= 0.0:
                self._activity_running = False
                self._close_overlay()

    def _site_close_clicked(self) -> None:
        self.siteCloseRequested.emit()
        self._allow_close = True
        self.close()

    def _alternative_clicked(self, action_title: str) -> None:
        self._start_activity(action_title)

    def _close_overlay(self) -> None:
        self._allow_close = True
        self.close()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Shield")
    app.setOrganizationName("Shield")

    window = BlurOverlayWindow()
    window.capture_background()
    if window._screen is not None:
        window.setGeometry(window._screen.geometry())
    window.showFullScreen()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

