from __future__ import annotations

import sys
from collections import Counter
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Final

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

APP_BG: Final[str] = "#0a0a0a"
SURFACE: Final[str] = "#111111"
SURFACE_2: Final[str] = "#171717"
BORDER: Final[str] = "#272727"
TEXT: Final[str] = "#ececec"
MUTED: Final[str] = "#a0a0a0"
SOFT: Final[str] = "#d6d6d6"
ACCENT_2: Final[str] = "#222222"
POSITIVE: Final[str] = "#c8d8c8"

WEEKDAY_LABELS: Final[tuple[str, ...]] = ("Pzt", "Sal", "Car", "Per", "Cum", "Cmt", "Paz")
MAX_HISTORY_ITEMS: Final[int] = 20
MAX_TRIGGER_ROWS: Final[int] = 50

_ROOT_DIR = Path(__file__).resolve().parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

try:  # pragma: no cover - runtime integration
    import core  # type: ignore
except Exception:  # pragma: no cover - standalone fallback

    class _CoreFallback:
        def get_streak(self) -> int:
            return 0

        def get_goals(self) -> list[str]:
            return []

        def get_checkin_history(self) -> list[dict]:
            return []

        def get_trigger_log(self) -> list[dict]:
            return []

    core = _CoreFallback()  # type: ignore


def _safe_call(name: str, default: Any) -> Any:
    func = getattr(core, name, None)
    if not callable(func):
        return default
    try:
        return func()
    except Exception:
        return default


def _font(size: int, weight: QFont.Weight) -> QFont:
    font = QFont("Segoe UI", size)
    font.setWeight(weight)
    return font


def _normalize_text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        text = value.strip()
        return text or fallback
    return str(value).strip() or fallback


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
                pass
        patterns = (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%d.%m.%Y %H:%M",
            "%d.%m.%Y",
        )
        for pattern in patterns:
            try:
                return datetime.strptime(text, pattern)
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

    for value in entry.values():
        if isinstance(value, dict):
            for nested_key in ("iso", "datetime", "date", "created_at", "timestamp", "time", "value"):
                if nested_key in value:
                    parsed = _parse_datetime(value.get(nested_key))
                    if parsed is not None:
                        return parsed
    return None


def _relative_time_label(when: datetime | None) -> str:
    if when is None:
        return "zaman bilinmiyor"

    now = datetime.now(when.tzinfo) if when.tzinfo else datetime.now()
    delta = now - when
    seconds = max(0, int(delta.total_seconds()))
    if seconds < 60:
        return "az once"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} dakika once"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} saat once"
    days = hours // 24
    if days < 7:
        return f"{days} gun once"
    weeks = days // 7
    if weeks < 5:
        return f"{weeks} hafta once"
    months = days // 30
    if months < 12:
        return f"{months} ay once"
    years = days // 365
    return f"{years} yil once"


def _format_clock(when: datetime | None) -> str:
    if when is None:
        return "Saat bilinmiyor"
    return when.strftime("%d.%m.%Y %H:%M")


def _coerce_entries(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, dict):
            out.append(item)
    return out


