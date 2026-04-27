from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedLayout,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from shield.core import Config
from shield.db import EventStore

MIN_GOAL_CHARS = 10
DEFAULT_ACTIONS = (
    "2 dakika yürüyüş",
    "Bir bardak su iç",
    "Kısa nefes egzersizi",
)

_active_onboarding_window: OnboardingWindow | None = None


def run_onboarding(db_path: str | None = None) -> int:
    """Launch onboarding as CLI owner or attach it to an existing Qt app."""
    global _active_onboarding_window

    app = QApplication.instance()
    owns_event_loop = app is None
    if app is None:
        app = QApplication([])

    path = db_path if db_path is not None else Config().db_path
    store = EventStore(path)

    def save_all(values: dict[str, Any]) -> None:
        for key, value in values.items():
            store.set_setting(key, value)

    window = OnboardingWindow(save_settings=save_all)
    _active_onboarding_window = window
    window.destroyed.connect(lambda *_: _release_active_onboarding(window))
    window.destroyed.connect(lambda *_: store.close())
    window.show()
    window.raise_()
    window.activateWindow()
    if not owns_event_loop:
        return 0

    exit_code = int(app.exec())
    _release_active_onboarding(window)
    return exit_code


def _release_active_onboarding(window: OnboardingWindow) -> None:
    global _active_onboarding_window
    if _active_onboarding_window is window:
        _active_onboarding_window = None


