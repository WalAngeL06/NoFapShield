from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QElapsedTimer, QEvent, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QCloseEvent, QFont, QKeyEvent, QPainter, QPen
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

COUNTDOWN_SECONDS = 15
ACTIVITY_SECONDS = 120


@dataclass(frozen=True)
class ActionCard:
    title: str
    detail: str


ACTION_CARDS = (
    ActionCard("Nefes al", "15 sakin nefes"),
    ActionCard("Su ic", "Bir bardak su"),
    ActionCard("Kisa yuruyus", "2 dakika hareket"),
)

_active_overlay_window: BlurOverlayWindow | None = None


def run_overlay(countdown_seconds: int = COUNTDOWN_SECONDS) -> int:
    """Launch the overlay from the CLI or attach it to an existing Qt app.

    When no QApplication exists this function owns the event loop and returns
    its exit code. When a QApplication already exists it only shows the overlay,
    keeps it alive at module scope, and returns immediately.
    """
    global _active_overlay_window

    app = QApplication.instance()
    owns_event_loop = app is None
    if app is None:
        app = QApplication([])

    window = BlurOverlayWindow(countdown_seconds=countdown_seconds)
    _active_overlay_window = window
    window.destroyed.connect(lambda *_: _release_active_overlay(window))
    window.showFullScreen()
    window.raise_()
    window.activateWindow()
    if not owns_event_loop:
        return 0

    exit_code = int(app.exec())
    _release_active_overlay(window)
    return exit_code


def _release_active_overlay(window: BlurOverlayWindow) -> None:
    global _active_overlay_window
    if _active_overlay_window is window:
        _active_overlay_window = None


class BlurOverlayWindow(QWidget):
    def __init__(
        self,
        countdown_seconds: int = COUNTDOWN_SECONDS,
        activity_seconds: int = ACTIVITY_SECONDS,
    ) -> None:
        super().__init__()
        if countdown_seconds <= 0:
            raise ValueError("countdown_seconds must be positive")
        if activity_seconds <= 0:
            raise ValueError("activity_seconds must be positive")

        self.countdown_seconds = countdown_seconds
        self.activity_seconds = activity_seconds
        self.allow_close = False
        self._activity_remaining = activity_seconds

        self.setWindowTitle("Shield")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setStyleSheet("background: #0a0a0a; color: #f8fafc;")

        self._countdown = CountdownRing(seconds=countdown_seconds)
        self._choice_screen = ChoiceScreen(cards=ACTION_CARDS)
        self._activity_screen = ActivityScreen()
        self._activity_screen.set_remaining(activity_seconds)

        self._stack = QStackedLayout()
        self._stack.addWidget(self._countdown)
        self._stack.addWidget(self._choice_screen)
        self._stack.addWidget(self._activity_screen)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addLayout(self._stack)

        self._countdown.finished.connect(self._show_choices)
        self._choice_screen.close_requested.connect(self._close_from_inside)
        self._choice_screen.action_selected.connect(self._start_activity)

        self._activity_timer = QTimer(self)
        self._activity_timer.setInterval(1000)
        self._activity_timer.timeout.connect(self._tick_activity)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.can_close():
            event.accept()
            return
        event.ignore()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self.should_block_key(event.key(), event.modifiers()):
            event.ignore()
            return
        super().keyPressEvent(event)

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.WindowStateChange and self.isMinimized():
            QTimer.singleShot(0, self.showFullScreen)
            event.ignore()
            return
        super().changeEvent(event)

    def _show_choices(self) -> None:
        self._stack.setCurrentWidget(self._choice_screen)

    def _start_activity(self, card: ActionCard) -> None:
        self._activity_remaining = self.activity_seconds
        self._activity_screen.set_action(card)
        self._activity_screen.set_remaining(self._activity_remaining)
        self._stack.setCurrentWidget(self._activity_screen)
        self._activity_timer.start()

    def _tick_activity(self) -> None:
        self._activity_remaining -= 1
        self._activity_screen.set_remaining(max(0, self._activity_remaining))
        if self._activity_remaining <= 0:
            self._activity_timer.stop()
            self.request_internal_close()

    def can_close(self) -> bool:
        return self.allow_close

    def request_internal_close(self) -> None:
        self.allow_close = True
        if self.isVisible():
            self.close()

    def should_block_key(self, key: int, modifiers: Qt.KeyboardModifier | Qt.KeyboardModifiers) -> bool:
        if key == Qt.Key.Key_Escape:
            return True
        return key == Qt.Key.Key_F4 and bool(modifiers & Qt.KeyboardModifier.AltModifier)

    def _close_from_inside(self) -> None:
        self.request_internal_close()


