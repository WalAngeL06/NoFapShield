from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Final

from PyQt6.QtCore import QEasingCurve, QEvent, QPropertyAnimation, Qt, QTimer, pyqtProperty
from PyQt6.QtGui import QFont, QKeyEvent
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStyle,
    QStyleOptionButton,
    QStylePainter,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

APP_BG: Final[str] = "#0a0a0a"
SURFACE: Final[str] = "#111111"
SURFACE_2: Final[str] = "#171717"
SURFACE_3: Final[str] = "#1d1d1d"
BORDER: Final[str] = "#272727"
TEXT: Final[str] = "#ececec"
MUTED: Final[str] = "#a0a0a0"
SOFT: Final[str] = "#cfcfcf"
ACCENT: Final[str] = "#e7e7e7"
ERROR: Final[str] = "#c8b2b2"

STEP_TITLES: Final[tuple[str, ...]] = ("Hedef", "Alternatifler", "Girisi tamamla")
PRESET_ACTIONS: Final[tuple[str, ...]] = (
    "Derin nefes al",
    "Kisa yuruyus yap",
    "Baska bir odaya gec",
    "Birine mesaj at",
    "Kisa not yaz",
)

GOAL_MIN_CHARS: Final[int] = 8
PASSWORD_MIN_CHARS: Final[int] = 6

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


_ROOT_DIR = Path(__file__).resolve().parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

try:  # pragma: no cover - runtime integration only
    import core  # type: ignore
except Exception:  # pragma: no cover - local fallback for standalone runs

    class _CoreFallback:
        def update_settings(self, key: str, value) -> None:
            return None

    core = _CoreFallback()  # type: ignore


class ShakeButton(QPushButton):
    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self._shake_offset = 0.0
        self._shake_anim = QPropertyAnimation(self, b"shakeOffset", self)
        self._shake_anim.setDuration(320)
        self._shake_anim.setEasingCurve(QEasingCurve.Type.Linear)
        self._shake_anim.setKeyValueAt(0.0, 0.0)
        self._shake_anim.setKeyValueAt(0.12, -8.0)
        self._shake_anim.setKeyValueAt(0.24, 8.0)
        self._shake_anim.setKeyValueAt(0.36, -6.0)
        self._shake_anim.setKeyValueAt(0.48, 6.0)
        self._shake_anim.setKeyValueAt(0.60, -4.0)
        self._shake_anim.setKeyValueAt(0.72, 4.0)
        self._shake_anim.setKeyValueAt(0.84, -2.0)
        self._shake_anim.setKeyValueAt(1.0, 0.0)

    def shake(self) -> None:
        if self._shake_anim.state() == QPropertyAnimation.State.Running:
            self._shake_anim.stop()
        self._shake_anim.setStartValue(0.0)
        self._shake_anim.setEndValue(0.0)
        self._shake_anim.start()

    def getShakeOffset(self) -> float:
        return self._shake_offset

    def setShakeOffset(self, value: float) -> None:
        self._shake_offset = float(value)
        self.update()

    shakeOffset = pyqtProperty(float, fget=getShakeOffset, fset=setShakeOffset)

    def paintEvent(self, event) -> None:  # noqa: N802
        option = QStyleOptionButton()
        self.initStyleOption(option)
        painter = QStylePainter(self)
        painter.translate(self._shake_offset, 0.0)
        painter.drawControl(QStyle.ControlElement.CE_PushButton, option)


class OnboardingWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._allow_close = False
        self._current_step = 0
        self._goal_text = ""
        self._action_list: list[str] = []

        self._configure_window()
        self._build_ui()
        self._update_step_ui(0)
        self._feedback_for_step(0)

    def _configure_window(self) -> None:
        self.setWindowTitle("Shield")
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
            QFrame#Card {{
                background: rgba(17, 17, 17, 0.95);
                border: 1px solid {BORDER};
                border-radius: 26px;
            }}
            QLabel#StepChip {{
                color: #8f8f8f;
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid #262626;
                border-radius: 14px;
                padding: 8px 12px;
            }}
            QLabel#StepChipActive {{
                color: {TEXT};
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid #3a3a3a;
            }}
            QTextEdit, QLineEdit {{
                background: {SURFACE};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 18px;
                padding: 16px 16px;
                selection-background-color: #434343;
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
                border-radius: 18px;
                padding: 8px;
                outline: 0;
            }}
            QListWidget::item {{
                padding: 11px 12px;
                margin: 3px 4px;
                border-radius: 12px;
                color: {TEXT};
            }}
            QListWidget::item:selected {{
                background: rgba(255, 255, 255, 0.05);
            }}
            QPushButton#PrimaryButton {{
                background: {ACCENT};
                color: #0b0b0b;
                border: 1px solid {ACCENT};
                border-radius: 18px;
                padding: 15px 20px;
                font-size: 16px;
                font-weight: 700;
            }}
            QPushButton#PrimaryButton:hover {{
                background: #f6f6f6;
            }}
            QPushButton#PrimaryButton:pressed {{
                background: #d7d7d7;
            }}
            QPushButton#SecondaryButton {{
                background: rgba(255, 255, 255, 0.03);
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 18px;
                padding: 15px 20px;
                font-size: 15px;
                font-weight: 600;
            }}
            QPushButton#SecondaryButton:hover {{
                background: rgba(255, 255, 255, 0.06);
            }}
            QPushButton#SecondaryButton:disabled {{
                color: #666666;
                background: rgba(255, 255, 255, 0.02);
            }}
            """
        )

    def _build_ui(self) -> None:
        root = QWidget(self)
        root.setStyleSheet(
            f"""
            QWidget {{
                background: {APP_BG};
            }}
            """
        )
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(42, 36, 42, 34)
        outer.setSpacing(20)

        header = QHBoxLayout()
        header.setSpacing(16)

        title_col = QVBoxLayout()
        title_col.setSpacing(6)

        self.kicker = QLabel("Ilk kurulum")
        self.kicker.setFont(self._font(12, QFont.Weight.DemiBold))
        self.kicker.setStyleSheet(f"color: {MUTED}; letter-spacing: 0.8px;")

        self.title_label = QLabel("Shield ile baslarken")
        self.title_label.setFont(self._font(28, QFont.Weight.DemiBold))
        self.title_label.setWordWrap(True)

        self.subtitle_label = QLabel(
            "Bu sihirbaz niyetini, alternatiflerini ve giris bilgilerini sakin bir akista toplar."
        )
        self.subtitle_label.setFont(self._font(13, QFont.Weight.Normal))
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setStyleSheet(f"color: {MUTED};")

        title_col.addWidget(self.kicker)
        title_col.addWidget(self.title_label)
        title_col.addWidget(self.subtitle_label)
        header.addLayout(title_col, 1)

        indicator_col = QVBoxLayout()
        indicator_col.setSpacing(8)

        self.step_label = QLabel("Adim 1 / 3")
        self.step_label.setFont(self._font(13, QFont.Weight.DemiBold))
        self.step_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.step_label.setStyleSheet(f"color: {SOFT};")

        chip_row = QHBoxLayout()
        chip_row.setSpacing(8)
        self.step_chips: list[QLabel] = []
        for index in range(3):
            chip = QLabel(str(index + 1))
            chip.setObjectName("StepChip")
            chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chip.setMinimumWidth(34)
            chip.setFont(self._font(12, QFont.Weight.DemiBold))
            self.step_chips.append(chip)
            chip_row.addWidget(chip)

        indicator_col.addWidget(self.step_label)
        indicator_col.addLayout(chip_row)
        header.addLayout(indicator_col, 0)
        outer.addLayout(header)

        self.stack = QStackedWidget()
        self.stack.setObjectName("onboardingStack")
        self.stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.stack_effect = QGraphicsOpacityEffect(self.stack)
        self.stack.setGraphicsEffect(self.stack_effect)
        self.stack_effect.setOpacity(1.0)

        self.goal_page = self._build_goal_page()
        self.actions_page = self._build_actions_page()
        self.credentials_page = self._build_credentials_page()

        self.stack.addWidget(self.goal_page)
        self.stack.addWidget(self.actions_page)
        self.stack.addWidget(self.credentials_page)
        outer.addWidget(self.stack, 1)

        footer = QHBoxLayout()
        footer.setSpacing(14)

        self.feedback_label = QLabel("Hazir oldugunda ilerleyebiliriz.")
        self.feedback_label.setFont(self._font(12, QFont.Weight.Normal))
        self.feedback_label.setWordWrap(True)
        self.feedback_label.setStyleSheet(f"color: {MUTED};")
        footer.addWidget(self.feedback_label, 1)

        nav_row = QHBoxLayout()
        nav_row.setSpacing(10)

        self.back_button = QPushButton("Geri")
        self.back_button.setObjectName("SecondaryButton")
        self.back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_button.setMinimumHeight(52)
        self.back_button.clicked.connect(self._go_back)
        nav_row.addWidget(self.back_button)

        self.next_button = ShakeButton("Devam et")
        self.next_button.setObjectName("PrimaryButton")
        self.next_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_button.setMinimumHeight(52)
        self.next_button.clicked.connect(self._go_next)
        nav_row.addWidget(self.next_button)

        footer.addLayout(nav_row, 0)
        outer.addLayout(footer)

    def _build_goal_page(self) -> QWidget:
        page = QFrame()
        page.setObjectName("Card")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        heading = QLabel("1. Hedefini yaz")
        heading.setFont(self._font(24, QFont.Weight.DemiBold))

        sub = QLabel("Neden bunu yaptigini bir ya da iki cümlede anlat. Kisa ve net olmasi yeterli.")
        sub.setFont(self._font(13, QFont.Weight.Normal))
        sub.setWordWrap(True)
        sub.setStyleSheet(f"color: {MUTED};")

        layout.addWidget(heading)
        layout.addWidget(sub)

        self.goal_editor = QTextEdit()
        self.goal_editor.setPlaceholderText("Ornek: Daha sakin, daha bilincli ve hedeflerime sadik kalmak istiyorum.")
        self.goal_editor.setAcceptRichText(False)
        self.goal_editor.setTabChangesFocus(True)
        self.goal_editor.setMinimumHeight(240)
        self.goal_editor.textChanged.connect(self._refresh_current_state)
        layout.addWidget(self.goal_editor, 1)

        tip = QLabel("Bu alan dolmadan ilerleyemezsin.")
        tip.setFont(self._font(11, QFont.Weight.Normal))
        tip.setStyleSheet(f"color: {MUTED};")
        layout.addWidget(tip)

        return page

    def _build_actions_page(self) -> QWidget:
        page = QFrame()
        page.setObjectName("Card")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        heading = QLabel("2. Alternatif eylemlerini sec ve yaz")
        heading.setFont(self._font(24, QFont.Weight.DemiBold))

        sub = QLabel("En az bir hazir secenek sec veya kendi alternatiflerini alt alta ekle.")
        sub.setFont(self._font(13, QFont.Weight.Normal))
        sub.setWordWrap(True)
        sub.setStyleSheet(f"color: {MUTED};")

        layout.addWidget(heading)
        layout.addWidget(sub)

        self.actions_list = QListWidget()
        self.actions_list.setMinimumHeight(170)
        for action in PRESET_ACTIONS:
            item = QListWidgetItem(action)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.actions_list.addItem(item)
        self.actions_list.itemChanged.connect(self._refresh_current_state)
        layout.addWidget(self.actions_list)

        custom_label = QLabel("Kendi eylemlerin")
        custom_label.setFont(self._font(12, QFont.Weight.DemiBold))
        custom_label.setStyleSheet(f"color: {SOFT};")
        layout.addWidget(custom_label)

        self.custom_actions_editor = QTextEdit()
        self.custom_actions_editor.setPlaceholderText("Her satira bir alternatif yaz.")
        self.custom_actions_editor.setAcceptRichText(False)
        self.custom_actions_editor.setTabChangesFocus(True)
        self.custom_actions_editor.setMinimumHeight(132)
        self.custom_actions_editor.textChanged.connect(self._refresh_current_state)
        layout.addWidget(self.custom_actions_editor, 1)

        self.actions_summary = QLabel("Henüz secim yapilmadi.")
        self.actions_summary.setFont(self._font(11, QFont.Weight.Normal))
        self.actions_summary.setStyleSheet(f"color: {MUTED};")
        layout.addWidget(self.actions_summary)

        return page

    def _build_credentials_page(self) -> QWidget:
        page = QFrame()
        page.setObjectName("Card")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        heading = QLabel("3. Sifre ve destek kisisi")
        heading.setFont(self._font(24, QFont.Weight.DemiBold))

        sub = QLabel("Sifreni belirle. Istiyorsan bir destek kisisi e-postasi da ekleyebilirsin.")
        sub.setFont(self._font(13, QFont.Weight.Normal))
        sub.setWordWrap(True)
        sub.setStyleSheet(f"color: {MUTED};")

        layout.addWidget(heading)
        layout.addWidget(sub)

        password_label = QLabel("Sifre")
        password_label.setFont(self._font(12, QFont.Weight.DemiBold))
        password_label.setStyleSheet(f"color: {SOFT};")
        layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("En az 6 karakter")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.textChanged.connect(self._refresh_current_state)
        self.password_input.returnPressed.connect(self._go_next)
        layout.addWidget(self.password_input)

        email_label = QLabel("Destek kisisi e-postasi (opsiyonel)")
        email_label.setFont(self._font(12, QFont.Weight.DemiBold))
        email_label.setStyleSheet(f"color: {SOFT};")
        layout.addWidget(email_label)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("ornek@domain.com")
        self.email_input.textChanged.connect(self._refresh_current_state)
        self.email_input.returnPressed.connect(self._go_next)
        layout.addWidget(self.email_input)

        note = QLabel("Bu ekranda sadece temel kurulum kaydedilir.")
        note.setFont(self._font(11, QFont.Weight.Normal))
        note.setStyleSheet(f"color: {MUTED};")
        layout.addWidget(note)

        layout.addStretch(1)
        return page

    def _font(self, size: int, weight: QFont.Weight) -> QFont:
        font = QFont("Segoe UI", size)
        font.setWeight(weight)
        return font

    def _all_selected_actions(self) -> list[str]:
        actions: list[str] = []
        for index in range(self.actions_list.count()):
            item = self.actions_list.item(index)
            if item is not None and item.checkState() == Qt.CheckState.Checked:
                text = item.text().strip()
                if text and text not in actions:
                    actions.append(text)

        custom_lines = [
            line.strip()
            for line in self.custom_actions_editor.toPlainText().splitlines()
            if line.strip()
        ]
        for line in custom_lines:
            if line not in actions:
                actions.append(line)
        return actions

    def _goal_value(self) -> str:
        return self.goal_editor.toPlainText().strip()

    def _password_value(self) -> str:
        return self.password_input.text().strip()

    def _email_value(self) -> str:
        return self.email_input.text().strip()

    def _goal_valid(self) -> bool:
        return len(self._goal_value()) >= GOAL_MIN_CHARS

    def _actions_valid(self) -> bool:
        return len(self._all_selected_actions()) > 0

    def _credentials_valid(self) -> bool:
        password = self._password_value()
        if len(password) < PASSWORD_MIN_CHARS:
            return False

        email = self._email_value()
        if email and not EMAIL_RE.match(email):
            return False

        return True

    def _save_setting(self, key: str, value) -> bool:
        try:
            core.update_settings(key, value)
        except Exception as exc:  # pragma: no cover - runtime safeguard
            self._set_feedback(f"Kaydetme tamamlanamadi: {exc}", error=True)
            return False
        return True

    def _set_feedback(self, message: str, error: bool = False) -> None:
        self.feedback_label.setText(message)
        self.feedback_label.setStyleSheet(f"color: {ERROR if error else MUTED};")

    def _refresh_current_state(self) -> None:
        self._update_step_ui(self._current_step)
        if self._current_step == 1:
            actions = self._all_selected_actions()
            if actions:
                summary = f"{len(actions)} alternatif hazir."
            else:
                summary = "Henüz secim yapilmadi."
            self.actions_summary.setText(summary)

    def _update_step_ui(self, step_index: int) -> None:
        self._current_step = step_index
        self.stack.setCurrentIndex(step_index)
        self.step_label.setText(f"Adim {step_index + 1} / 3")
        for index, chip in enumerate(self.step_chips):
            if index == step_index:
                chip.setObjectName("StepChipActive")
                chip.setStyleSheet(
                    """
                    QLabel#StepChipActive {
                        color: #f0f0f0;
                        background: rgba(255, 255, 255, 0.08);
                        border: 1px solid #3a3a3a;
                        border-radius: 14px;
                        padding: 8px 12px;
                    }
                    """
                )
            else:
                chip.setObjectName("StepChip")
                chip.setStyleSheet(
                    """
                    QLabel#StepChip {
                        color: #8f8f8f;
                        background: rgba(255, 255, 255, 0.03);
                        border: 1px solid #262626;
                        border-radius: 14px;
                        padding: 8px 12px;
                    }
                    """
                )

        self.back_button.setEnabled(step_index > 0)
        if step_index < 2:
            self.next_button.setText("Devam et")
        else:
            self.next_button.setText("Bitir ve kaydet")

        if step_index == 0:
            self.goal_editor.setFocus()
        elif step_index == 1:
            self.actions_list.setFocus()
        else:
            self.password_input.setFocus()

        if step_index == 1:
            self.actions_summary.setText(
                f"{len(self._all_selected_actions())} alternatif hazir."
                if self._all_selected_actions()
                else "Henüz secim yapilmadi."
            )

    def _animate_step_change(self, next_step: int) -> None:
        self.stack_effect.setOpacity(0.35)
        self.stack.setCurrentIndex(next_step)
        self._step_fade_animation = QPropertyAnimation(self.stack_effect, b"opacity", self)
        self._step_fade_animation.setDuration(180)
        self._step_fade_animation.setStartValue(0.35)
        self._step_fade_animation.setEndValue(1.0)
        self._step_fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._step_fade_animation.start()
        self._update_step_ui(next_step)
        self._feedback_for_step(next_step)

    def _feedback_for_step(self, step_index: int) -> None:
        if step_index == 0:
            self._set_feedback("Niyetini yazip devam edebilirsin.")
        elif step_index == 1:
            self._set_feedback("Bir ya da daha fazla alternatif sec.")
        else:
            self._set_feedback("Sifreni belirle ve istersen destek kisini ekle.")

    def _go_back(self) -> None:
        if self._current_step <= 0:
            return
        self._animate_step_change(self._current_step - 1)

    def _go_next(self) -> None:
        if self._current_step == 0:
            self._commit_goal_and_advance()
            return
        if self._current_step == 1:
            self._commit_actions_and_advance()
            return
        self._commit_credentials_and_finish()

    def _commit_goal_and_advance(self) -> None:
        if not self._goal_valid():
            self._set_feedback("Lutfen hedef alanini doldur.", error=True)
            self.next_button.shake()
            self.goal_editor.setFocus()
            return

        self._goal_text = self._goal_value()
        if not self._save_setting("goals", [self._goal_text]):
            return
        self._set_feedback("Hedef kaydedildi.")
        self._animate_step_change(1)

    def _commit_actions_and_advance(self) -> None:
        if not self._actions_valid():
            self._set_feedback("En az bir alternatif sec veya yaz.", error=True)
            self.next_button.shake()
            self.custom_actions_editor.setFocus()
            return

        actions = self._all_selected_actions()
        self._action_list = actions
        if not self._save_setting("alternative_actions", actions):
            return
        self._set_feedback("Alternatifler kaydedildi.")
        self._animate_step_change(2)

    def _commit_credentials_and_finish(self) -> None:
        password = self._password_value()
        email = self._email_value()

        if not self._credentials_valid():
            if len(password) < PASSWORD_MIN_CHARS:
                self._set_feedback("Sifre en az 6 karakter olmali.", error=True)
                self.next_button.shake()
                self.password_input.setFocus()
                return
            if email and not EMAIL_RE.match(email):
                self._set_feedback("E-posta formati gecersiz gorunuyor.", error=True)
                self.next_button.shake()
                self.email_input.setFocus()
                return

        if not self._save_setting("password", password):
            return
        if not self._save_setting("partner_email", email):
            return
        if not self._save_setting("onboarding_completed", True):
            return

        self._set_feedback("Kurulum tamamlandi.")
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

    window = OnboardingWindow()
    window.showFullScreen()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
