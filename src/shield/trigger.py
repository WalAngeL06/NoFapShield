from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from urllib.parse import urlsplit

DEFAULT_RISK_DOMAINS: tuple[str, ...] = (
    "risk.example",
    "blocked.example",
    "relapse.example",
)

_DOMAIN_LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


@dataclass(frozen=True)
class TriggerMatch:
    candidate: str
    candidate_domain: str
    matched_domain: str


def normalize_candidate(value: str) -> str | None:
    candidate = value.strip().lower()
    return candidate or None


def extract_domain(value: str) -> str | None:
    candidate = normalize_candidate(value)
    if candidate is None:
        return None
    if any(char.isspace() for char in candidate) or "\\" in candidate:
        return None

    parse_target = candidate if "://" in candidate else f"https://{candidate}"
    try:
        parsed = urlsplit(parse_target)
    except ValueError:
        return None

    hostname = parsed.hostname
    if hostname is None:
        return None

    domain = hostname.strip(".").lower()
    if not _is_valid_domain(domain):
        return None
    return domain


def is_domain_match(candidate_domain: str, blocked_domain: str) -> bool:
    candidate = extract_domain(candidate_domain)
    blocked = extract_domain(blocked_domain)
    if candidate is None or blocked is None:
        return False
    return candidate == blocked or candidate.endswith(f".{blocked}")


def match_trigger(candidate: str, risk_domains: Sequence[str]) -> TriggerMatch | None:
    normalized_candidate = normalize_candidate(candidate)
    candidate_domain = extract_domain(candidate)
    if normalized_candidate is None or candidate_domain is None:
        return None

    for risk_domain in risk_domains:
        blocked_domain = extract_domain(risk_domain)
        if blocked_domain is None:
            continue
        if is_domain_match(candidate_domain, blocked_domain):
            return TriggerMatch(
                candidate=normalized_candidate,
                candidate_domain=candidate_domain,
                matched_domain=blocked_domain,
            )
    return None


def _is_valid_domain(domain: str) -> bool:
    if not domain or len(domain) > 253:
        return False
    labels = domain.split(".")
    if len(labels) < 2:
        return False
    return all(_DOMAIN_LABEL_RE.match(label) is not None for label in labels)