class CountdownRing(QWidget):
    finished = pyqtSignal()

    def __init__(self, seconds: int) -> None:
        super().__init__()
        self.seconds = seconds
        self._clock = QElapsedTimer()
        self._clock.start()

        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

        self._finished_emitted = False
        self.setMinimumSize(640, 520)

    def paintEvent(self, event) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = self.rect()
        center = rect.center()
        radius = max(96, min(rect.width(), rect.height()) // 6)
        elapsed = self._clock.elapsed() / 1000
        remaining = max(0.0, self.seconds - elapsed)
        progress = remaining / self.seconds

        painter.fillRect(rect, QColor("#0a0a0a"))
        self._draw_center_text(painter, center.y() - radius - 90, "Dur ve nefes al", 34, QColor("#f8fafc"))
        self._draw_center_text(
            painter,
            center.y() - radius - 42,
            "Secenekler birazdan gorunecek.",
            18,
            QColor("#94a3b8"),
        )

        ring_rect = QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
        painter.setPen(QPen(QColor("#334155"), 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(ring_rect, 90 * 16, -360 * 16)
        painter.setPen(QPen(QColor("#60a5fa"), 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(ring_rect, 90 * 16, int(-360 * progress * 16))

        self._draw_center_text(painter, center.y() - 46, str(max(0, int(remaining + 0.999))), 64, QColor("#f8fafc"))

    def _tick(self) -> None:
        if self._clock.elapsed() >= self.seconds * 1000 and not self._finished_emitted:
            self._finished_emitted = True
            self._timer.stop()
            self.finished.emit()
        self.update()

    def _draw_center_text(self, painter: QPainter, y: int, text: str, size: int, color: QColor) -> None:
        painter.setPen(color)
        font = QFont("Segoe UI", size)
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.drawText(QRectF(0, y, self.width(), size + 18), Qt.AlignmentFlag.AlignCenter, text)


class ChoiceScreen(QWidget):
    close_requested = pyqtSignal()
    action_selected = pyqtSignal(object)

    def __init__(self, cards: tuple[ActionCard, ...]) -> None:
        super().__init__()
        self._cards = cards
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(48, 72, 48, 72)
        outer.setSpacing(28)
        outer.addStretch(1)

        title = QLabel("Simdi bir secim yap")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(_font(32, QFont.Weight.DemiBold))
        title.setStyleSheet("color: #f8fafc; background: transparent;")
        outer.addWidget(title)

        subtitle = QLabel("Siteyi kapatabilir veya kisa bir eylem secebilirsin.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(_font(16))
        subtitle.setStyleSheet("color: #94a3b8; background: transparent;")
        outer.addWidget(subtitle)

        close_button = QPushButton("Siteyi kapat")
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.setFixedSize(260, 58)
        close_button.setFont(_font(16, QFont.Weight.DemiBold))
        close_button.setStyleSheet(
            """
            QPushButton {
                background: #2563eb;
                border: 1px solid #60a5fa;
                border-radius: 8px;
                color: #ffffff;
            }
            QPushButton:hover { background: #1d4ed8; }
            QPushButton:pressed { background: #1e40af; }
            """
        )
        close_button.clicked.connect(self.close_requested.emit)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(close_button)
        button_row.addStretch(1)
        outer.addLayout(button_row)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(20)
        cards_row.addStretch(1)
        for card in self._cards:
            widget = ActionCardButton(card)
            widget.clicked.connect(lambda checked=False, selected=card: self.action_selected.emit(selected))
            cards_row.addWidget(widget)
        cards_row.addStretch(1)
        outer.addLayout(cards_row)

        outer.addStretch(2)


class ActionCardButton(QPushButton):
    def __init__(self, card: ActionCard) -> None:
        super().__init__()
        self.card = card
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(260, 150)
        self.setText(f"{card.title}\n{card.detail}")
        self.setFont(_font(16, QFont.Weight.DemiBold))
        self.setStyleSheet(
            """
            QPushButton {
                background: #111827;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #f8fafc;
                padding: 18px;
                text-align: left;
            }
            QPushButton:hover { border-color: #60a5fa; background: #172033; }
            QPushButton:pressed { background: #1f2937; }
            """
        )


class ActivityScreen(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 72, 48, 72)
        layout.addStretch(1)

        self._title = QLabel("Eyleme basla")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setFont(_font(32, QFont.Weight.DemiBold))
        self._title.setStyleSheet("color: #f8fafc; background: transparent;")
        layout.addWidget(self._title)

        self._detail = QLabel("")
        self._detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._detail.setFont(_font(17))
        self._detail.setStyleSheet("color: #94a3b8; background: transparent;")
        layout.addWidget(self._detail)

        self._timer = QLabel("")
        self._timer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._timer.setFont(_font(58, QFont.Weight.DemiBold))
        self._timer.setStyleSheet("color: #60a5fa; background: transparent;")
        layout.addWidget(self._timer)

        layout.addStretch(2)

    def set_action(self, card: ActionCard) -> None:
        self._detail.setText(card.detail)

    def set_remaining(self, seconds: int) -> None:
        minutes = seconds // 60
        rest = seconds % 60
        self._timer.setText(f"{minutes:02d}:{rest:02d}")


def _font(size: int, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    font = QFont("Segoe UI", size)
    font.setWeight(weight)
    return font
