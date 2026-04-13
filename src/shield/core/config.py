# src/shield/core/config.py
from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Config:
    detection_threshold: float = 0.7
    screenshot_interval: int = 3       # seconds between captures
    dns_score_ttl: int = 10            # seconds before DNS score resets to 0.0
    db_path: str = "shield.db"
    accountability_enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    partner_email: str = ""

    @classmethod
    def from_file(cls, path: Path) -> Config:
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            valid = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
            return cls(**valid)
        except (json.JSONDecodeError, TypeError):
            return cls()

    def save(self, path: Path) -> None:
        path.write_text(
            json.dumps(asdict(self), indent=2), encoding="utf-8"
        )