class OnboardingWindow(QWidget):
    def __init__(
        self,
        save_settings: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        super().__init__()
        self._save_settings = save_settings or (lambda values: None)
        self._current_step = 0
        self._completed = False

        self.setWindowTitle("Shield Onboarding")
        self.setMinimumSize(760, 560)
        self.resize(860, 640)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setStyleSheet("background: #0a0a0a; color: #f8fafc;")

        self._build_ui()

    def current_step(self) -> int:
        return self._current_step

    def collected_values(self) -> dict[str, Any]:
        return {
            "goal_text": self._goal_edit.toPlainText().strip(),
            "alternative_actions": self.alternative_actions(),
            "accountability_email": self._email_edit.text().strip(),
            "onboarding_completed": True,
        }

    def alternative_actions(self) -> list[str]:
        return [line.strip() for line in self._actions_edit.toPlainText().splitlines() if line.strip()]

    def validate_goal(self) -> bool:
        count = sum(1 for char in self._goal_edit.toPlainText() if not char.isspace())
        if count < MIN_GOAL_CHARS:
            self._set_feedback("Kendine biraz daha net bir cümle bırakabilirsin.")
            return False
        self._clear_feedback()
        return True

    def validate_actions(self) -> bool:
        if not self.alternative_actions():
            self._set_feedback("En az bir kısa alternatif eylem ekleyebilirsin.")
            return False
        self._clear_feedback()
        return True

    def next_step(self) -> bool:
        if self._current_step == 0 and not self.validate_goal():
            return False
        if self._current_step == 1 and not self.validate_actions():
            return False
        if self._current_step >= 2:
            return self.finish()

        self._current_step += 1
        self._stack.setCurrentIndex(self._current_step)
        self._sync_buttons()
        self._clear_feedback()
        return True

    def previous_step(self) -> None:
        if self._current_step == 0:
            return
        self._current_step -= 1
        self._stack.setCurrentIndex(self._current_step)
        self._sync_buttons()
        self._clear_feedback()

    def finish(self) -> bool:
        if not self.validate_goal() or not self.validate_actions():
            return False
        self._save_settings(self.collected_values())
        self._completed = True
        self._set_feedback("✓ Hazır. Ayarların yerel olarak kaydedildi.", success=True)
        if self.isVisible():
            self.close()
        return True

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(42, 34, 42, 34)
        root.setSpacing(18)

        header = QLabel("Shield kurulumu")
        header.setFont(_font(28, QFont.Weight.Bold))
        header.setStyleSheet("color: #f8fafc; background: transparent;")
        root.addWidget(header)

        subtitle = QLabel("Sakin bir başlangıç. Bilgiler yalnızca yerel olarak saklanır.")
        subtitle.setFont(_font(14))
        subtitle.setStyleSheet("color: #94a3b8; background: transparent;")
        root.addWidget(subtitle)

        self._stack = QStackedLayout()
        self._stack.addWidget(self._build_goal_step())
        self._stack.addWidget(self._build_actions_step())
        self._stack.addWidget(self._build_email_step())
        root.addLayout(self._stack, 1)

        self._feedback_label = QLabel("")
        self._feedback_label.setFont(_font(13))
        self._feedback_label.setStyleSheet("color: #94a3b8; background: transparent;")
        root.addWidget(self._feedback_label)

        root.addLayout(self._build_nav())
        self._sync_buttons()

    def _build_goal_step(self) -> QFrame:
        card = _make_card()
        col = _card_layout(card)
        col.addWidget(_step_label("1 / 3"))
        col.addWidget(_title_label("Bunu neden yapıyorsun?"))
        col.addWidget(_helper_label("Kendine hatırlatmak istediğin nedeni kısa ve dürüstçe yaz."))

        self._goal_edit = QTextEdit()
        self._goal_edit.setMinimumHeight(160)
        self._goal_edit.setFont(_font(14))
        self._goal_edit.setPlaceholderText("Örnek: Daha sakin ve dürüst bir gün geçirmek istiyorum.")
        self._goal_edit.setStyleSheet(_text_edit_style())
        col.addWidget(self._goal_edit)
        return card

    def _build_actions_step(self) -> QFrame:
        card = _make_card()
        col = _card_layout(card)
        col.addWidget(_step_label("2 / 3"))
        col.addWidget(_title_label("Alternatif eylemler"))
        col.addWidget(_helper_label("Zor bir anda deneyebileceğin kısa eylemleri düzenle."))

        self._actions_edit = QTextEdit()
        self._actions_edit.setMinimumHeight(170)
        self._actions_edit.setFont(_font(14))
        self._actions_edit.setPlainText("\n".join(DEFAULT_ACTIONS))
        self._actions_edit.setStyleSheet(_text_edit_style())
        col.addWidget(self._actions_edit)
        return card

    def _build_email_step(self) -> QFrame:
        card = _make_card()
        col = _card_layout(card)
        col.addWidget(_step_label("3 / 3"))
        col.addWidget(_title_label("Opsiyonel hesap verme adresi"))
        col.addWidget(_helper_label(
            "Bu alan şimdilik yalnızca yerel bir nottur. v0.1 sürümünde e-posta gönderilmez."
        ))

        self._email_edit = QLineEdit()
        self._email_edit.setFont(_font(14))
        self._email_edit.setPlaceholderText("partner@ornek.com")
        self._email_edit.setStyleSheet(_line_edit_style())
        col.addWidget(self._email_edit)
        return card

    def _build_nav(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addStretch(1)

        self._back_button = QPushButton("Geri")
        self._back_button.setFixedSize(120, 44)
        self._back_button.setFont(_font(13, QFont.Weight.DemiBold))
        self._back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_button.setStyleSheet(_secondary_button_style())
        self._back_button.clicked.connect(self.previous_step)
        row.addWidget(self._back_button)

        self._next_button = QPushButton("İleri")
        self._next_button.setFixedSize(140, 44)
        self._next_button.setFont(_font(13, QFont.Weight.DemiBold))
        self._next_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._next_button.setStyleSheet(_primary_button_style())
        self._next_button.clicked.connect(self.next_step)
        row.addWidget(self._next_button)
        return row

    def _sync_buttons(self) -> None:
        self._back_button.setEnabled(self._current_step > 0)
        self._next_button.setText("Kaydet" if self._current_step == 2 else "İleri")

    def _set_feedback(self, text: str, success: bool = False) -> None:
        color = "#86efac" if success else "#fbbf24"
        self._feedback_label.setText(text)
        self._feedback_label.setStyleSheet(f"color: {color}; background: transparent;")

    def _clear_feedback(self) -> None:
        self._feedback_label.setText("")
        self._feedback_label.setStyleSheet("color: #94a3b8; background: transparent;")


def _make_card() -> QFrame:
    card = QFrame()
    card.setFrameShape(QFrame.Shape.NoFrame)
    card.setStyleSheet(
        "QFrame { background: #111827; border: 1px solid #1e293b; border-radius: 10px; }"
    )
    return card


def _card_layout(card: QFrame) -> QVBoxLayout:
    col = QVBoxLayout(card)
    col.setContentsMargins(24, 22, 24, 24)
    col.setSpacing(12)
    return col


def _step_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setFont(_font(12, QFont.Weight.DemiBold))
    label.setStyleSheet("color: #60a5fa; background: transparent; border: none;")
    return label


def _title_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setFont(_font(22, QFont.Weight.Bold))
    label.setStyleSheet("color: #f8fafc; background: transparent; border: none;")
    return label


def _helper_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setFont(_font(13))
    label.setWordWrap(True)
    label.setStyleSheet("color: #94a3b8; background: transparent; border: none;")
    return label


def _text_edit_style() -> str:
    return """
    QTextEdit {
        background: #0a0a0a;
        border: 1px solid #334155;
        border-radius: 8px;
        color: #f8fafc;
        padding: 12px;
    }
    QTextEdit:focus { border-color: #60a5fa; }
    """


def _line_edit_style() -> str:
    return """
    QLineEdit {
        background: #0a0a0a;
        border: 1px solid #334155;
        border-radius: 8px;
        color: #f8fafc;
        padding: 10px 12px;
    }
    QLineEdit:focus { border-color: #60a5fa; }
    """


def _primary_button_style() -> str:
    return """
    QPushButton {
        background: #2563eb;
        border: 1px solid #60a5fa;
        border-radius: 8px;
        color: #ffffff;
    }
    QPushButton:hover { background: #1d4ed8; }
    QPushButton:pressed { background: #1e40af; }
    """


def _secondary_button_style() -> str:
    return """
    QPushButton {
        background: #111827;
        border: 1px solid #334155;
        border-radius: 8px;
        color: #cbd5e1;
    }
    QPushButton:disabled { color: #475569; border-color: #1e293b; }
    QPushButton:hover:!disabled { border-color: #60a5fa; }
    """


def _font(size: int, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    font = QFont("Segoe UI", size)
    font.setWeight(weight)
    return font
