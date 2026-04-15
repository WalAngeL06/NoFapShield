from __future__ import annotations

import sys
from pathlib import Path
from typing import Final

from PyQt6.QtCore import QEasingCurve, QEvent, QPropertyAnimation, QDate, Qt, pyqtProperty, QTimer
from PyQt6.QtGui import QFont, QKeyEvent
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStyle,
    QStyleOptionButton,
    QStylePainter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

APP_BG: Final[str] = "#0a0a0a"
SURFACE: Final[str] = "#121212"
SURFACE_2: Final[str] = "#181818"
BORDER: Final[str] = "#262626"
TEXT: Final[str] = "#ececec"
MUTED: Final[str] = "#9c9c9c"
ACCENT: Final[str] = "#dcdcdc"

MIN_CHARS: Final[int] = 40
QUESTIONS: Final[tuple[str, ...]] = (
    "Bugün bu saatte burada olmak istediğini söyleyebilir misin?",
    "Şu an içinde hissettiklerini bir cümleyle tarif et.",
    "Yarın sabah bugünü nasıl hatırlamak istersin?",
    "Bu eylem seni hedeflerine yaklaştırıyor mu, uzaklaştırıyor mu?",
    "Gerçekten istediğin şey bu mu?",
)


_ROOT_DIR = Path(__file__).resolve().parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

try:  # pragma: no cover - runtime integration
    import core  # type: ignore
except Exception:  # pragma: no cover - local fallback for standalone runs

    class _CoreFallback:
        def get_streak(self) -> int:
            return 0

        def save_checkin(self, text: str) -> None:
            return None

    core = _CoreFallback()  # type: ignore


class ShakeButton(QPushButton):
    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self._shake_offset = 0.0
        self._shake_anim = QPropertyAnimation(self, b"shakeOffset", self)
        self._shake_anim.setDuration(360)
        self._shake_anim.setEasingCurve(QEasingCurve.Type.Linear)
        self._shake_anim.setKeyValueAt(0.0, 0.0)
        self._shake_anim.setKeyValueAt(0.12, -10.0)
        self._shake_anim.setKeyValueAt(0.24, 10.0)
        self._shake_anim.setKeyValueAt(0.36, -8.0)
        self._shake_anim.setKeyValueAt(0.48, 8.0)
        self._shake_anim.setKeyValueAt(0.60, -5.0)
        self._shake_anim.setKeyValueAt(0.72, 5.0)
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


class MorningCheckinWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._allow_close = False
        self._question = self._daily_question()

        self._configure_window()
        self._build_ui()
        self._refresh_state()

    def _configure_window(self) -> None:
        self.setWindowTitle("Shield - Morning Check-in")
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
            QTextEdit {{
                background: {SURFACE};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 20px;
                padding: 18px;
                selection-background-color: #3b3b3b;
                selection-color: {TEXT};
                font-size: 16px;
                line-height: 1.4;
            }}
            QTextEdit:focus {{
                border: 1px solid #3a3a3a;
                background: {SURFACE_2};
            }}
            QPushButton#submitButton {{
                background: {ACCENT};
                color: #0c0c0c;
                border: 1px solid {ACCENT};
                border-radius: 18px;
                padding: 16px 22px;
                font-size: 17px;
                font-weight: 700;
            }}
            QPushButton#submitButton:hover {{
                background: #f4f4f4;
            }}
            QPushButton#submitButton:pressed {{
                background: #d1d1d1;
            }}
            """
        )

    def _build_ui(self) -> None:
        root = QWidget(self)
        root.setStyleSheet(f"background: {APP_BG};")
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(48, 42, 48, 40)
        outer.setSpacing(0)

        header = QHBoxLayout()
        header.setSpacing(12)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)

        self.kicker = QLabel("Günün duraklaması")
        self.kicker.setFont(self._font(12, QFont.Weight.DemiBold))
        self.kicker.setStyleSheet(f"color: {MUTED}; letter-spacing: 0.6px;")

        self.question_label = QLabel(self._question)
        self.question_label.setFont(self._font(26, QFont.Weight.DemiBold))
        self.question_label.setWordWrap(True)

        title_col.addWidget(self.kicker)
        title_col.addWidget(self.question_label)
        title_col.setStretch(0, 0)

        header.addLayout(title_col, 1)

        self.streak_label = QLabel()
        self.streak_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self.streak_label.setFont(self._font(13, QFont.Weight.DemiBold))
        self.streak_label.setStyleSheet(
            """
            QLabel {
                color: #d8d8d8;
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid #2a2a2a;
                border-radius: 16px;
                padding: 10px 14px;
            }
            """
        )
        self.streak_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        header.addWidget(self.streak_label, 0, Qt.AlignmentFlag.AlignTop)

        outer.addLayout(header)
        outer.addSpacing(22)

        self.card = QFrame()
        self.card.setStyleSheet(
            f"""
            QFrame {{
                background: rgba(18, 18, 18, 0.92);
                border: 1px solid {BORDER};
                border-radius: 28px;
            }}
            """
        )
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(26, 26, 26, 26)
        card_layout.setSpacing(18)

        intro = QLabel("Kısa bir cevap yaz. Bu ekran ancak yeterince yazdıktan sonra kapanır.")
        intro.setFont(self._font(13, QFont.Weight.Normal))
        intro.setWordWrap(True)
        intro.setStyleSheet(f"color: {MUTED};")
        card_layout.addWidget(intro)

        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Buraya yaz...")
        self.editor.setAcceptRichText(False)
        self.editor.setTabChangesFocus(True)
        self.editor.setMinimumHeight(220)
        self.editor.textChanged.connect(self._refresh_state)
        card_layout.addWidget(self.editor, 1)

        counter_row = QHBoxLayout()
        counter_row.setSpacing(12)

        self.counter_label = QLabel()
        self.counter_label.setFont(self._font(12, QFont.Weight.DemiBold))
        self.counter_label.setStyleSheet(f"color: {MUTED};")
        counter_row.addWidget(self.counter_label, 1)

        self.hint_label = QLabel("Cevap cihazda yerel kalır.")
        self.hint_label.setFont(self._font(12, QFont.Weight.Normal))
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.hint_label.setStyleSheet(f"color: {MUTED};")
        counter_row.addWidget(self.hint_label, 0)

        card_layout.addLayout(counter_row)

        self.submit_button = ShakeButton("Kaydet ve devam et")
        self.submit_button.setObjectName("submitButton")
        self.submit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.submit_button.setMinimumHeight(56)
        self.submit_button.clicked.connect(self._submit)
        card_layout.addWidget(self.submit_button)

        outer.addWidget(self.card, 1)

        footer = QLabel("40 karakter dolmadan bu pencere kapanmaz.")
        footer.setFont(self._font(11, QFont.Weight.Normal))
        footer.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        footer.setStyleSheet(f"color: {MUTED};")
        outer.addSpacing(18)
        outer.addWidget(footer)

    def _font(self, size: int, weight: QFont.Weight) -> QFont:
        font = QFont("Segoe UI", size)
        font.setWeight(weight)
        return font

    def _daily_question(self) -> str:
        index = QDate.currentDate().toJulianDay() % len(QUESTIONS)
        return QUESTIONS[index]

    def _current_text(self) -> str:
        return self.editor.toPlainText().strip()

    def _is_valid(self) -> bool:
        return len(self._current_text()) >= MIN_CHARS

    def _remaining_chars(self) -> int:
        return max(0, MIN_CHARS - len(self._current_text()))

    def _refresh_state(self) -> None:
        remaining = self._remaining_chars()
        if remaining > 0:
            self.counter_label.setText(f"{remaining} karakter daha")
        else:
            self.counter_label.setText("✓")

        self.streak_label.setText(f"Streak {self._streak()}")
        self.submit_button.setEnabled(True)

    def _streak(self) -> int:
        try:
            streak = core.get_streak()
        except Exception:
            return 0
        try:
            return int(streak)
        except Exception:
            return 0

    def _submit(self) -> None:
        if not self._is_valid():
            self.submit_button.shake()
            self.editor.setFocus()
            return

        text = self._current_text()
        try:
            core.save_checkin(text)
        except Exception as exc:  # pragma: no cover - runtime safeguard
            self.counter_label.setText(f"Kaydetme başarısız: {exc}")
            self.submit_button.shake()
            return

        self._allow_close = True
        self.close()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.raise_()
        self.activateWindow()
        self.setFocus()
        self.editor.setFocus()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            event.ignore()
            return
        if event.key() == Qt.Key.Key_F4 and event.modifiers() & Qt.KeyboardModifier.AltModifier:
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

    window = MorningCheckinWindow()
    window.showFullScreen()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
