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
    QScrollArea,
    QSlider,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from shield.core import Config
from shield.db import EventStore

SETTING_KEYS = (
    "goal_text",
    "alternative_actions",
    "accountability_email",
    "detection_sensitivity",
)
DEFAULT_SENSITIVITY = 0.7

_active_settings_window: SettingsWindow | None = None


def run_settings(db_path: str | None = None) -> int:
    """Launch settings as CLI owner or attach it to an existing Qt app."""
    global _active_settings_window

    app = QApplication.instance()
    owns_event_loop = app is None
    if app is None:
        app = QApplication([])

    path = db_path if db_path is not None else Config().db_path
    store = EventStore(path)

    def save_all(values: dict[str, Any]) -> None:
        for key, value in values.items():
            store.set_setting(key, value)

    window = SettingsWindow(
        get_settings=store.list_settings,
        save_settings=save_all,
    )
    _active_settings_window = window
    window.destroyed.connect(lambda *_: _release_active_settings(window))
    window.destroyed.connect(lambda *_: store.close())
    window.show()
    window.raise_()
    window.activateWindow()
    if not owns_event_loop:
        return 0

    exit_code = int(app.exec())
    _release_active_settings(window)
    return exit_code


def _release_active_settings(window: SettingsWindow) -> None:
    global _active_settings_window
    if _active_settings_window is window:
        _active_settings_window = None


