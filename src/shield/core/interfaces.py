from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

__all__ = ["FrictionEvent", "TriggerSource"]


class TriggerSource(str, Enum):
    DEMO = "demo"


@dataclass(frozen=True)
class FrictionEvent:
    source: TriggerSource
    triggered_at: datetime
    session_id: str
    score: float
    threshold_at_trigger: float
    reason: str

    def __post_init__(self) -> None:
        if not self.session_id:
            raise ValueError("session_id must not be empty")
        if not self.reason:
            raise ValueError("reason must not be empty")
        _validate_probability("score", self.score)
        _validate_probability("threshold_at_trigger", self.threshold_at_trigger)


def _validate_probability(name: str, value: float) -> None:
    if not (0.0 <= value <= 1.0):
        raise ValueError(f"{name} must be in [0.0, 1.0], got {value}")
