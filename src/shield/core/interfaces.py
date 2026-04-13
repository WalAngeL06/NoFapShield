# src/shield/core/interfaces.py
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


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


@dataclass
class DomainScore:
    """Produced by dns_proxy/server.py."""
    domain: str
    match_score: float   # 1.0 on blocklist hit, 0.0 otherwise


@dataclass
class HybridScore:
    """Calculated by detection/scorer.py.
    final_score = 0.6 * model_score + 0.3 * domain_match + 0.1 * url_heuristic
    """
    final_score: float
    nsfw: NSFWScore
    domain: DomainScore
    url_score: float
    source: TriggerSource
    computed_at: datetime


@dataclass
class FrictionEvent:
    """Consumed by core/event_loop.py, forwarded to UI via callback."""
    score: HybridScore
    triggered_at: datetime
    session_id: str
    threshold_at_trigger: float  # snapshot of config threshold at moment of trigger


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
