from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Config:
    trigger_threshold: float = 0.7
    demo_score: float = 1.0
    friction_delay_seconds: int = 15
    db_path: str = ":memory:"

    def __post_init__(self) -> None:
        _validate_probability("trigger_threshold", self.trigger_threshold)
        _validate_probability("demo_score", self.demo_score)
        if self.friction_delay_seconds < 0:
            raise ValueError("friction_delay_seconds cannot be negative")
        if not self.db_path:
            raise ValueError("db_path must not be empty")

    @classmethod
    def from_file(cls, path: Path) -> Config:
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls()
        if not isinstance(data, dict):
            return cls()
        valid = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        try:
            return cls(**valid)
        except (TypeError, ValueError):
            return cls()

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")


def _validate_probability(name: str, value: float) -> None:
    if not (0.0 <= value <= 1.0):
        raise ValueError(f"{name} must be in [0.0, 1.0], got {value}")
