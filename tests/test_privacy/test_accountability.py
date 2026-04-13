from __future__ import annotations

import smtplib
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from shield.core.interfaces import (
    DomainScore,
    FrictionEvent,
    HybridScore,
    NSFWScore,
    TriggerSource,
)
from shield.privacy.accountability import (
    AccountabilityConfig,
    AccountabilityError,
    AccountabilityService,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event(source: TriggerSource = TriggerSource.SCREENSHOT) -> FrictionEvent:
    nsfw = NSFWScore(model_score=0.85, confidence=0.9) if source == TriggerSource.SCREENSHOT else None
    score = HybridScore(
        final_score=0.75,
        domain=DomainScore(domain="example.com", match_score=0.5),
        url_score=0.2,
        source=source,
        computed_at=datetime(2024, 1, 15, 10, 30, 0),
        nsfw=nsfw,
    )
    return FrictionEvent(
        score=score,
        triggered_at=datetime(2024, 1, 15, 10, 30, 5),
        session_id="sess-abc-123",
        threshold_at_trigger=0.6,
    )


def _make_config(enabled: bool = True) -> AccountabilityConfig:
    return AccountabilityConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_user="sender@example.com",
        smtp_password="secret",
        partner_email="partner@example.com",
        enabled=enabled,
    )


# ---------------------------------------------------------------------------
# send() — enabled path
# ---------------------------------------------------------------------------

class TestSendEnabled:
    @patch("shield.privacy.accountability.smtplib.SMTP")
    def test_calls_sendmail(self, mock_smtp_cls):
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_smtp

        service = AccountabilityService(_make_config(enabled=True))
        event = _make_event()
        service.send(event)

        mock_smtp.sendmail.assert_called_once()

    @patch("shield.privacy.accountability.smtplib.SMTP")
    def test_calls_starttls(self, mock_smtp_cls):
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_smtp

        service = AccountabilityService(_make_config(enabled=True))
        service.send(_make_event())

        mock_smtp.starttls.assert_called_once()

    @patch("shield.privacy.accountability.smtplib.SMTP")
    def test_calls_login(self, mock_smtp_cls):
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_smtp

        service = AccountabilityService(_make_config(enabled=True))
        service.send(_make_event())

        mock_smtp.login.assert_called_once_with("sender@example.com", "secret")

    @patch("shield.privacy.accountability.smtplib.SMTP")
    def test_email_contains_final_score(self, mock_smtp_cls):
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_smtp

        service = AccountabilityService(_make_config(enabled=True))
        service.send(_make_event())

        _, _, raw_msg = mock_smtp.sendmail.call_args[0]
        assert "0.75" in raw_msg

    @patch("shield.privacy.accountability.smtplib.SMTP")
    def test_email_contains_session_id(self, mock_smtp_cls):
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_smtp

        service = AccountabilityService(_make_config(enabled=True))
        service.send(_make_event())

        _, _, raw_msg = mock_smtp.sendmail.call_args[0]
        assert "sess-abc-123" in raw_msg

    @patch("shield.privacy.accountability.smtplib.SMTP")
    def test_email_contains_triggered_at(self, mock_smtp_cls):
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_smtp

        service = AccountabilityService(_make_config(enabled=True))
        service.send(_make_event())

        _, _, raw_msg = mock_smtp.sendmail.call_args[0]
        assert "2024-01-15" in raw_msg

    @patch("shield.privacy.accountability.smtplib.SMTP")
    def test_email_subject(self, mock_smtp_cls):
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_smtp

        service = AccountabilityService(_make_config(enabled=True))
        service.send(_make_event())

        _, _, raw_msg = mock_smtp.sendmail.call_args[0]
        assert "Shield: accountability check-in" in raw_msg

    @patch("shield.privacy.accountability.smtplib.SMTP")
    def test_dns_event_does_not_access_nsfw(self, mock_smtp_cls):
        """DNS-triggered events have nsfw=None — send() must not crash."""
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_smtp

        service = AccountabilityService(_make_config(enabled=True))
        service.send(_make_event(source=TriggerSource.DNS))

        mock_smtp.sendmail.assert_called_once()

    @patch("shield.privacy.accountability.smtplib.SMTP")
    def test_no_image_bytes_in_email(self, mock_smtp_cls):
        """Screenshots must never appear in email content."""
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_smtp

        service = AccountabilityService(_make_config(enabled=True))
        service.send(_make_event())

        _, _, raw_msg = mock_smtp.sendmail.call_args[0]
        assert "image_bytes" not in raw_msg
        assert "screenshot" not in raw_msg.lower()


# ---------------------------------------------------------------------------
# send() — disabled path
# ---------------------------------------------------------------------------

