from __future__ import annotations

import urllib.request
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
        with urllib.request.urlopen(BLOCKLIST_URL) as response:
            raw = response.read()

        domains: set[str] = set()
        for line in raw.decode("utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            ip, domain = parts[0], parts[1].lower()
            if domain in ("0.0.0.0", "localhost", "localhost.localdomain", "broadcasthost"):
                continue
            if domain.startswith("#"):
                continue
            domains.add(domain)

        self._domains = domains
        return len(self._domains)

    def is_blocked(self, domain: str) -> bool:
        """Case-insensitive lookup, strips trailing dot if present."""
        return domain.rstrip(".").lower() in self._domains

    def domain_score(self, domain: str) -> DomainScore:
        """Returns DomainScore(domain=domain, match_score=1.0 if blocked, else 0.0)."""
        score = 1.0 if self.is_blocked(domain) else 0.0
        return DomainScore(domain=domain, match_score=score)
