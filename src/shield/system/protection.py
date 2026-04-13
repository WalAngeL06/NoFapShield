from __future__ import annotations

import bcrypt

from shield.db import DBService
from shield.system.service import NSSMService


class UninstallProtection:
    PASSWORD_HASH_KEY = "uninstall_password_hash"
    ATTEMPT_COUNT_KEY = "uninstall_attempts"

    def __init__(self, db: DBService, user_id: int) -> None:
        self._db = db
        # user_id reserved for future multi-user support;
        # current operations use global settings keys
        self._user_id = user_id

    def verify_password(self, password: str) -> bool:
        """Loads password_hash from db settings (key: 'uninstall_password_hash').
        Returns bcrypt.checkpw(password.encode(), stored_hash).
        Returns False if no hash is stored.
        """
        stored_hash = self._db.get_setting(self.PASSWORD_HASH_KEY)
        if stored_hash is None:
            return False
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode()
        return bcrypt.checkpw(password.encode(), stored_hash)

    def attempt_uninstall(self, password: str, nssm: NSSMService) -> bool:
        """1. Increment uninstall_attempts counter in db settings
        2. If verify_password(password) is True → call nssm.uninstall(), return True
        3. If False → return False (attempt already logged in step 1)
        """
        current = self._db.get_setting(self.ATTEMPT_COUNT_KEY, 0)
        self._db.set_setting(self.ATTEMPT_COUNT_KEY, current + 1)

        if self.verify_password(password):
            return nssm.uninstall()
        return False
