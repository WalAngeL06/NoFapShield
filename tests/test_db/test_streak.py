from datetime import date

from shield.db.streak import compute_streak


def test_same_day_no_change():
    today = date(2024, 3, 10)
    new_current, new_longest = compute_streak(5, 10, today, today)
    assert new_current == 5
    assert new_longest == 10


def test_consecutive_day_increments():
    yesterday = date(2024, 3, 9)
    today = date(2024, 3, 10)
    new_current, new_longest = compute_streak(5, 5, yesterday, today)
    assert new_current == 6
    assert new_longest == 6


def test_consecutive_day_extends_longest():
    yesterday = date(2024, 3, 9)
    today = date(2024, 3, 10)
    new_current, new_longest = compute_streak(10, 10, yesterday, today)
    assert new_current == 11
    assert new_longest == 11


def test_gap_resets_to_one():
    old = date(2024, 3, 1)
    today = date(2024, 3, 10)
    new_current, new_longest = compute_streak(7, 7, old, today)
    assert new_current == 1
    assert new_longest == 7  # longest preserved


def test_gap_longest_preserved_when_higher():
    old = date(2024, 3, 1)
    today = date(2024, 3, 10)
    new_current, new_longest = compute_streak(3, 20, old, today)
    assert new_current == 1
    assert new_longest == 20


def test_two_day_gap_resets():
    two_days_ago = date(2024, 3, 8)
    today = date(2024, 3, 10)
    new_current, _ = compute_streak(5, 5, two_days_ago, today)
    assert new_current == 1
