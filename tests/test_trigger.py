import pytest

from shield.trigger import (
    DEFAULT_RISK_DOMAINS,
    extract_domain,
    is_domain_match,
    match_trigger,
    normalize_candidate,
)


def test_normalize_candidate_trims_and_lowercases():
    assert normalize_candidate("  HTTPS://Risk.Example/Path  ") == "https://risk.example/path"


@pytest.mark.parametrize(
    ("candidate", "expected"),
    [
        ("risk.example", "risk.example"),
        ("  RISK.EXAMPLE  ", "risk.example"),
        ("https://www.risk.example/path", "www.risk.example"),
        ("risk.example/path?x=1", "risk.example"),
        ("risk.example:8443/path", "risk.example"),
    ],
)
def test_extract_domain_normalizes_url_and_bare_domain(candidate, expected):
    assert extract_domain(candidate) == expected


@pytest.mark.parametrize("candidate", ["", "   ", "not a url", "http://", "bad_domain.test"])
def test_extract_domain_rejects_empty_or_malformed_input(candidate):
    assert extract_domain(candidate) is None


def test_is_domain_match_accepts_exact_domain():
    assert is_domain_match("risk.example", "risk.example")


def test_is_domain_match_accepts_subdomain():
    assert is_domain_match("sub.risk.example", "risk.example")


def test_is_domain_match_rejects_different_suffix():
    assert not is_domain_match("risk.example.evil.test", "risk.example")


def test_match_trigger_returns_first_matching_placeholder_domain():
    match = match_trigger("https://sub.risk.example/path", DEFAULT_RISK_DOMAINS)

    assert match is not None
    assert match.candidate == "https://sub.risk.example/path"
    assert match.candidate_domain == "sub.risk.example"
    assert match.matched_domain == "risk.example"


def test_match_trigger_returns_none_for_no_match_or_invalid_risk_entries():
    assert match_trigger("safe.example", ["", "bad_domain.test", "risk.example"]) is None
