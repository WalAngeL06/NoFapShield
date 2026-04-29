from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from urllib.parse import urlsplit

RISK_DOMAINS_SETTING_KEY = "trigger_risk_domains"
ALLOW_DOMAINS_SETTING_KEY = "trigger_allow_domains"

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


def match_allowlist(candidate: str, allow_domains: Sequence[str]) -> TriggerMatch | None:
    normalized_candidate = normalize_candidate(candidate)
    candidate_domain = extract_domain(candidate)
    if normalized_candidate is None or candidate_domain is None:
        return None

    for allow_domain in allow_domains:
        allowed_domain = extract_domain(allow_domain)
        if allowed_domain is None:
            continue
        if is_domain_match(candidate_domain, allowed_domain):
            return TriggerMatch(
                candidate=normalized_candidate,
                candidate_domain=candidate_domain,
                matched_domain=allowed_domain,
            )
    return None


def parse_risk_domains(
    value: object,
    fallback: Sequence[str] = DEFAULT_RISK_DOMAINS,
) -> tuple[str, ...]:
    domains = _parse_domain_list(value)
    return tuple(domains) if domains else tuple(fallback)


def parse_allow_domains(value: object) -> tuple[str, ...]:
    return tuple(_parse_domain_list(value))


def load_risk_domains(store) -> tuple[str, ...]:
    try:
        value = store.get_setting(RISK_DOMAINS_SETTING_KEY, None)
    except Exception:
        return DEFAULT_RISK_DOMAINS
    return parse_risk_domains(value)


def load_allow_domains(store) -> tuple[str, ...]:
    try:
        value = store.get_setting(ALLOW_DOMAINS_SETTING_KEY, None)
    except Exception:
        return ()
    return parse_allow_domains(value)


def _is_valid_domain(domain: str) -> bool:
    if not domain or len(domain) > 253:
        return False
    labels = domain.split(".")
    if len(labels) < 2:
        return False
    return all(_DOMAIN_LABEL_RE.match(label) is not None for label in labels)


def _parse_domain_list(value: object) -> list[str]:
    domains: list[str] = []
    seen: set[str] = set()
    for candidate in _iter_domain_candidates(value):
        domain = extract_domain(candidate)
        if domain is None or domain in seen:
            continue
        domains.append(domain)
        seen.add(domain)
    return domains


def _iter_risk_domain_candidates(value: object) -> tuple[str, ...]:
    return _iter_domain_candidates(value)


def _iter_domain_candidates(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return tuple(part.strip() for part in re.split(r"[,\r\n]+", value))
    if isinstance(value, Sequence):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.extend(part.strip() for part in re.split(r"[,\r\n]+", item))
        return tuple(parts)
    return ()
