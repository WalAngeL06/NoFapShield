from shield.db import DBService
from shield.system.service import NSSMService
from shield.system.protection import UninstallProtection


class SystemService:
    def __init__(self, db: DBService, user_id: int, nssm_path: str = "nssm") -> None:
        self._nssm = NSSMService(nssm_path=nssm_path)
        self._protection = UninstallProtection(db=db, user_id=user_id)

    @property
    def nssm(self) -> NSSMService:
        return self._nssm

    @property
    def protection(self) -> UninstallProtection:
        return self._protection


__all__ = ["SystemService"]
