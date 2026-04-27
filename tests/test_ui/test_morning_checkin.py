import os
from datetime import date

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from shield.ui.morning_checkin import MIN_CHECKIN_CHARS, QUESTIONS, MorningCheckinWindow, question_for_date


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def test_question_for_date_is_allowed_and_deterministic():
    day = date(2026, 4, 27)

    assert question_for_date(day) in QUESTIONS
    assert question_for_date(day) == question_for_date(day)
    assert question_for_date(day.replace(day=28)) in QUESTIONS


def test_character_counter_below_and_at_limit(qapp):
    window = MorningCheckinWindow()

    window._text_edit.setPlainText("abc")
    window.update_character_counter()
    assert window._counter_label.text() == f"{MIN_CHECKIN_CHARS - 3} karakter daha"

    window._text_edit.setPlainText("x" * MIN_CHECKIN_CHARS)
    window.update_character_counter()
    assert window._counter_label.text() == "✓"


def test_invalid_submit_does_not_allow_close(qapp):
    saved: list[str] = []
    window = MorningCheckinWindow(save_checkin=saved.append)

    window._text_edit.setPlainText("kısa")
    result = window.submit()

    assert result is False
    assert window.can_close() is False
    assert saved == []
    assert window._feedback_label.text()


def test_valid_submit_saves_and_allows_close(qapp):
    saved: list[str] = []
    window = MorningCheckinWindow(save_checkin=saved.append)
    text = "Bugün kendime karşı dürüst ve sakin kalmayı seçiyorum."

    window._text_edit.setPlainText(text)
    result = window.submit()

    assert result is True
    assert saved == [text]
    assert window.can_close() is True


def test_close_and_key_guards(qapp):
    window = MorningCheckinWindow()

    assert window.can_close() is False
    assert window.should_block_key(Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier) is True
    assert window.should_block_key(Qt.Key.Key_F4, Qt.KeyboardModifier.AltModifier) is True
    assert window.should_block_key(Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier) is False

    window.request_internal_close()

    assert window.can_close() is True