class MetricCard(QFrame):
    def __init__(self, title: str, value: str, subtitle: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("MetricCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        self.title_label = QLabel(title)
        self.title_label.setFont(_font(12, QFont.Weight.DemiBold))
        self.title_label.setStyleSheet(f"color: {MUTED}; letter-spacing: 0.6px;")

        self.value_label = QLabel(value)
        self.value_label.setFont(_font(30, QFont.Weight.Bold))
        self.value_label.setStyleSheet(f"color: {TEXT};")

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setFont(_font(12, QFont.Weight.Normal))
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setStyleSheet(f"color: {MUTED};")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.subtitle_label)


class SectionCard(QFrame):
    def __init__(self, title: str, subtitle: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SectionCard")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 18, 20, 20)
        self._layout.setSpacing(14)

        header = QVBoxLayout()
        header.setSpacing(4)

        title_label = QLabel(title)
        title_label.setFont(_font(18, QFont.Weight.DemiBold))

        subtitle_label = QLabel(subtitle)
        subtitle_label.setFont(_font(12, QFont.Weight.Normal))
        subtitle_label.setWordWrap(True)
        subtitle_label.setStyleSheet(f"color: {MUTED};")

        header.addWidget(title_label)
        header.addWidget(subtitle_label)

        self._layout.addLayout(header)

    def body(self) -> QVBoxLayout:
        return self._layout


class HistoryEntryCard(QFrame):
    def __init__(self, entry: dict[str, Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("HistoryEntryCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        when = _extract_datetime(entry)
        rel = _relative_time_label(when)
        exact = _format_clock(when)
        text = _normalize_text(
            entry.get("text")
            or entry.get("answer")
            or entry.get("content")
            or entry.get("note")
            or entry.get("response"),
            "Icerik yok",
        )

        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        time_label = QLabel(rel)
        time_label.setFont(_font(12, QFont.Weight.DemiBold))
        time_label.setStyleSheet(f"color: {SOFT};")

        exact_label = QLabel(exact)
        exact_label.setFont(_font(11, QFont.Weight.Normal))
        exact_label.setStyleSheet(f"color: {MUTED};")
        exact_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        header_row.addWidget(time_label, 0)
        header_row.addStretch(1)
        header_row.addWidget(exact_label, 0)

        body = QLabel(text)
        body.setFont(_font(13, QFont.Weight.Normal))
        body.setWordWrap(True)
        body.setStyleSheet(f"color: {TEXT}; line-height: 1.35;")

        layout.addLayout(header_row)
        layout.addWidget(body)


class WeekCell(QFrame):
    def __init__(self, label: str, day_num: str, active: bool, is_today: bool, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("WeekCell")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        day_label = QLabel(label)
        day_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        day_label.setFont(_font(11, QFont.Weight.DemiBold))
        day_label.setStyleSheet(f"color: {MUTED};")

        num_label = QLabel(day_num)
        num_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        num_label.setFont(_font(16, QFont.Weight.Bold))
        num_label.setStyleSheet(f"color: {TEXT};")

        status_label = QLabel("✓" if active else "·")
        status_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        status_label.setFont(_font(15, QFont.Weight.Bold))
        status_label.setStyleSheet(f"color: {POSITIVE if active else MUTED};")

        layout.addWidget(day_label)
        layout.addWidget(num_label)
        layout.addWidget(status_label)

        if is_today:
            self.setStyleSheet(
                f"""
                QFrame#WeekCell {{
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid #3a3a3a;
                    border-radius: 16px;
                }}
                """
            )
        elif active:
            self.setStyleSheet(
                f"""
                QFrame#WeekCell {{
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid #2d2d2d;
                    border-radius: 16px;
                }}
                """
            )
        else:
            self.setStyleSheet(
                f"""
                QFrame#WeekCell {{
                    background: rgba(255, 255, 255, 0.015);
                    border: 1px solid #232323;
                    border-radius: 16px;
                }}
                """
            )


class DashboardWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Shield - Dashboard")
        self.resize(1360, 920)
        self.setMinimumSize(1100, 760)
        self.setStyleSheet(
            f"""
            QMainWindow, QWidget {{
                background: {APP_BG};
                color: {TEXT};
            }}
            QLabel {{
                color: {TEXT};
            }}
            QFrame#MetricCard, QFrame#SectionCard, QFrame#HistoryEntryCard {{
                background: rgba(17, 17, 17, 0.96);
                border: 1px solid {BORDER};
                border-radius: 22px;
            }}
            QFrame#WeekCell {{
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid {BORDER};
                border-radius: 16px;
            }}
            QTabWidget::pane {{
                border: 1px solid {BORDER};
                background: rgba(17, 17, 17, 0.96);
                border-radius: 22px;
                top: -1px;
            }}
            QTabBar::tab {{
                background: rgba(255, 255, 255, 0.03);
                color: {MUTED};
                border: 1px solid {BORDER};
                border-bottom: 0;
                border-top-left-radius: 14px;
                border-top-right-radius: 14px;
                padding: 10px 14px;
                min-width: 130px;
                margin-right: 6px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background: rgba(255, 255, 255, 0.07);
                color: {TEXT};
            }}
            QTableWidget {{
                background: transparent;
                color: {TEXT};
                gridline-color: {BORDER};
                border: 0;
                outline: 0;
            }}
            QHeaderView::section {{
                background: rgba(255, 255, 255, 0.04);
                color: {MUTED};
                border: 0;
                border-bottom: 1px solid {BORDER};
                padding: 10px 12px;
                font-weight: 600;
            }}
            QTableWidget::item {{
                padding: 10px 12px;
                border-bottom: 1px solid #1e1e1e;
            }}
            QTableWidget::item:selected {{
                background: rgba(255, 255, 255, 0.05);
            }}
            QPushButton#RefreshButton {{
                background: rgba(255, 255, 255, 0.04);
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 14px;
                padding: 10px 14px;
                font-weight: 600;
            }}
            QPushButton#RefreshButton:hover {{
                background: rgba(255, 255, 255, 0.07);
            }}
            """
        )

        self._build_ui()
        self.refresh()

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(60_000)
        self._refresh_timer.timeout.connect(self.refresh)
        self._refresh_timer.start()

    def _build_ui(self) -> None:
        root = QWidget(self)
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(18)

        header = QHBoxLayout()
        header.setSpacing(14)

        title_col = QVBoxLayout()
        title_col.setSpacing(5)

        kicker = QLabel("Dashboard")
        kicker.setFont(_font(12, QFont.Weight.DemiBold))
        kicker.setStyleSheet(f"color: {MUTED}; letter-spacing: 0.8px;")

        title = QLabel("Gunluk durum, haftalik ritim ve geri bildirimler")
        title.setFont(_font(28, QFont.Weight.Bold))
        title.setWordWrap(True)

        subtitle = QLabel(
            "Streak, check-in gecmisi, hedefler ve tetiklenme anlari ayni sakin yuzeyde."
        )
        subtitle.setFont(_font(13, QFont.Weight.Normal))
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"color: {MUTED};")

        title_col.addWidget(kicker)
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header.addLayout(title_col, 1)

        self.refresh_button = QPushButton("Yenile")
        self.refresh_button.setObjectName("RefreshButton")
        self.refresh_button.clicked.connect(self.refresh)
        header.addWidget(self.refresh_button, 0, Qt.AlignmentFlag.AlignTop)

        outer.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(18)

        left_col = QVBoxLayout()
        left_col.setSpacing(18)

        self.streak_card = MetricCard(
            "Gunluk streak",
            "0",
            "Core'dan gelen son deger.",
        )
        left_col.addWidget(self.streak_card)

        week_card = SectionCard("Haftalik gorunum", "Son 7 gunun check-in ritmi.")
        self.week_grid = QHBoxLayout()
        self.week_grid.setSpacing(10)
        week_card.body().addLayout(self.week_grid)
        self.week_empty = QLabel("Henuz hafta ici veri yok.")
        self.week_empty.setFont(_font(12, QFont.Weight.Normal))
        self.week_empty.setStyleSheet(f"color: {MUTED};")
        self.week_empty.setWordWrap(True)
        self.week_empty.setVisible(False)
        week_card.body().addWidget(self.week_empty)
        left_col.addWidget(week_card)

        goals_card = SectionCard("Hedefler", "Kullanicinin onboarding'de girdigi kendi nedenleri.")
        self.goals_body = QVBoxLayout()
        self.goals_body.setSpacing(10)
        goals_card.body().addLayout(self.goals_body)
        left_col.addWidget(goals_card)
        left_col.addStretch(1)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(False)

        self.history_tab = QWidget()
        history_layout = QVBoxLayout(self.history_tab)
        history_layout.setContentsMargins(18, 18, 18, 18)
        history_layout.setSpacing(14)

        history_intro = QLabel("Gecmise hizli bakis: son cevaplar ve zaman baglamlari.")
        history_intro.setFont(_font(12, QFont.Weight.Normal))
        history_intro.setStyleSheet(f"color: {MUTED};")
        history_intro.setWordWrap(True)
        history_layout.addWidget(history_intro)

        self.history_scroll = QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.history_scroll.setStyleSheet("background: transparent; border: 0;")
        self.history_scroll_content = QWidget()
        self.history_scroll_layout = QVBoxLayout(self.history_scroll_content)
        self.history_scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.history_scroll_layout.setSpacing(12)
        self.history_scroll_layout.addStretch(1)
        self.history_scroll.setWidget(self.history_scroll_content)
        history_layout.addWidget(self.history_scroll, 1)

        self.history_empty = QLabel("Henuz kaydedilmis bir check-in yok.")
        self.history_empty.setFont(_font(13, QFont.Weight.Normal))
        self.history_empty.setStyleSheet(f"color: {MUTED};")
        self.history_empty.setWordWrap(True)
        history_layout.addWidget(self.history_empty)

        self.logs_tab = QWidget()
        logs_layout = QVBoxLayout(self.logs_tab)
        logs_layout.setContentsMargins(18, 18, 18, 18)
        logs_layout.setSpacing(14)

        logs_intro = QLabel("Tetiklenme loglari saat ve yogunluk penceresiyle.")
        logs_intro.setFont(_font(12, QFont.Weight.Normal))
        logs_intro.setStyleSheet(f"color: {MUTED};")
        logs_intro.setWordWrap(True)
        logs_layout.addWidget(logs_intro)

        self.trigger_summary = QLabel("Henuz tetiklenme logu yok.")
        self.trigger_summary.setFont(_font(12, QFont.Weight.DemiBold))
        self.trigger_summary.setStyleSheet(f"color: {SOFT};")
        self.trigger_summary.setWordWrap(True)
        logs_layout.addWidget(self.trigger_summary)

        self.trigger_table = QTableWidget(0, 4)
        self.trigger_table.setHorizontalHeaderLabels(["Saat", "Kaynak", "Detay", "Adet"])
        self.trigger_table.verticalHeader().setVisible(False)
        self.trigger_table.setAlternatingRowColors(False)
        self.trigger_table.setShowGrid(False)
        self.trigger_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.trigger_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.trigger_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.trigger_table.setWordWrap(True)
        self.trigger_table.horizontalHeader().setStretchLastSection(True)
        self.trigger_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.trigger_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.trigger_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.trigger_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.trigger_table.setMinimumHeight(420)
        logs_layout.addWidget(self.trigger_table, 1)

        self.trigger_empty = QLabel("Henuz tetiklenme logu yok.")
        self.trigger_empty.setFont(_font(13, QFont.Weight.Normal))
        self.trigger_empty.setStyleSheet(f"color: {MUTED};")
        self.trigger_empty.setWordWrap(True)
        logs_layout.addWidget(self.trigger_empty)

        self.tabs.addTab(self.history_tab, "Check-in gecmisi")
        self.tabs.addTab(self.logs_tab, "Tetiklenme loglari")

        body.addLayout(left_col, 4)
        body.addWidget(self.tabs, 6)

        outer.addLayout(body, 1)

    def refresh(self) -> None:
        self._refresh_streak()
        self._refresh_goals()
        self._refresh_week_view()
        self._refresh_history()
        self._refresh_triggers()

    def _refresh_streak(self) -> None:
        streak = _safe_call("get_streak", 0)
        try:
            streak_value = int(streak)
        except Exception:
            streak_value = 0

        self.streak_card.value_label.setText(str(streak_value))
        self.streak_card.subtitle_label.setText(
            "Core'dan gelen son deger." if streak_value else "Henuz baslamamis bir seri."
        )

    def _refresh_goals(self) -> None:
        while self.goals_body.count():
            item = self.goals_body.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        goals = _safe_call("get_goals", [])
        goals_list = [goal for goal in goals if _normalize_text(goal)]

        if not goals_list:
            empty = QLabel("Henuz hedef eklenmemis.")
            empty.setFont(_font(12, QFont.Weight.Normal))
            empty.setStyleSheet(f"color: {MUTED};")
            empty.setWordWrap(True)
            self.goals_body.addWidget(empty)
            return

        for goal in goals_list[:8]:
            pill = QLabel(_normalize_text(goal))
            pill.setFont(_font(12, QFont.Weight.DemiBold))
            pill.setWordWrap(True)
            pill.setStyleSheet(
                f"""
                QLabel {{
                    background: rgba(255, 255, 255, 0.04);
                    color: {TEXT};
                    border: 1px solid {BORDER};
                    border-radius: 14px;
                    padding: 10px 12px;
                }}
                """
            )
            self.goals_body.addWidget(pill)

    def _refresh_week_view(self) -> None:
        while self.week_grid.count():
            item = self.week_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        history = _coerce_entries(_safe_call("get_checkin_history", []))
        history_dates: set[date] = set()
        for entry in history:
            when = _extract_datetime(entry)
            if when is not None:
                history_dates.add(when.date())

        today = datetime.now().date()
        start = today - timedelta(days=today.weekday())
        days = [start + timedelta(days=offset) for offset in range(7)]

        if not days:
            self.week_empty.setVisible(True)
            return

        self.week_empty.setVisible(False)

        for current_day in days:
            cell = WeekCell(
                WEEKDAY_LABELS[current_day.weekday()],
                str(current_day.day),
                active=current_day in history_dates,
                is_today=current_day == today,
            )
            self.week_grid.addWidget(cell)

        self.week_grid.addStretch(1)

    def _refresh_history(self) -> None:
        history = _coerce_entries(_safe_call("get_checkin_history", []))
        sorted_history = sorted(
            history,
            key=lambda entry: _extract_datetime(entry) or datetime.min,
            reverse=True,
        )[:MAX_HISTORY_ITEMS]

        while self.history_scroll_layout.count():
            item = self.history_scroll_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not sorted_history:
            self.history_empty.setVisible(True)
            self.history_scroll.setVisible(False)
            return

        self.history_empty.setVisible(False)
        self.history_scroll.setVisible(True)

        for entry in sorted_history:
            self.history_scroll_layout.addWidget(HistoryEntryCard(entry))
        self.history_scroll_layout.addStretch(1)

    def _refresh_triggers(self) -> None:
        logs = _coerce_entries(_safe_call("get_trigger_log", []))
        sorted_logs = sorted(
            logs,
            key=lambda entry: _extract_datetime(entry) or datetime.min,
            reverse=True,
        )[:MAX_TRIGGER_ROWS]

        self.trigger_table.setRowCount(0)

        if not sorted_logs:
            self.trigger_empty.setVisible(True)
            self.trigger_summary.setText("Henuz tetiklenme logu yok.")
            return

        self.trigger_empty.setVisible(False)

        hourly_counts: Counter[int] = Counter()
        for entry in sorted_logs:
            when = _extract_datetime(entry)
            if when is not None:
                hourly_counts[when.hour] += 1

        if hourly_counts:
            top_hours = hourly_counts.most_common(5)
            summary_bits = [f"{hour:02d}:00 - {count}" for hour, count in top_hours]
            self.trigger_summary.setText("En yogun saatler: " + ", ".join(summary_bits))
        else:
            self.trigger_summary.setText("Saat verisi olmayan loglar geldi.")

        self.trigger_table.setRowCount(len(sorted_logs))
        for row, entry in enumerate(sorted_logs):
            when = _extract_datetime(entry)
            when_label = when.strftime("%H:%M") if when is not None else "--:--"
            source = _normalize_text(
                entry.get("source")
                or entry.get("reason")
                or entry.get("domain")
                or entry.get("site")
                or entry.get("label")
                or entry.get("trigger"),
                "Bilinmiyor",
            )
            detail = _normalize_text(
                entry.get("detail")
                or entry.get("message")
                or entry.get("text")
                or entry.get("note")
                or entry.get("url")
                or entry.get("query")
                or entry.get("pattern"),
                "Detay yok",
            )

            count_value = entry.get("count")
            if count_value is None:
                count_value = entry.get("hits")
            if count_value is None:
                count_value = entry.get("occurrences")
            if count_value is None:
                count_value = 1

            self.trigger_table.setItem(row, 0, QTableWidgetItem(when_label))
            self.trigger_table.setItem(row, 1, QTableWidgetItem(source))
            self.trigger_table.setItem(row, 2, QTableWidgetItem(detail))
            self.trigger_table.setItem(row, 3, QTableWidgetItem(f"x{count_value}"))

            for column in range(4):
                item = self.trigger_table.item(row, column)
                if item is not None:
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                    item.setToolTip(detail)
            self.trigger_table.item(row, 0).setToolTip(_format_clock(when))
            self.trigger_table.item(row, 1).setToolTip(source)
            self.trigger_table.item(row, 3).setToolTip(f"Toplam tekrar: x{count_value}")

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        QTimer.singleShot(0, self.refresh)


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    window = DashboardWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
