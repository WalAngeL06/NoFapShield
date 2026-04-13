# Privacy Agent — Shield Project

## Your single responsibility
Implement `src/shield/privacy/` module: accountability notifications via SMTP (extensible to other channels).

## Working directory
Y:/NoFapShield

## Files you must create
- `src/shield/privacy/accountability.py`   — AccountabilityService class
- `src/shield/privacy/__init__.py`         — exports AccountabilityService
- `tests/test_privacy/test_accountability.py`

## Files you must NOT touch
- Anything outside `src/shield/privacy/` and `tests/test_privacy/`
- `src/shield/core/interfaces.py` — read it, never edit it

## Interface contract
```python
from shield.core.interfaces import FrictionEvent
```

## AccountabilityService API (implement exactly this)
```python
from dataclasses import dataclass
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
    def __init__(self, config: AccountabilityConfig) -> None: ...
    
    def send(self, event: FrictionEvent) -> None:
        """Send accountability email to partner.
        
        If config.enabled is False, returns immediately (no-op).
        Subject: "Shield: accountability check-in"
        Body: triggered_at, final_score, session_id
        Raises: AccountabilityError on SMTP failure
        Screenshots and image data are NEVER included.
        """
        ...
    
    def test_connection(self) -> bool:
        """Returns True if SMTP login succeeds, False on any failure. Never raises."""
        ...
```

## Implementation rules
- Use `smtplib` + `email.mime` from stdlib — no third-party mail library
- Use STARTTLS (`smtp.starttls()`) on port 587
- If `config.enabled` is False, `send()` returns immediately without connecting
- Screenshots are NEVER attached or referenced in emails
- `AccountabilityError` is defined in `accountability.py`
- `test_connection()` must catch all exceptions and return False on any failure

## Privacy constraint
The `send()` method receives a `FrictionEvent` which contains a `HybridScore`.
- Include in email: `event.score.final_score`, `event.triggered_at`, `event.session_id`
- Never include: image_bytes, any screenshot data
- `HybridScore.nsfw` may be None (DNS-triggered events) — never access it

## Testing rules
- Mock `smtplib.SMTP` — never open real SMTP connections in tests
- Test: `send()` calls `smtp.sendmail()` when enabled=True
- Test: `send()` is a no-op when enabled=False
- Test: `send()` raises AccountabilityError when SMTP throws
- Test: `test_connection()` returns False on any exception, never raises

## Success criteria
```bash
python -m pytest tests/test_privacy/ -v --timeout=30
```
All tests pass.

## Boundary
Do not implement anything outside src/shield/privacy/. No disk writes. No screenshot handling.
