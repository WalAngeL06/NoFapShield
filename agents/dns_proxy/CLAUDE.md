# DNS Proxy Agent — Shield Project

## Your single responsibility
Implement `src/shield/dns_proxy/` module: local DNS proxy on 127.0.0.1:53 and StevenBlack hosts blocklist management.

## Working directory
Y:/NoFapShield

## Files you must create
- `src/shield/dns_proxy/blocklist.py`   — StevenBlack list fetch and domain lookup
- `src/shield/dns_proxy/server.py`      — DNS proxy server + DomainScore production
- `src/shield/dns_proxy/__init__.py`    — exports DNSProxyService
- `tests/test_dns_proxy/test_blocklist.py`
- `tests/test_dns_proxy/test_server.py`

## Files you must NOT touch
- Anything outside `src/shield/dns_proxy/` and `tests/test_dns_proxy/`
- `src/shield/core/interfaces.py` — read it, never edit it

## Interface contract
```python
from shield.core.interfaces import DomainScore
```

## API to implement
```python
from shield.core.interfaces import DomainScore

BLOCKLIST_URL = "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"

class BlocklistManager:
    def __init__(self) -> None:
        self._domains: set[str] = set()

    def fetch_and_update(self) -> int:
        """Downloads BLOCKLIST_URL, parses lines like '0.0.0.0 example.com'.
        Ignores comment lines (#), ignores '0.0.0.0' and 'localhost' entries.
        Returns count of loaded domains.
        """
        ...

    def is_blocked(self, domain: str) -> bool:
        """Case-insensitive lookup, strips trailing dot if present."""
        ...

    def domain_score(self, domain: str) -> DomainScore:
        """Returns DomainScore(domain=domain, match_score=1.0 if blocked, else 0.0)."""
        ...

class DNSProxyService:
    def __init__(self, blocklist: BlocklistManager, upstream: str = "8.8.8.8") -> None: ...

    def start(self) -> None:
        """Binds UDP socket to 127.0.0.1:53.
        Forwards non-blocked queries to upstream DNS.
        Blocked domains: returns NXDOMAIN response.
        Runs in current thread until stop() is called.
        """
        ...

    def stop(self) -> None:
        """Signals the server loop to exit."""
        ...

    def get_last_queried_domain(self) -> str | None:
        """Returns the most recently queried domain (for orchestrator DNS TTL)."""
        ...
```

## Implementation rules
- Use `dnspython` (`dns.message`, `dns.query`) for DNS message parsing/building
- UDP socket only — no TCP DNS
- `BlocklistManager.fetch_and_update()` uses `urllib.request.urlopen` — no requests library
- Blocklist is stored in memory only — no file I/O
- Mock `urllib.request.urlopen` in tests — never hit real internet

## Testing rules

```python
SAMPLE_HOSTS = b"""
# Comment line
127.0.0.1 localhost
0.0.0.0 pornhub.com
0.0.0.0 xvideos.com
# Another comment
0.0.0.0 example-safe.com
"""

def test_blocklist_parses_correctly(mock_urlopen):
    # mock_urlopen returns io.BytesIO(SAMPLE_HOSTS)
    mgr = BlocklistManager()
    count = mgr.fetch_and_update()
    assert "pornhub.com" in mgr._domains
    assert "localhost" not in mgr._domains
    assert count >= 3

def test_domain_score_blocked(mock_urlopen):
    mgr = BlocklistManager()
    mgr.fetch_and_update()
    score = mgr.domain_score("pornhub.com")
    assert score.match_score == 1.0

def test_domain_score_not_blocked(mock_urlopen):
    mgr = BlocklistManager()
    mgr.fetch_and_update()
    score = mgr.domain_score("google.com")
    assert score.match_score == 0.0

def test_is_blocked_case_insensitive(mock_urlopen):
    mgr = BlocklistManager()
    mgr.fetch_and_update()
    assert mgr.is_blocked("PORNHUB.COM") is True
```

- Do NOT start a real DNS server in tests — test BlocklistManager independently
- DNSProxyService tests use `unittest.mock.patch("socket.socket")` to avoid binding port 53

## Success criteria
```bash
python -m pytest tests/test_dns_proxy/ -v --timeout=30
```
All tests pass.

## Boundary
Do not implement anything outside src/shield/dns_proxy/. Do not import from detection, privacy, db, or system modules.
