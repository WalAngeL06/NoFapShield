from __future__ import annotations

from collections.abc import Callable
from datetime import date

from PyQt6.QtCore import QEvent, Qt, QTimer
from PyQt6.QtGui import QCloseEvent, QFont, QKeyEvent
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from shield.core import Config
from shield.db import EventStore

MIN_CHECKIN_CHARS = 40
QUESTIONS = (
    "Bugün bu saatte burada olmak istediğini söyleyebilir misin?",
    "Şu an içinde hissettiklerini bir cümleyle tarif et.",
    "Yarın sabah bugünü nasıl hatırlamak istersin?",
    "Bu eylem seni hedeflerine yaklaştırıyor mu, uzaklaştırıyor mu?",
    "Gerçekten istediğin şey bu mu?",
)

_active_checkin_window: MorningCheckinWindow | None = None


def question_for_date(date_obj: date) -> str:
    return QUESTIONS[date_obj.toordinal() % len(QUESTIONS)]


def run_checkin(db_path: str | None = None, today: date | None = None) -> int:
    """Launch check-in as CLI owner or attach it to an existing Qt app."""
    global _active_checkin_window

    app = QApplication.instance()
    owns_event_loop = app is None
    if app is None:
        app = QApplication([])

    path = db_path if db_path is not None else Config().db_path
    store = EventStore(path)
    window = MorningCheckinWindow(
        save_checkin=store.save_checkin,
        today=today,
        on_destroy=store.close,
    )
    _active_checkin_window = window
    window.destroyed.connect(lambda *_: _release_active_checkin(window))
    window.showFullScreen()
    window.raise_()
    window.activateWindow()
    if not owns_event_loop:
        return 0

    exit_code = int(app.exec())
    _release_active_checkin(window)
    store.close()
    return exit_code


def _release_active_checkin(window: MorningCheckinWindow) -> None:
    global _active_checkin_window
    if _active_checkin_window is window:
        _active_checkin_window = None


class MorningCheckinWindow(QWidget):
    def __init__(
        self,
        save_checkin: Callable[[str], None] | None = None,
        today: date | None = None,
        streak_count: int = 0,
        on_destroy: Callable[[], None] | None = None,
    ) -> None:
        super().__init__()
        self.save_checkin = save_checkin or (lambda text: None)
        self.question = question_for_date(today or date.today())
        self.allow_close = False
        self._on_destroy = on_destroy

        self.setWindowTitle("Shield Check-in")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setStyleSheet("background: #0a0a0a; color: #f8fafc;")
        self.destroyed.connect(self._handle_destroyed)

        self._build_ui(streak_count)
        self.update_character_counter()

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

    def non_whitespace_count(self) -> int:
        return sum(1 for char in self._text_edit.toPlainText() if not char.isspace())

    def update_character_counter(self) -> None:
        count = self.non_whitespace_count()
        if count < MIN_CHECKIN_CHARS:
            self._counter_label.setText(f"{MIN_CHECKIN_CHARS - count} karakter daha")
            self._counter_label.setStyleSheet("color: #94a3b8; background: transparent;")
            return
        self._counter_label.setText("✓")
        self._counter_label.setStyleSheet("color: #86efac; background: transparent;")

    def invalid_submit_feedback(self) -> None:
        self._feedback_label.setText("Biraz daha yazabilirsin. Kısa bir cümle yeterli.")
        self._feedback_label.setStyleSheet("color: #fbbf24; background: transparent;")

    def submit(self) -> bool:
        if self.non_whitespace_count() < MIN_CHECKIN_CHARS:
            self.invalid_submit_feedback()
            return False

        self.save_checkin(self._text_edit.toPlainText())
        self.request_internal_close()
        return True

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

    def _build_ui(self, streak_count: int) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(72, 48, 72, 64)
        root.setSpacing(20)

        top_row = QHBoxLayout()
        top_row.addStretch(1)
        streak = QLabel(f"Streak: {streak_count}")
        streak.setFont(_font(14, QFont.Weight.DemiBold))
        streak.setStyleSheet("color: #94a3b8; background: transparent;")
        top_row.addWidget(streak)
        root.addLayout(top_row)
        root.addStretch(1)

        title = QLabel("Sabah kontrolü")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(_font(34, QFont.Weight.DemiBold))
        title.setStyleSheet("color: #f8fafc; background: transparent;")
        root.addWidget(title)

        question = QLabel(self.question)
        question.setAlignment(Qt.AlignmentFlag.AlignCenter)
        question.setWordWrap(True)
        question.setFont(_font(22, QFont.Weight.DemiBold))
        question.setStyleSheet("color: #cbd5e1; background: transparent;")
        root.addWidget(question)

        self._text_edit = QTextEdit()
        self._text_edit.setMinimumHeight(180)
        self._text_edit.setMaximumWidth(760)
        self._text_edit.setFont(_font(15))
        self._text_edit.setPlaceholderText("Kendine kısa ve dürüst bir not yaz.")
        self._text_edit.setStyleSheet(
            """
            QTextEdit {
                background: #111827;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #f8fafc;
                padding: 16px;
            }
            QTextEdit:focus { border-color: #60a5fa; }
            """
        )
        self._text_edit.textChanged.connect(self.update_character_counter)
        root.addWidget(self._text_edit, alignment=Qt.AlignmentFlag.AlignHCenter)

        lower_row = QHBoxLayout()
        lower_row.addStretch(1)
        self._counter_label = QLabel()
        self._counter_label.setFont(_font(13, QFont.Weight.DemiBold))
        lower_row.addWidget(self._counter_label)
        lower_row.addSpacing(24)
        submit_button = QPushButton("Kaydet")
        submit_button.setFixedSize(160, 52)
        submit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        submit_button.setFont(_font(15, QFont.Weight.DemiBold))
        submit_button.setStyleSheet(
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
        submit_button.clicked.connect(self.submit)
        lower_row.addWidget(submit_button)
        lower_row.addStretch(1)
        root.addLayout(lower_row)

        self._feedback_label = QLabel("")
        self._feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._feedback_label.setFont(_font(13))
        self._feedback_label.setStyleSheet("color: #94a3b8; background: transparent;")
        root.addWidget(self._feedback_label)
        root.addStretch(2)

    def _handle_destroyed(self) -> None:
        if self._on_destroy is not None:
            self._on_destroy()
            self._on_destroy = None


def _font(size: int, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    font = QFont("Segoe UI", size)
    font.setWeight(weight)
    return font
