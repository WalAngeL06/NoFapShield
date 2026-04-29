import pytest

from shield.trigger import (
    ALLOW_DOMAINS_SETTING_KEY,
    DEFAULT_RISK_DOMAINS,
    RISK_DOMAINS_SETTING_KEY,
    extract_domain,
    is_domain_match,
    load_allow_domains,
    load_risk_domains,
    match_allowlist,
    match_trigger,
    normalize_candidate,
    parse_allow_domains,
    parse_risk_domains,
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


def test_parse_risk_domains_falls_back_for_missing_or_empty_values():
    assert parse_risk_domains(None) == DEFAULT_RISK_DOMAINS
    assert parse_risk_domains([]) == DEFAULT_RISK_DOMAINS
    assert parse_risk_domains(" , \n ") == DEFAULT_RISK_DOMAINS


def test_parse_risk_domains_normalizes_ignores_invalid_and_dedupes():
    assert parse_risk_domains(
        [
            "  HTTPS://Focus.Example/path  ",
            "bad_domain.test",
            "sub.focus.example",
            "focus.example",
            "https://focus.example/again",
        ]
    ) == ("focus.example", "sub.focus.example")


def test_parse_risk_domains_falls_back_when_all_custom_entries_are_invalid():
    assert parse_risk_domains(["bad_domain.test", "not a url"]) == DEFAULT_RISK_DOMAINS


def test_parse_risk_domains_accepts_newline_and_comma_separated_strings():
    assert parse_risk_domains("Focus.Example\nrest.example, blocked.example") == (
        "focus.example",
        "rest.example",
        "blocked.example",
    )


def test_parse_risk_domains_can_return_empty_tuple_for_set_validation():
    assert parse_risk_domains("bad_domain.test", fallback=()) == ()


def test_load_risk_domains_reads_store_setting_or_falls_back():
    class Store:
        def get_setting(self, key, default=None):
            assert key == RISK_DOMAINS_SETTING_KEY
            del default
            return ["Focus.Example", "bad_domain.test"]

    assert load_risk_domains(Store()) == ("focus.example",)


def test_load_risk_domains_falls_back_when_store_read_fails():
    class BrokenStore:
        def get_setting(self, key, default=None):
            del key, default
            raise RuntimeError("settings unavailable")

    assert load_risk_domains(BrokenStore()) == DEFAULT_RISK_DOMAINS


def test_parse_allow_domains_missing_empty_or_malformed_returns_empty_tuple():
    assert parse_allow_domains(None) == ()
    assert parse_allow_domains([]) == ()
    assert parse_allow_domains(" , \n ") == ()
    assert parse_allow_domains({"domain": "safe.example.com"}) == ()


def test_parse_allow_domains_accepts_list_and_dedupes_order():
    assert parse_allow_domains(
        [
            " Safe.Example.Com ",
            "bad_domain.test",
            "sub.safe.example.com",
            "https://safe.example.com/path",
        ]
    ) == ("safe.example.com", "sub.safe.example.com")


def test_parse_allow_domains_accepts_comma_and_newline_separated_strings():
    assert parse_allow_domains("Safe.Example.Com, rest.example\nsafe.example.com") == (
        "safe.example.com",
        "rest.example",
    )


def test_match_allowlist_accepts_exact_and_subdomain_matches():
    exact = match_allowlist("safe.example.com", ["safe.example.com"])
    subdomain = match_allowlist("sub.safe.example.com", ["safe.example.com"])

    assert exact is not None
    assert exact.candidate_domain == "safe.example.com"
    assert exact.matched_domain == "safe.example.com"
    assert subdomain is not None
    assert subdomain.candidate_domain == "sub.safe.example.com"
    assert subdomain.matched_domain == "safe.example.com"


def test_match_allowlist_rejects_different_suffix():
    assert match_allowlist("safe.example.com.evil.test", ["safe.example.com"]) is None


def test_load_allow_domains_reads_store_setting_or_returns_empty_tuple():
    class Store:
        def get_setting(self, key, default=None):
            assert key == ALLOW_DOMAINS_SETTING_KEY
            del default
            return ["Safe.Example.Com", "bad_domain.test"]

    assert load_allow_domains(Store()) == ("safe.example.com",)


def test_load_allow_domains_returns_empty_tuple_when_store_read_fails():
    class BrokenStore:
        def get_setting(self, key, default=None):
            del key, default
            raise RuntimeError("settings unavailable")

    assert load_allow_domains(BrokenStore()) == ()
