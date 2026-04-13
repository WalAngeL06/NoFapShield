from datetime import date


def compute_streak(
    current_days: int,
    longest_days: int,
    last_active_date: date,
    today: date,
) -> tuple[int, int]:
    """Return (new_current_days, new_longest_days) based on the gap since last_active_date.

    - Gap == 0 (same day): no change.
    - Gap == 1 (yesterday): increment current_days.
    - Gap  > 1 (missed days): reset current_days to 1.
    longest_days is always at least current_days.
    """
    delta = (today - last_active_date).days
    if delta == 0:
        return current_days, longest_days
    if delta == 1:
        new_current = current_days + 1
    else:
        new_current = 1
    new_longest = max(longest_days, new_current)
    return new_current, new_longest
