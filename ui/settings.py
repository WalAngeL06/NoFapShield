from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Final

from PyQt6.QtCore import QEvent, Qt, QTimer
from PyQt6.QtGui import QFont, QKeyEvent
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSlider,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

APP_BG: Final[str] = "#0a0a0a"
SURFACE: Final[str] = "#111111"
SURFACE_2: Final[str] = "#171717"
BORDER: Final[str] = "#272727"
TEXT: Final[str] = "#ececec"
MUTED: Final[str] = "#a0a0a0"
SOFT: Final[str] = "#d9d9d9"
ACCENT: Final[str] = "#e6e6e6"
ERROR: Final[str] = "#d8b3b3"
SUCCESS: Final[str] = "#b8d8bf"

MIN_PASSWORD_CHARS: Final[int] = 6
MIN_GOAL_CHARS: Final[int] = 8
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

DEFAULT_SENSITIVITY: Final[int] = 65
SLIDER_MIN: Final[int] = 0
SLIDER_MAX: Final[int] = 100


_ROOT_DIR = Path(__file__).resolve().parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

try:  # pragma: no cover - runtime integration
    import core  # type: ignore
except Exception:  # pragma: no cover - standalone fallback

    class _CoreFallback:
        def get_goals(self) -> list[str]:
            return []

        def update_settings(self, key: str, value) -> None:
            return None

        def verify_password(self, pw: str) -> bool:
            return False

    core = _CoreFallback()  # type: ignore


