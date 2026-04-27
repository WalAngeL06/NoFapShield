from __future__ import annotations

from collections.abc import Callable
from datetime import date

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from shield.core import Config
from shield.db import EventStore

_active_dashboard_window: DashboardWindow | None = None


def run_dashboard(db_path: str | None = None) -> int:
    """Launch dashboard as CLI owner or attach it to an existing Qt app."""
    global _active_dashboard_window

    app = QApplication.instance()
    owns_event_loop = app is None
    if app is None:
        app = QApplication([])

    path = db_path if db_path is not None else Config().db_path
    store = EventStore(path)
    window = DashboardWindow(
        get_checkins=lambda: store.get_checkin_history(limit=50),
        get_triggers=lambda: store.list_events(limit=50),
    )
    _active_dashboard_window = window
    window.destroyed.connect(lambda *_: _release_active_dashboard(window))
    window.destroyed.connect(lambda *_: store.close())
    window.show()
    window.raise_()
    window.activateWindow()
    if not owns_event_loop:
        return 0

    exit_code = int(app.exec())
    _release_active_dashboard(window)
    return exit_code


def _release_active_dashboard(window: DashboardWindow) -> None:
    global _active_dashboard_window
    if _active_dashboard_window is window:
        _active_dashboard_window = None


class DashboardWindow(QWidget):
    def __init__(
        self,
        get_checkins: Callable[[], list[dict]] | None = None,
        get_triggers: Callable[[], list[dict]] | None = None,
    ) -> None:
        super().__init__()
        self._get_checkins = get_checkins or (lambda: [])
        self._get_triggers = get_triggers or (lambda: [])

        self.setWindowTitle("Shield")
        self.setMinimumSize(800, 600)
        self.resize(960, 700)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setStyleSheet("background: #0a0a0a; color: #f8fafc;")

        self._build_ui()

    def _build_ui(self) -> None:
        checkins = self._get_checkins()
        triggers = self._get_triggers()

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
        layout.setSpacing(32)

        layout.addLayout(self._build_header())
        layout.addLayout(self._build_cards(checkins, triggers))
        layout.addLayout(self._build_section(
            "Son Check-inler",
            checkins,
            lambda row: row["created_at"][:10] + "  —  " + row["text"][:80],
            "_checkin_list",
        ))
        layout.addLayout(self._build_section(
            "Tetikleyici Günlüğü",
            triggers,
            lambda row: row["triggered_at"][:10] + "  —  " + row["reason"],
            "_trigger_list",
        ))
        layout.addStretch(1)

    def _build_header(self) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(6)

        title = QLabel("Shield")
        title.setFont(_font(32, QFont.Weight.Bold))
        title.setStyleSheet("color: #f8fafc; background: transparent;")
        col.addWidget(title)

        subtitle = QLabel("Bugün sakin bir seçim daha.")
        subtitle.setFont(_font(15))
        subtitle.setStyleSheet("color: #94a3b8; background: transparent;")
        col.addWidget(subtitle)

        chip = QLabel("Local-only")
        chip.setFont(_font(11, QFont.Weight.DemiBold))
        chip.setStyleSheet(
            "color: #86efac; background: #052e16; border-radius: 4px; padding: 2px 8px;"
        )
        col.addWidget(chip, alignment=Qt.AlignmentFlag.AlignLeft)

        return col

    def _build_cards(self, checkins: list[dict], triggers: list[dict]) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(16)

        today_iso = date.today().isoformat()
        has_today = any(entry["created_at"][:10] == today_iso for entry in checkins)
        today_text = "✓ Yapıldı" if has_today else "—"

        self._today_status_label = _add_card(row, "Bugün Check-in", today_text)
        self._total_checkins_label = _add_card(row, "Toplam Check-in", str(len(checkins)))
        self._total_triggers_label = _add_card(row, "Tetikleyici", str(len(triggers)))

        row.addStretch(1)
        return row

    def _build_section(
        self,
        title: str,
        rows: list[dict],
        formatter: Callable[[dict], str],
        attr_name: str,
    ) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(10)

        heading = QLabel(title)
        heading.setFont(_font(14, QFont.Weight.DemiBold))
        heading.setStyleSheet("color: #94a3b8; background: transparent;")
        col.addWidget(heading)

        list_widget = QListWidget()
        list_widget.setMaximumHeight(200)
        list_widget.setStyleSheet(
            """
            QListWidget {
                background: #111827;
                border: 1px solid #1e293b;
                border-radius: 8px;
                color: #cbd5e1;
                padding: 4px;
            }
            QListWidget::item { padding: 8px 12px; }
            QListWidget::item:alternate { background: #0f172a; }
            """
        )
        list_widget.setAlternatingRowColors(True)
        list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)

        if rows:
            for entry in rows:
                list_widget.addItem(QListWidgetItem(formatter(entry)))
        else:
            empty = QListWidgetItem("Henüz kayıt yok.")
            empty.setForeground(QColor("#475569"))
            list_widget.addItem(empty)

        setattr(self, attr_name, list_widget)
        col.addWidget(list_widget)
        return col


def _add_card(parent: QHBoxLayout, title: str, value: str) -> QLabel:
    card = QFrame()
    card.setFrameShape(QFrame.Shape.NoFrame)
    card.setStyleSheet(
        "QFrame { background: #111827; border: 1px solid #1e293b; border-radius: 10px; }"
    )
    card.setFixedSize(200, 100)

    col = QVBoxLayout(card)
    col.setContentsMargins(16, 14, 16, 14)
    col.setSpacing(4)

    label = QLabel(title)
    label.setFont(_font(11))
    label.setStyleSheet("color: #64748b; background: transparent; border: none;")
    col.addWidget(label)

    value_label = QLabel(value)
    value_label.setFont(_font(22, QFont.Weight.Bold))
    value_label.setStyleSheet("color: #f8fafc; background: transparent; border: none;")
    col.addWidget(value_label)

    parent.addWidget(card)
    return value_label


def _font(size: int, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    font = QFont("Segoe UI", size)
    font.setWeight(weight)
    return font
