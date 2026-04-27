from datetime import datetime, timezone

import pytest

from shield.core import FrictionEvent, TriggerSource


def test_friction_event_validates_score_range():
    with pytest.raises(ValueError, match="score"):
        FrictionEvent(
            source=TriggerSource.DEMO,
            triggered_at=datetime.now(timezone.utc),
            session_id="s",
            score=1.1,
            threshold_at_trigger=0.7,
            reason="test",
        )


def test_friction_event_requires_session_id_and_reason():
    with pytest.raises(ValueError, match="session_id"):
        FrictionEvent(
            source=TriggerSource.DEMO,
            triggered_at=datetime.now(timezone.utc),
            session_id="",
            score=1.0,
            threshold_at_trigger=0.7,
            reason="test",
        )

    with pytest.raises(ValueError, match="reason"):
        FrictionEvent(
            source=TriggerSource.DEMO,
            triggered_at=datetime.now(timezone.utc),
            session_id="s",
            score=1.0,
            threshold_at_trigger=0.7,
            reason="",
        )