class TestSendDisabled:
    @patch("shield.privacy.accountability.smtplib.SMTP")
    def test_no_smtp_connection_when_disabled(self, mock_smtp_cls):
        service = AccountabilityService(_make_config(enabled=False))
        service.send(_make_event())

        mock_smtp_cls.assert_not_called()

    @patch("shield.privacy.accountability.smtplib.SMTP")
    def test_returns_none_when_disabled(self, mock_smtp_cls):
        service = AccountabilityService(_make_config(enabled=False))
        result = service.send(_make_event())

        assert result is None


# ---------------------------------------------------------------------------
# send() — SMTP failure raises AccountabilityError
# ---------------------------------------------------------------------------

class TestSendSmtpFailure:
    @patch("shield.privacy.accountability.smtplib.SMTP")
    def test_raises_accountability_error_on_smtp_exception(self, mock_smtp_cls):
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_smtp
        mock_smtp.sendmail.side_effect = smtplib.SMTPException("connection refused")

        service = AccountabilityService(_make_config(enabled=True))
        with pytest.raises(AccountabilityError):
            service.send(_make_event())

    @patch("shield.privacy.accountability.smtplib.SMTP")
    def test_raises_accountability_error_on_starttls_failure(self, mock_smtp_cls):
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_smtp
        mock_smtp.starttls.side_effect = OSError("TLS handshake failed")

        service = AccountabilityService(_make_config(enabled=True))
        with pytest.raises(AccountabilityError):
            service.send(_make_event())

    @patch("shield.privacy.accountability.smtplib.SMTP")
    def test_raises_accountability_error_on_connect_failure(self, mock_smtp_cls):
        mock_smtp_cls.side_effect = OSError("connection refused")

        service = AccountabilityService(_make_config(enabled=True))
        with pytest.raises(AccountabilityError):
            service.send(_make_event())

    @patch("shield.privacy.accountability.smtplib.SMTP")
    def test_original_exception_is_chained(self, mock_smtp_cls):
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_smtp
        original = smtplib.SMTPAuthenticationError(535, b"auth failed")
        mock_smtp.login.side_effect = original

        service = AccountabilityService(_make_config(enabled=True))
        with pytest.raises(AccountabilityError) as exc_info:
            service.send(_make_event())

        assert exc_info.value.__cause__ is original


# ---------------------------------------------------------------------------
# test_connection()
# ---------------------------------------------------------------------------

class TestTestConnection:
    @patch("shield.privacy.accountability.smtplib.SMTP")
    def test_returns_true_on_success(self, mock_smtp_cls):
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_smtp

        service = AccountabilityService(_make_config())
        assert service.test_connection() is True

    @patch("shield.privacy.accountability.smtplib.SMTP")
    def test_returns_false_on_smtp_exception(self, mock_smtp_cls):
        mock_smtp_cls.side_effect = smtplib.SMTPException("bad server")

        service = AccountabilityService(_make_config())
        assert service.test_connection() is False

    @patch("shield.privacy.accountability.smtplib.SMTP")
    def test_returns_false_on_os_error(self, mock_smtp_cls):
        mock_smtp_cls.side_effect = OSError("network unreachable")

        service = AccountabilityService(_make_config())
        assert service.test_connection() is False

    @patch("shield.privacy.accountability.smtplib.SMTP")
    def test_returns_false_on_auth_failure(self, mock_smtp_cls):
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_smtp
        mock_smtp.login.side_effect = smtplib.SMTPAuthenticationError(535, b"auth failed")

        service = AccountabilityService(_make_config())
        assert service.test_connection() is False

    @patch("shield.privacy.accountability.smtplib.SMTP")
    def test_never_raises(self, mock_smtp_cls):
        mock_smtp_cls.side_effect = RuntimeError("unexpected error")

        service = AccountabilityService(_make_config())
        # must not propagate — just return False
        result = service.test_connection()
        assert result is False

    @patch("shield.privacy.accountability.smtplib.SMTP")
    def test_calls_starttls_and_login(self, mock_smtp_cls):
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_smtp

        service = AccountabilityService(_make_config())
        service.test_connection()

        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("sender@example.com", "secret")

    def test_connection_skips_login_with_empty_credentials(self):
        config = AccountabilityConfig(smtp_host="mail.example.com", enabled=True)
        service = AccountabilityService(config)
        with patch("shield.privacy.accountability.smtplib.SMTP") as mock_smtp_cls:
            mock_smtp = MagicMock()
            mock_smtp_cls.return_value.__enter__.return_value = mock_smtp
            result = service.test_connection()
            mock_smtp.login.assert_not_called()
