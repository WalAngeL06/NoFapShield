from datetime import datetime

from shield.core.interfaces import StreakInfo, UserGoal


def streak_row_to_info(row: tuple) -> StreakInfo:
    """Convert a streaks table row to StreakInfo.

    Row order: (id, user_id, started_at, last_active, current_days, longest_days)
    """
    started_at = datetime.fromisoformat(row[2])
    return StreakInfo(
        current_days=row[4],
        longest_days=row[5],
        last_reset=started_at,
    )


def goal_row_to_goal(row: tuple) -> UserGoal:
    """Convert a questions table row to UserGoal.

    Row order: (id, text, created_at)
    """
    return UserGoal(
        goal_text=row[1],
        created_at=datetime.fromisoformat(row[2]),
    )
