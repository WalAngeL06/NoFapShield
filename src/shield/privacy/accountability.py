from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.mime.text import MIMEText

from shield.core.interfaces import FrictionEvent


@dataclass
class AccountabilityConfig:
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    partner_email: str = ""
    enabled: bool = False


class AccountabilityError(Exception):
    pass


class AccountabilityService:
    def __init__(self, config: AccountabilityConfig) -> None:
        self._config = config

    def send(self, event: FrictionEvent) -> None:
        """Send accountability email to partner.

        If config.enabled is False, returns immediately (no-op).
        Subject: "Shield: accountability check-in"
        Body: triggered_at, final_score, session_id
        Raises: AccountabilityError on SMTP failure
        Screenshots and image data are NEVER included.
        """
        if not self._config.enabled:
            return

        body = (
            f"triggered_at: {event.triggered_at.isoformat()}\n"
            f"final_score: {event.score.final_score}\n"
            f"session_id: {event.session_id}\n"
        )

        msg = MIMEText(body)
        msg["Subject"] = "Shield: accountability check-in"
        msg["From"] = self._config.smtp_user
        msg["To"] = self._config.partner_email

        try:
            with smtplib.SMTP(self._config.smtp_host, self._config.smtp_port) as smtp:
                smtp.starttls()
                if self._config.smtp_user and self._config.smtp_password:
                    smtp.login(self._config.smtp_user, self._config.smtp_password)
                smtp.sendmail(
                    self._config.smtp_user,
                    self._config.partner_email,
                    msg.as_string(),
                )
        except Exception as exc:
            raise AccountabilityError(str(exc)) from exc

    def test_connection(self) -> bool:
        """Returns True if SMTP login succeeds, False on any failure. Never raises."""
        try:
            with smtplib.SMTP(self._config.smtp_host, self._config.smtp_port) as smtp:
                smtp.starttls()
                smtp.login(self._config.smtp_user, self._config.smtp_password)
            return True
        except Exception:
            return False