class SettingsSection(QFrame):
    def __init__(self, title: str, subtitle: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Section")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(22, 20, 22, 20)
        self._layout.setSpacing(14)

        title_label = QLabel(title)
        title_label.setFont(self._font(20, QFont.Weight.DemiBold))

        subtitle_label = QLabel(subtitle)
        subtitle_label.setFont(self._font(12, QFont.Weight.Normal))
        subtitle_label.setWordWrap(True)
        subtitle_label.setStyleSheet(f"color: {MUTED};")

        self._layout.addWidget(title_label)
        self._layout.addWidget(subtitle_label)

    def body(self) -> QVBoxLayout:
        return self._layout

    @staticmethod
    def _font(size: int, weight: QFont.Weight) -> QFont:
        font = QFont("Segoe UI", size)
        font.setWeight(weight)
        return font


class SettingsWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._allow_close = False
        self._configure_window()
        self._build_ui()
        self._prefill_from_core()
        self._sync_sensitivity_label(self.sensitivity_slider.value())
        self._set_status(self.password_status, "Hazir.")
        self._set_status(self.email_status, "Hazir.")
        self._set_global_status("Degisiklikler burada yerel kalir.")

    def _configure_window(self) -> None:
        self.setWindowTitle("Shield - Settings")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
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
            QFrame#Section {{
                background: rgba(17, 17, 17, 0.95);
                border: 1px solid {BORDER};
                border-radius: 24px;
            }}
            QTextEdit, QLineEdit {{
                background: {SURFACE};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 16px;
                padding: 14px 15px;
                selection-background-color: #3b3b3b;
                selection-color: {TEXT};
                font-size: 15px;
            }}
            QTextEdit:focus, QLineEdit:focus {{
                background: {SURFACE_2};
                border: 1px solid #3a3a3a;
            }}
            QListWidget {{
                background: {SURFACE};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 16px;
                padding: 8px;
                outline: 0;
            }}
            QListWidget::item {{
                padding: 10px 12px;
                margin: 3px 4px;
                border-radius: 12px;
            }}
            QListWidget::item:selected {{
                background: rgba(255, 255, 255, 0.06);
            }}
            QSlider::groove:horizontal {{
                height: 8px;
                background: #222222;
                border-radius: 4px;
            }}
            QSlider::sub-page:horizontal {{
                background: #dcdcdc;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {ACCENT};
                border: 1px solid #f2f2f2;
                width: 20px;
                margin: -8px 0;
                border-radius: 10px;
            }}
            QPushButton#PrimaryButton {{
                background: {ACCENT};
                color: #0b0b0b;
                border: 1px solid {ACCENT};
                border-radius: 16px;
                padding: 13px 18px;
                font-size: 15px;
                font-weight: 700;
            }}
            QPushButton#PrimaryButton:hover {{
                background: #f5f5f5;
            }}
            QPushButton#PrimaryButton:pressed {{
                background: #d6d6d6;
            }}
            QPushButton#SecondaryButton {{
                background: rgba(255, 255, 255, 0.03);
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 16px;
                padding: 12px 16px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton#SecondaryButton:hover {{
                background: rgba(255, 255, 255, 0.06);
            }}
            QPushButton#SecondaryButton:disabled {{
                color: #6c6c6c;
                background: rgba(255, 255, 255, 0.02);
            }}
            """
        )

    def _build_ui(self) -> None:
        root = QWidget(self)
        root.setStyleSheet(f"background: {APP_BG};")
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(36, 28, 36, 28)
        outer.setSpacing(18)

        header = QHBoxLayout()
        header.setSpacing(14)

        title_col = QVBoxLayout()
        title_col.setSpacing(6)

        kicker = QLabel("Ayarlar")
        kicker.setFont(self._font(12, QFont.Weight.DemiBold))
        kicker.setStyleSheet(f"color: {MUTED}; letter-spacing: 0.8px;")

        title = QLabel("Shield ayarlarini sakin bir sekilde duzenle")
        title.setFont(self._font(28, QFont.Weight.DemiBold))
        title.setWordWrap(True)

        subtitle = QLabel(
            "Burada hedefini, alternatiflerini, sifreni, partner e-postani ve tespit hassasiyetini guncellersin."
        )
        subtitle.setFont(self._font(13, QFont.Weight.Normal))
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"color: {MUTED};")

        title_col.addWidget(kicker)
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header.addLayout(title_col, 1)

        self.global_status = QLabel("Degisiklikler burada yerel kalir.")
        self.global_status.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self.global_status.setFont(self._font(12, QFont.Weight.DemiBold))
        self.global_status.setStyleSheet(
            """
            QLabel {
                color: #dddddd;
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid #272727;
                border-radius: 16px;
                padding: 10px 14px;
            }
            """
        )
        header.addWidget(self.global_status, 0, Qt.AlignmentFlag.AlignTop)
        outer.addLayout(header)

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }
            """
        )

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        self.scroll.setWidget(content)

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        self.goal_section = self._build_goal_section()
        self.actions_section = self._build_actions_section()
        self.password_section = self._build_password_section()
        self.sensitivity_section = self._build_sensitivity_section()
        self.email_section = self._build_email_section()

        content_layout.addWidget(self.goal_section)
        content_layout.addWidget(self.actions_section)
        content_layout.addWidget(self.password_section)
        content_layout.addWidget(self.sensitivity_section)
        content_layout.addWidget(self.email_section)
        content_layout.addStretch(1)

        outer.addWidget(self.scroll, 1)

        footer = QLabel("ESC ve Alt+F4 kapali; pencere minimize edilse bile geri acilir.")
        footer.setFont(self._font(11, QFont.Weight.Normal))
        footer.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        footer.setStyleSheet(f"color: {MUTED};")
        outer.addWidget(footer)

        close_row = QHBoxLayout()
        close_row.addStretch(1)
        self.close_button = QPushButton("Ayarlari kapat")
        self.close_button.setObjectName("SecondaryButton")
        self.close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_button.clicked.connect(self._request_close)
        close_row.addWidget(self.close_button)
        outer.addLayout(close_row)

    def _build_goal_section(self) -> QFrame:
        section = SettingsSection(
            "Hedef metni",
            "Gunluk hedefini duzenle. Birden fazla satir girersen her satir ayri hedef olarak kaydedilir.",
            self,
        )
        card = section.body()

        self.goal_editor = QTextEdit()
        self.goal_editor.setPlaceholderText(
            "Ornek: Daha sakin kalmak, hedeflerime sadik olmak ve bugunu bilincli gecirmek."
        )
        self.goal_editor.setAcceptRichText(False)
        self.goal_editor.setTabChangesFocus(True)
        self.goal_editor.setMinimumHeight(160)
        card.addWidget(self.goal_editor)

        row = QHBoxLayout()
        row.setSpacing(12)
        self.goal_hint = QLabel("0 karakter")
        self.goal_hint.setFont(self._font(12, QFont.Weight.DemiBold))
        self.goal_hint.setStyleSheet(f"color: {MUTED};")
        row.addWidget(self.goal_hint, 1)

        self.goal_status = QLabel()
        self.goal_status.setFont(self._font(12, QFont.Weight.DemiBold))
        self.goal_status.setAlignment(Qt.AlignmentFlag.AlignRight)
        row.addWidget(self.goal_status, 0)
        card.addLayout(row)

        save_row = QHBoxLayout()
        save_row.addStretch(1)
        self.goal_save_button = QPushButton("Hedefi kaydet")
        self.goal_save_button.setObjectName("PrimaryButton")
        self.goal_save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.goal_save_button.clicked.connect(self._save_goals)
        save_row.addWidget(self.goal_save_button)
        card.addLayout(save_row)
        self.goal_editor.textChanged.connect(self._update_goal_feedback)

        return section

    def _build_actions_section(self) -> QFrame:
        section = SettingsSection(
            "Alternatif eylemler",
            "Durdurma aninda gorunecek alternatifleri buradan ekle, duzenle, sil ve sirala.",
            self,
        )
        card = section.body()

        self.actions_list = QListWidget()
        self.actions_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.actions_list.itemSelectionChanged.connect(self._sync_action_editor)
        card.addWidget(self.actions_list)

        editor_row = QHBoxLayout()
        editor_row.setSpacing(10)

        self.action_input = QLineEdit()
        self.action_input.setPlaceholderText("Yeni eylem ya da secili eylemin yeni metni")
        self.action_input.returnPressed.connect(self._add_or_update_action)
        editor_row.addWidget(self.action_input, 1)

        self.action_apply_button = QPushButton("Ekle / guncelle")
        self.action_apply_button.setObjectName("SecondaryButton")
        self.action_apply_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_apply_button.clicked.connect(self._add_or_update_action)
        editor_row.addWidget(self.action_apply_button, 0)
        card.addLayout(editor_row)

        controls = QHBoxLayout()
        controls.setSpacing(10)

        self.action_delete_button = QPushButton("Sil")
        self.action_delete_button.setObjectName("SecondaryButton")
        self.action_delete_button.clicked.connect(self._remove_selected_action)
        controls.addWidget(self.action_delete_button)

        self.action_up_button = QPushButton("Yukari")
        self.action_up_button.setObjectName("SecondaryButton")
        self.action_up_button.clicked.connect(lambda: self._move_selected_action(-1))
        controls.addWidget(self.action_up_button)

        self.action_down_button = QPushButton("Asagi")
        self.action_down_button.setObjectName("SecondaryButton")
        self.action_down_button.clicked.connect(lambda: self._move_selected_action(1))
        controls.addWidget(self.action_down_button)

        controls.addStretch(1)

        self.actions_save_button = QPushButton("Listeyi kaydet")
        self.actions_save_button.setObjectName("PrimaryButton")
        self.actions_save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.actions_save_button.clicked.connect(self._save_actions)
        controls.addWidget(self.actions_save_button)
        card.addLayout(controls)

        self.actions_status = QLabel()
        self.actions_status.setFont(self._font(12, QFont.Weight.DemiBold))
        self.actions_status.setStyleSheet(f"color: {MUTED};")
        card.addWidget(self.actions_status)

        return section

    def _build_password_section(self) -> QFrame:
        section = SettingsSection(
            "Sifre degistirme",
            "Mevcut sifreyi dogrula, sonra yeni sifreyi kaydet. UI tarafinda hashing yapilmaz.",
            self,
        )
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(12)

        self.current_password_input = QLineEdit()
        self.current_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.current_password_input.setPlaceholderText("Mevcut sifre")
        form.addRow("Mevcut sifre", self.current_password_input)

        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setPlaceholderText("Yeni sifre")
        form.addRow("Yeni sifre", self.new_password_input)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setPlaceholderText("Yeni sifre tekrar")
        form.addRow("Yeni sifre tekrar", self.confirm_password_input)

        section.body().addLayout(form)

        button_row = QHBoxLayout()
        button_row.addStretch(1)

        self.password_save_button = QPushButton("Sifreyi guncelle")
        self.password_save_button.setObjectName("PrimaryButton")
        self.password_save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.password_save_button.clicked.connect(self._save_password)
        button_row.addWidget(self.password_save_button)
        section.body().addLayout(button_row)

        self.password_status = QLabel()
        self.password_status.setFont(self._font(12, QFont.Weight.DemiBold))
        self.password_status.setStyleSheet(f"color: {MUTED};")
        section.body().addWidget(self.password_status)

        return section

    def _build_sensitivity_section(self) -> QFrame:
        section = SettingsSection(
            "Tespit hassasiyeti",
            "Slider yukari ciktikca daha sık tetiklenir. Deger degistiginde yerel ayara yazilir.",
            self,
        )
        card = section.body()

        row = QHBoxLayout()
        row.setSpacing(12)

        label_col = QVBoxLayout()
        label_col.setSpacing(6)

        self.sensitivity_value_label = QLabel()
        self.sensitivity_value_label.setFont(self._font(20, QFont.Weight.DemiBold))
        self.sensitivity_value_label.setStyleSheet(f"color: {SOFT};")
        label_col.addWidget(self.sensitivity_value_label)

        self.sensitivity_note = QLabel("0 = daha esnek, 100 = daha sik duraklama")
        self.sensitivity_note.setFont(self._font(12, QFont.Weight.Normal))
        self.sensitivity_note.setStyleSheet(f"color: {MUTED};")
        label_col.addWidget(self.sensitivity_note)

        row.addLayout(label_col, 0)

        self.sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self.sensitivity_slider.setRange(SLIDER_MIN, SLIDER_MAX)
        self.sensitivity_slider.setSingleStep(1)
        self.sensitivity_slider.setPageStep(5)
        self.sensitivity_slider.valueChanged.connect(self._sync_sensitivity_label)
        self.sensitivity_slider.sliderReleased.connect(self._save_sensitivity)
        row.addWidget(self.sensitivity_slider, 1)

        card.addLayout(row)

        self.sensitivity_status = QLabel()
        self.sensitivity_status.setFont(self._font(12, QFont.Weight.DemiBold))
        self.sensitivity_status.setStyleSheet(f"color: {MUTED};")
        card.addWidget(self.sensitivity_status)

        return section

    def _build_email_section(self) -> QFrame:
        section = SettingsSection(
            "Accountability partner e-postasi",
            "Opsiyonel. Uygun gorursen destek kisisi ici gorunce dogrudan iletilecek adresi buraya yaz.",
            self,
        )
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(12)

        self.partner_email_input = QLineEdit()
        self.partner_email_input.setPlaceholderText("ornek@domain.com")
        form.addRow("E-posta", self.partner_email_input)
        section.body().addLayout(form)

        button_row = QHBoxLayout()
        button_row.addStretch(1)

        self.email_save_button = QPushButton("E-postayi kaydet")
        self.email_save_button.setObjectName("PrimaryButton")
        self.email_save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.email_save_button.clicked.connect(self._save_email)
        button_row.addWidget(self.email_save_button)
        section.body().addLayout(button_row)

        self.email_status = QLabel()
        self.email_status.setFont(self._font(12, QFont.Weight.DemiBold))
        self.email_status.setStyleSheet(f"color: {MUTED};")
        section.body().addWidget(self.email_status)

        return section

    @staticmethod
    def _font(size: int, weight: QFont.Weight) -> QFont:
        font = QFont("Segoe UI", size)
        font.setWeight(weight)
        return font

    @staticmethod
    def _set_status(label: QLabel, message: str, error: bool = False) -> None:
        label.setText(message)
        label.setStyleSheet(f"color: {ERROR if error else SUCCESS if message == 'Kaydedildi.' else MUTED};")

    def _set_global_status(self, message: str, error: bool = False) -> None:
        self.global_status.setText(message)
        self.global_status.setStyleSheet(
            f"""
            QLabel {{
                color: {ERROR if error else SUCCESS if message.startswith('Kaydedildi') else '#dddddd'};
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid #272727;
                border-radius: 16px;
                padding: 10px 14px;
            }}
            """
        )

    def _prefill_from_core(self) -> None:
        goals = self._safe_goals()
        if goals:
            self.goal_editor.setPlainText("\n".join(goals))
        else:
            self.goal_editor.setPlainText("")
        self._update_goal_feedback()

        default_actions = [
            "Derin nefes al",
            "Kisa yuruyus yap",
            "Bir bardak su ic",
        ]
        for action in default_actions:
            self.actions_list.addItem(QListWidgetItem(action))
        self._sync_action_editor()

        self.sensitivity_slider.setValue(DEFAULT_SENSITIVITY)

    def _safe_goals(self) -> list[str]:
        try:
            goals = core.get_goals()
        except Exception:
            return []

        if isinstance(goals, list):
            return [str(goal).strip() for goal in goals if str(goal).strip()]
        if isinstance(goals, str):
            return [line.strip() for line in goals.splitlines() if line.strip()]
        return []

    def _goal_lines(self) -> list[str]:
        return [line.strip() for line in self.goal_editor.toPlainText().splitlines() if line.strip()]

    def _selected_action_row(self) -> int:
        item = self.actions_list.currentItem()
        if item is None:
            return -1
        return self.actions_list.row(item)

    def _selected_action_text(self) -> str:
        item = self.actions_list.currentItem()
        if item is None:
            return ""
        return item.text().strip()

    def _update_goal_feedback(self) -> None:
        chars = len(self.goal_editor.toPlainText().strip())
        self.goal_hint.setText(f"{chars} karakter")
        if chars >= MIN_GOAL_CHARS:
            self.goal_hint.setStyleSheet(f"color: {SUCCESS};")
            self._set_status(self.goal_status, "Hazir.")
        else:
            self.goal_hint.setStyleSheet(f"color: {MUTED};")
            remaining = max(0, MIN_GOAL_CHARS - chars)
            self.goal_status.setText(f"{remaining} karakter daha")
            self.goal_status.setStyleSheet(f"color: {MUTED};")

    def _sync_action_editor(self) -> None:
        text = self._selected_action_text()
        self.action_input.setText(text)
        self.action_delete_button.setEnabled(self._selected_action_row() >= 0)
        self.action_up_button.setEnabled(self._selected_action_row() > 0)
        self.action_down_button.setEnabled(
            0 <= self._selected_action_row() < self.actions_list.count() - 1
        )
        self._update_actions_summary()

    def _update_actions_summary(self) -> None:
        count = self.actions_list.count()
        if count == 0:
            self.actions_status.setText("Liste bos.")
            self.actions_status.setStyleSheet(f"color: {MUTED};")
            return
        self.actions_status.setText(f"{count} eylem hazir.")
        self.actions_status.setStyleSheet(f"color: {MUTED};")

    def _sync_sensitivity_label(self, value: int) -> None:
        self.sensitivity_value_label.setText(f"{value}")
        self.sensitivity_status.setText("Deger ayarlandi; kaydetmek icin slideri birak.")
        self.sensitivity_status.setStyleSheet(f"color: {MUTED};")

    def _save_setting(self, key: str, value, label: QLabel, success_text: str) -> bool:
        try:
            core.update_settings(key, value)
        except Exception as exc:  # pragma: no cover - runtime safeguard
            self._set_status(label, f"Kaydedilemedi: {exc}", error=True)
            self._set_global_status("Bir ayar kaydedilemedi.", error=True)
            return False
        self._set_status(label, success_text)
        self._set_global_status(success_text)
        return True

    def _save_goals(self) -> None:
        goals = self._goal_lines()
        if not goals:
            self._set_status(self.goal_status, "En az bir hedef yaz.", error=True)
            self.goal_editor.setFocus()
            return

        if not self._save_setting("goals", goals, self.goal_status, "Kaydedildi."):
            return
        self._update_goal_feedback()

    def _add_or_update_action(self) -> None:
        text = self.action_input.text().strip()
        if not text:
            self._set_status(self.actions_status, "Bir eylem metni yaz.", error=True)
            self.action_input.setFocus()
            return

        row = self._selected_action_row()
        if row >= 0:
            self.actions_list.item(row).setText(text)
            self._set_status(self.actions_status, "Secili eylem guncellendi.")
        else:
            self.actions_list.addItem(QListWidgetItem(text))
            self._set_status(self.actions_status, "Eylem eklendi.")

        self.action_input.clear()
        self._sync_action_editor()

    def _remove_selected_action(self) -> None:
        row = self._selected_action_row()
        if row < 0:
            self._set_status(self.actions_status, "Silinecek eylem sec.", error=True)
            return

        self.actions_list.takeItem(row)
        self.action_input.clear()
        self._set_status(self.actions_status, "Eylem silindi.")
        self._sync_action_editor()

    def _move_selected_action(self, direction: int) -> None:
        row = self._selected_action_row()
        if row < 0:
            return

        new_row = row + direction
        if new_row < 0 or new_row >= self.actions_list.count():
            return

        item = self.actions_list.takeItem(row)
        if item is None:
            return
        self.actions_list.insertItem(new_row, item)
        self.actions_list.setCurrentRow(new_row)
        self._sync_action_editor()

    def _save_actions(self) -> None:
        actions = [
            self.actions_list.item(index).text().strip()
            for index in range(self.actions_list.count())
            if self.actions_list.item(index) is not None
            and self.actions_list.item(index).text().strip()
        ]
        if not actions:
            self._set_status(self.actions_status, "En az bir alternatif gir.", error=True)
            return

        self._save_setting("alternative_actions", actions, self.actions_status, "Kaydedildi.")

    def _save_password(self) -> None:
        current_password = self.current_password_input.text().strip()
        new_password = self.new_password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()

        if not current_password:
            self._set_status(self.password_status, "Mevcut sifreyi yaz.", error=True)
            self.current_password_input.setFocus()
            return
        if not new_password:
            self._set_status(self.password_status, "Yeni sifre bos olamaz.", error=True)
            self.new_password_input.setFocus()
            return
        if len(new_password) < MIN_PASSWORD_CHARS:
            self._set_status(
                self.password_status,
                f"Yeni sifre en az {MIN_PASSWORD_CHARS} karakter olmali.",
                error=True,
            )
            self.new_password_input.setFocus()
            return
        if new_password != confirm_password:
            self._set_status(self.password_status, "Yeni sifreler eslesmiyor.", error=True)
            self.confirm_password_input.setFocus()
            return

        try:
            verified = bool(core.verify_password(current_password))
        except Exception as exc:  # pragma: no cover - runtime safeguard
            self._set_status(self.password_status, f"Dogrulama hatasi: {exc}", error=True)
            return

        if not verified:
            self._set_status(self.password_status, "Mevcut sifre hatali.", error=True)
            self.current_password_input.setFocus()
            return

        if not self._save_setting("password", new_password, self.password_status, "Kaydedildi."):
            return

        self.current_password_input.clear()
        self.new_password_input.clear()
        self.confirm_password_input.clear()

    def _save_sensitivity(self) -> None:
        value = int(self.sensitivity_slider.value())
        if not self._save_setting(
            "detection_sensitivity",
            value,
            self.sensitivity_status,
            "Kaydedildi.",
        ):
            return
        self.sensitivity_status.setText(f"Kaydedildi: {value}")

    def _save_email(self) -> None:
        email = self.partner_email_input.text().strip()
        if email and not EMAIL_RE.match(email):
            self._set_status(self.email_status, "E-posta formati gecersiz.", error=True)
            self.partner_email_input.setFocus()
            return

        if not self._save_setting("partner_email", email, self.email_status, "Kaydedildi."):
            return

    def _request_close(self) -> None:
        self._allow_close = True
        self.close()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.raise_()
        self.activateWindow()
        self.setFocus()
        if not self.isFullScreen():
            self.showFullScreen()
        QTimer.singleShot(0, self.goal_editor.setFocus)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            event.ignore()
            return
        if event.key() == Qt.Key.Key_F4 and event.modifiers() & Qt.KeyboardModifier.AltModifier:
            event.ignore()
            return
        if event.key() in (Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            event.ignore()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event) -> None:  # noqa: N802
        if self._allow_close:
            event.accept()
            return
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


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Shield")
    app.setOrganizationName("Shield")
    app.setQuitOnLastWindowClosed(False)

    window = SettingsWindow()
    window.showFullScreen()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
