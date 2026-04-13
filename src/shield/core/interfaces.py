from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

__all__ = [
    "TriggerSource",
    "ScreenshotResult",
    "NSFWScore",
    "DomainScore",
    "HybridScore",
    "FrictionEvent",
    "UserGoal",
    "StreakInfo",
]


class TriggerSource(Enum):
    SCREENSHOT = "screenshot"
    DNS = "dns"


@dataclass
class ScreenshotResult:
    """Produced by detection/screenshot.py — RAM buffer, never written to disk."""
    image_bytes: bytes
    captured_at: datetime


@dataclass
class NSFWScore:
    """Produced by detection/classifier.py."""
    model_score: float   # NudeNet output [0.0–1.0]
    confidence: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.model_score <= 1.0):
            raise ValueError(f"model_score must be in [0.0, 1.0], got {self.model_score}")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence must be in [0.0, 1.0], got {self.confidence}")


@dataclass
class DomainScore:
    """Produced by dns_proxy/server.py."""
    domain: str
    match_score: float   # 1.0 on blocklist hit, 0.0 otherwise

    def __post_init__(self) -> None:
        if not (0.0 <= self.match_score <= 1.0):
            raise ValueError(f"match_score must be in [0.0, 1.0], got {self.match_score}")


@dataclass
class HybridScore:
    """Calculated by detection/scorer.py.
    final_score = 0.6 * model_score + 0.3 * domain_match + 0.1 * url_score
    """
    final_score: float
    domain: DomainScore
    url_score: float
    source: TriggerSource
    computed_at: datetime
    nsfw: Optional[NSFWScore] = None  # None iff source is TriggerSource.DNS


    def __post_init__(self) -> None:
        if self.source == TriggerSource.SCREENSHOT and self.nsfw is None:
            raise ValueError("nsfw must be provided when source is SCREENSHOT")
        if self.source == TriggerSource.DNS and self.nsfw is not None:
            raise ValueError("nsfw must be None when source is DNS")


@dataclass
class FrictionEvent:
    """Consumed by core/event_loop.py, forwarded to UI via callback."""
    score: HybridScore
    triggered_at: datetime
    session_id: str
    threshold_at_trigger: float  # snapshot of config threshold at moment of trigger

    def __post_init__(self) -> None:
        if not self.session_id:
            raise ValueError("session_id must not be empty")


@dataclass
class UserGoal:
    """Provided by db/models.py — shown to user during friction."""
    goal_text: str
    created_at: datetime


@dataclass
class StreakInfo:
    """Calculated by db/streak.py."""
    current_days: int
    longest_days: int
    last_reset: datetime

    def __post_init__(self) -> None:
        if self.current_days < 0:
            raise ValueError("current_days cannot be negative")
        if self.longest_days < 0:
            raise ValueError("longest_days cannot be negative")
        if self.current_days > self.longest_days:
            raise ValueError(
                f"current_days ({self.current_days}) cannot exceed longest_days ({self.longest_days})"
            )
