# System Agent — Shield Project

## Your single responsibility
Implement `src/shield/system/` module: NSSM Windows service lifecycle and password-protected uninstall guard.

## Working directory
Y:/NoFapShield

## Files you must create
- `src/shield/system/service.py`    — NSSM install/uninstall/status
- `src/shield/system/protection.py` — password verification, uninstall attempt logging
- `src/shield/system/__init__.py`   — exports SystemService
- `tests/test_system/test_service.py`
- `tests/test_system/test_protection.py`

## Files you must NOT touch
- Anything outside `src/shield/system/` and `tests/test_system/`
- `src/shield/core/interfaces.py` — read it, never edit it

## Dependencies
- `subprocess` (stdlib) — NSSM command execution
- `bcrypt` — password hash verification
- `src/shield/db/__init__.py` DBService already exists — import it for logging uninstall attempts

## DBService import
```python
from shield.db import DBService
```
DBService has these methods available:
- `get_setting(key, default=None) -> Any`
- `set_setting(key, value) -> None`

## API to implement
```python
import subprocess
import bcrypt
from shield.db import DBService

class NSSMService:
    SERVICE_NAME = "ShieldProtection"

    def __init__(self, nssm_path: str = "nssm") -> None:
        self._nssm = nssm_path

    def install(self, python_path: str, script_path: str) -> bool:
        """Runs: nssm install ShieldProtection <python_path> <script_path>
        Returns True on success (returncode == 0), False otherwise.
        """
        ...

    def uninstall(self) -> bool:
        """Runs: nssm remove ShieldProtection confirm
        Returns True on success, False otherwise.
        """
        ...

    def status(self) -> str:
        """Runs: nssm status ShieldProtection
        Returns stdout stripped, e.g. 'SERVICE_RUNNING', 'SERVICE_STOPPED'.
        Returns 'UNKNOWN' on any error.
        """
        ...

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        """Runs nssm with given args, capture_output=True, timeout=10"""
        ...

class UninstallProtection:
    PASSWORD_HASH_KEY = "uninstall_password_hash"
    ATTEMPT_COUNT_KEY = "uninstall_attempts"

    def __init__(self, db: DBService, user_id: int) -> None: ...

    def verify_password(self, password: str) -> bool:
        """Loads password_hash from db settings (key: 'uninstall_password_hash').
        Returns bcrypt.checkpw(password.encode(), stored_hash).
        Returns False if no hash is stored.
        """
        ...

    def attempt_uninstall(self, password: str, nssm: NSSMService) -> bool:
        """1. Increment uninstall_attempts counter in db settings
        2. If verify_password(password) is True → call nssm.uninstall(), return True
        3. If False → return False (attempt already logged in step 1)
        """
        ...

class SystemService:
    def __init__(self, db: DBService, user_id: int, nssm_path: str = "nssm") -> None: ...
    
    @property
    def nssm(self) -> NSSMService: ...
    
    @property
    def protection(self) -> UninstallProtection: ...
```

## Implementation rules
- NSSM commands use `subprocess.run(..., capture_output=True, timeout=10)`
- Do NOT implement ESC, Alt+F4, or minimize hooks — those are UI's responsibility
- All subprocess calls must be mockable (inject nssm_path parameter)
- UninstallProtection logs every attempt regardless of success/failure (increment counter)

## Testing rules
- Mock `subprocess.run` — never execute real NSSM commands
- Mock `DBService` — use `unittest.mock.MagicMock(spec=DBService)`

```python
from unittest.mock import MagicMock, patch

def test_install_calls_nssm(mock_subprocess):
    mock_subprocess.return_value.returncode = 0
    svc = NSSMService(nssm_path="nssm")
    result = svc.install("/path/to/python", "/path/to/script.py")
    assert result is True
    mock_subprocess.assert_called_once()
    call_args = mock_subprocess.call_args[0][0]
    assert "install" in call_args
    assert NSSMService.SERVICE_NAME in call_args

def test_uninstall_blocked_without_password(mock_db):
    import bcrypt
    pw_hash = bcrypt.hashpw(b"correct", bcrypt.gensalt())
    mock_db.get_setting.return_value = pw_hash
    protection = UninstallProtection(db=mock_db, user_id=1)
    mock_nssm = MagicMock(spec=NSSMService)
    result = protection.attempt_uninstall("wrong_password", nssm=mock_nssm)
    assert result is False
    mock_nssm.uninstall.assert_not_called()

def test_uninstall_succeeds_with_correct_password(mock_db):
    import bcrypt
    pw_hash = bcrypt.hashpw(b"correct", bcrypt.gensalt())
    mock_db.get_setting.return_value = pw_hash
    mock_db.set_setting.return_value = None
    protection = UninstallProtection(db=mock_db, user_id=1)
    mock_nssm = MagicMock(spec=NSSMService)
    mock_nssm.uninstall.return_value = True
    result = protection.attempt_uninstall("correct", nssm=mock_nssm)
    assert result is True
    mock_nssm.uninstall.assert_called_once()
```

## Success criteria
```bash
python -m pytest tests/test_system/ -v --timeout=30
```
All tests pass.

## Boundary
Do not implement anything outside src/shield/system/. Do not implement UI hooks (ESC, Alt+F4, minimize — those are UI's responsibility).
