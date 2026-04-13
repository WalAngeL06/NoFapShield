from __future__ import annotations

import bcrypt
from unittest.mock import MagicMock

import pytest

from shield.db import DBService
from shield.system.service import NSSMService
from shield.system.protection import UninstallProtection
from shield.system import SystemService


@pytest.fixture
def pw_hash():
    return bcrypt.hashpw(b"correct", bcrypt.gensalt())


@pytest.fixture
def mock_db():
    return MagicMock(spec=DBService)


@pytest.fixture
def mock_nssm():
    return MagicMock(spec=NSSMService)


class TestUninstallProtectionVerifyPassword:
    def test_returns_true_for_correct_password(self, mock_db, pw_hash):
        mock_db.get_setting.return_value = pw_hash
        protection = UninstallProtection(db=mock_db, user_id=1)
        assert protection.verify_password("correct") is True

    def test_returns_false_for_wrong_password(self, mock_db, pw_hash):
        mock_db.get_setting.return_value = pw_hash
        protection = UninstallProtection(db=mock_db, user_id=1)
        assert protection.verify_password("wrong") is False

    def test_returns_false_when_no_hash_stored(self, mock_db):
        mock_db.get_setting.return_value = None
        protection = UninstallProtection(db=mock_db, user_id=1)
        assert protection.verify_password("any_password") is False

    def test_uses_correct_settings_key(self, mock_db, pw_hash):
        mock_db.get_setting.return_value = pw_hash
        protection = UninstallProtection(db=mock_db, user_id=1)
        protection.verify_password("correct")
        mock_db.get_setting.assert_called_with(UninstallProtection.PASSWORD_HASH_KEY)

    def test_accepts_string_hash_from_db(self, mock_db, pw_hash):
        # DB may return the hash as a string (JSON-decoded)
        mock_db.get_setting.return_value = pw_hash.decode()
        protection = UninstallProtection(db=mock_db, user_id=1)
        assert protection.verify_password("correct") is True


class TestUninstallProtectionAttemptUninstall:
    def test_uninstall_blocked_without_password(self, mock_db, mock_nssm, pw_hash):
        mock_db.get_setting.side_effect = lambda key, default=None: (
            pw_hash if key == UninstallProtection.PASSWORD_HASH_KEY else 0
        )
        protection = UninstallProtection(db=mock_db, user_id=1)
        result = protection.attempt_uninstall("wrong_password", nssm=mock_nssm)
        assert result is False
        mock_nssm.uninstall.assert_not_called()

    def test_uninstall_succeeds_with_correct_password(self, mock_db, mock_nssm, pw_hash):
        mock_db.get_setting.side_effect = lambda key, default=None: (
            pw_hash if key == UninstallProtection.PASSWORD_HASH_KEY else 0
        )
        mock_db.set_setting.return_value = None
        protection = UninstallProtection(db=mock_db, user_id=1)
        mock_nssm.uninstall.return_value = True
        result = protection.attempt_uninstall("correct", nssm=mock_nssm)
        assert result is True
        mock_nssm.uninstall.assert_called_once()

    def test_attempt_counter_incremented_on_success(self, mock_db, mock_nssm, pw_hash):
        mock_db.get_setting.side_effect = lambda key, default=None: (
            pw_hash if key == UninstallProtection.PASSWORD_HASH_KEY else 3
        )
        mock_db.set_setting.return_value = None
        mock_nssm.uninstall.return_value = True
        protection = UninstallProtection(db=mock_db, user_id=1)
        protection.attempt_uninstall("correct", nssm=mock_nssm)
        mock_db.set_setting.assert_called_with(UninstallProtection.ATTEMPT_COUNT_KEY, 4)

    def test_attempt_counter_incremented_on_failure(self, mock_db, mock_nssm, pw_hash):
        mock_db.get_setting.side_effect = lambda key, default=None: (
            pw_hash if key == UninstallProtection.PASSWORD_HASH_KEY else 0
        )
        mock_db.set_setting.return_value = None
        protection = UninstallProtection(db=mock_db, user_id=1)
        protection.attempt_uninstall("wrong", nssm=mock_nssm)
        mock_db.set_setting.assert_called_with(UninstallProtection.ATTEMPT_COUNT_KEY, 1)

    def test_attempt_counter_starts_at_zero_when_missing(self, mock_db, mock_nssm, pw_hash):
        mock_db.get_setting.side_effect = lambda key, default=None: (
            pw_hash if key == UninstallProtection.PASSWORD_HASH_KEY else default
        )
        mock_db.set_setting.return_value = None
        protection = UninstallProtection(db=mock_db, user_id=1)
        protection.attempt_uninstall("wrong", nssm=mock_nssm)
        mock_db.set_setting.assert_called_with(UninstallProtection.ATTEMPT_COUNT_KEY, 1)

    def test_returns_false_when_no_hash_stored(self, mock_db, mock_nssm):
        mock_db.get_setting.side_effect = lambda key, default=None: (
            None if key == UninstallProtection.PASSWORD_HASH_KEY else default
        )
        protection = UninstallProtection(db=mock_db, user_id=1)
        result = protection.attempt_uninstall("any", nssm=mock_nssm)
        assert result is False
        mock_nssm.uninstall.assert_not_called()


class TestSystemService:
    def test_nssm_property_returns_nssm_service(self, mock_db):
        svc = SystemService(db=mock_db, user_id=1)
        assert isinstance(svc.nssm, NSSMService)

    def test_protection_property_returns_uninstall_protection(self, mock_db):
        svc = SystemService(db=mock_db, user_id=1)
        assert isinstance(svc.protection, UninstallProtection)

    def test_custom_nssm_path_forwarded(self, mock_db):
        svc = SystemService(db=mock_db, user_id=1, nssm_path="/custom/nssm")
        assert svc.nssm._nssm == "/custom/nssm"