class SettingsWindow(QWidget):
    def __init__(
        self,
        get_settings: Callable[[], dict[str, Any]] | None = None,
        save_settings: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        super().__init__()
        self._get_settings = get_settings or (lambda: {})
        self._save_settings = save_settings or (lambda values: None)

        self.setWindowTitle("Shield Ayarlar")
        self.setMinimumSize(720, 640)
        self.resize(880, 720)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setStyleSheet("background: #0a0a0a; color: #f8fafc;")

        self._build_ui()
        self._load_values(self._get_settings())

    def submit(self) -> bool:
        values = self._collect_values()
        self._save_settings(values)
        self._feedback_label.setText("✓ Kaydedildi")
        self._feedback_label.setStyleSheet("color: #86efac; background: transparent;")
        return True

    def _collect_values(self) -> dict[str, Any]:
        return {
            "goal_text": self._goal_edit.toPlainText().strip(),
            "alternative_actions": _parse_actions(self._actions_edit.toPlainText()),
            "accountability_email": self._email_edit.text().strip(),
            "detection_sensitivity": self._sensitivity_slider.value() / 100,
        }

    def _load_values(self, values: dict[str, Any]) -> None:
        self._goal_edit.setPlainText(str(values.get("goal_text", "") or ""))
        actions = values.get("alternative_actions") or []
        if isinstance(actions, list):
            self._actions_edit.setPlainText("\n".join(str(a) for a in actions))
        self._email_edit.setText(str(values.get("accountability_email", "") or ""))
        sensitivity = values.get("detection_sensitivity", DEFAULT_SENSITIVITY)
        try:
            slider_value = int(round(float(sensitivity) * 100))
        except (TypeError, ValueError):
            slider_value = int(DEFAULT_SENSITIVITY * 100)
        self._sensitivity_slider.setValue(max(0, min(100, slider_value)))

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #0a0a0a; border: none; }")
        root.addWidget(scroll)

        content = QWidget()
        content.setStyleSheet("background: #0a0a0a;")
        scroll.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(48, 40, 48, 48)
        layout.setSpacing(28)

        layout.addLayout(self._build_header())
        layout.addWidget(self._build_goal_card())
        layout.addWidget(self._build_actions_card())
        layout.addWidget(self._build_email_card())
        layout.addWidget(self._build_sensitivity_card())
        layout.addLayout(self._build_save_row())
        layout.addStretch(1)

    def _build_header(self) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(6)

        title = QLabel("Ayarlar")
        title.setFont(_font(28, QFont.Weight.Bold))
        title.setStyleSheet("color: #f8fafc; background: transparent;")
        col.addWidget(title)

        subtitle = QLabel("Yerel kişisel yapılandırma. Cihazından çıkmaz.")
        subtitle.setFont(_font(14))
        subtitle.setStyleSheet("color: #94a3b8; background: transparent;")
        col.addWidget(subtitle)

        return col

    def _build_goal_card(self) -> QFrame:
        card = _make_card()
        col = _card_layout(card)

        col.addWidget(_section_label("Kişisel hedef"))
        col.addWidget(_helper_label(
            "Bu ekranı açtığında neyi hatırlamak istersin?"
        ))

        self._goal_edit = QTextEdit()
        self._goal_edit.setMinimumHeight(96)
        self._goal_edit.setFont(_font(14))
        self._goal_edit.setPlaceholderText(
            "Örnek: Sakin ve dürüst bir alışkanlık kurmak istiyorum."
        )
        self._goal_edit.setStyleSheet(_text_edit_style())
        col.addWidget(self._goal_edit)
        return card

    def _build_actions_card(self) -> QFrame:
        card = _make_card()
        col = _card_layout(card)

        col.addWidget(_section_label("Alternatif eylemler"))
        col.addWidget(_helper_label(
            "Her satıra bir kısa eylem yaz. Pause ekranı bunlardan ilham alacak."
        ))

        self._actions_edit = QTextEdit()
        self._actions_edit.setMinimumHeight(120)
        self._actions_edit.setFont(_font(14))
        self._actions_edit.setPlaceholderText(
            "Örnek:\nİki dakika yürüyüş\nBir bardak su iç\nKısa nefes egzersizi"
        )
        self._actions_edit.setStyleSheet(_text_edit_style())
        col.addWidget(self._actions_edit)
        return card

    def _build_email_card(self) -> QFrame:
        card = _make_card()
        col = _card_layout(card)

        col.addWidget(_section_label("Hesap verme adresi (opsiyonel)"))

        self._email_edit = QLineEdit()
        self._email_edit.setFont(_font(14))
        self._email_edit.setPlaceholderText("partner@ornek.com")
        self._email_edit.setStyleSheet(_line_edit_style())
        col.addWidget(self._email_edit)

        self._email_helper = _helper_label(
            "Yerel placeholder. v0.1 sürümünde gönderim yapılmaz."
        )
        col.addWidget(self._email_helper)
        return card

    def _build_sensitivity_card(self) -> QFrame:
        card = _make_card()
        col = _card_layout(card)

        col.addWidget(_section_label("Algılama hassasiyeti"))

        slider_row = QHBoxLayout()
        slider_row.setSpacing(12)

        self._sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self._sensitivity_slider.setRange(0, 100)
        self._sensitivity_slider.setValue(int(DEFAULT_SENSITIVITY * 100))
        self._sensitivity_slider.setStyleSheet(_slider_style())
        slider_row.addWidget(self._sensitivity_slider, 1)

        self._sensitivity_value = QLabel(
            f"{int(DEFAULT_SENSITIVITY * 100)}%"
        )
        self._sensitivity_value.setFont(_font(13, QFont.Weight.DemiBold))
        self._sensitivity_value.setStyleSheet("color: #cbd5e1; background: transparent;")
        self._sensitivity_value.setFixedWidth(48)
        slider_row.addWidget(self._sensitivity_value)
        col.addLayout(slider_row)

        self._sensitivity_slider.valueChanged.connect(
            lambda v: self._sensitivity_value.setText(f"{v}%")
        )

        self._sensitivity_helper = _helper_label(
            "v0.1 sürümünde aktif değil. Tercihin ileri sürümlerde kullanılacak."
        )
        col.addWidget(self._sensitivity_helper)
        return card

    def _build_save_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(16)

        self._feedback_label = QLabel("")
        self._feedback_label.setFont(_font(13))
        self._feedback_label.setStyleSheet("color: #94a3b8; background: transparent;")
        row.addWidget(self._feedback_label)
        row.addStretch(1)

        self._save_button = QPushButton("Kaydet")
        self._save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._save_button.setFixedSize(160, 44)
        self._save_button.setFont(_font(14, QFont.Weight.DemiBold))
        self._save_button.setStyleSheet(
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
        self._save_button.clicked.connect(self.submit)
        row.addWidget(self._save_button)
        return row


def _parse_actions(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _make_card() -> QFrame:
    card = QFrame()
    card.setFrameShape(QFrame.Shape.NoFrame)
    card.setStyleSheet(
        "QFrame { background: #111827; border: 1px solid #1e293b; border-radius: 10px; }"
    )
    return card


def _card_layout(card: QFrame) -> QVBoxLayout:
    col = QVBoxLayout(card)
    col.setContentsMargins(20, 18, 20, 18)
    col.setSpacing(10)
    return col


def _section_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setFont(_font(15, QFont.Weight.DemiBold))
    label.setStyleSheet("color: #e2e8f0; background: transparent; border: none;")
    return label


def _helper_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setFont(_font(12))
    label.setWordWrap(True)
    label.setStyleSheet("color: #64748b; background: transparent; border: none;")
    return label


def _text_edit_style() -> str:
    return """
    QTextEdit {
        background: #0a0a0a;
        border: 1px solid #334155;
        border-radius: 8px;
        color: #f8fafc;
        padding: 10px;
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
        padding: 8px 10px;
    }
    QLineEdit:focus { border-color: #60a5fa; }
    """


def _slider_style() -> str:
    return """
    QSlider::groove:horizontal {
        height: 4px;
        background: #1e293b;
        border-radius: 2px;
    }
    QSlider::sub-page:horizontal {
        background: #60a5fa;
        border-radius: 2px;
    }
    QSlider::handle:horizontal {
        background: #f8fafc;
        width: 14px;
        margin: -6px 0;
        border-radius: 7px;
    }
    """


def _font(size: int, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    font = QFont("Segoe UI", size)
    font.setWeight(weight)
    return font
