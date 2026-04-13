from __future__ import annotations

import io
from unittest.mock import patch, MagicMock

import pytest

from shield.dns_proxy.blocklist import BlocklistManager

SAMPLE_HOSTS = b"""
# Comment line
127.0.0.1 localhost
0.0.0.0 pornhub.com
0.0.0.0 xvideos.com
# Another comment
0.0.0.0 example-safe.com
"""


@pytest.fixture
def mock_urlopen():
    with patch("urllib.request.urlopen") as mock:
        cm = MagicMock()
        cm.__enter__ = lambda s: io.BytesIO(SAMPLE_HOSTS)
        cm.__exit__ = MagicMock(return_value=False)
        mock.return_value = cm
        yield mock


def test_blocklist_parses_correctly(mock_urlopen):
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


def test_xvideos_blocked(mock_urlopen):
    mgr = BlocklistManager()
    mgr.fetch_and_update()
    assert mgr.is_blocked("xvideos.com") is True


def test_example_safe_blocked(mock_urlopen):
    mgr = BlocklistManager()
    mgr.fetch_and_update()
    assert mgr.is_blocked("example-safe.com") is True


def test_trailing_dot_stripped(mock_urlopen):
    mgr = BlocklistManager()
    mgr.fetch_and_update()
    assert mgr.is_blocked("pornhub.com.") is True


def test_domain_score_returns_domain_name(mock_urlopen):
    mgr = BlocklistManager()
    mgr.fetch_and_update()
    score = mgr.domain_score("pornhub.com")
    assert score.domain == "pornhub.com"


def test_fetch_returns_correct_count(mock_urlopen):
    mgr = BlocklistManager()
    count = mgr.fetch_and_update()
    assert count == 3  # pornhub.com, xvideos.com, example-safe.com


def test_empty_domains_before_fetch():
    mgr = BlocklistManager()
    assert mgr.is_blocked("pornhub.com") is False


def test_comment_lines_ignored(mock_urlopen):
    mgr = BlocklistManager()
    mgr.fetch_and_update()
    assert "# Comment line" not in mgr._domains
    assert "# Another comment" not in mgr._domains


def test_zero_zero_entry_not_stored(mock_urlopen):
    mgr = BlocklistManager()
    mgr.fetch_and_update()
    assert "0.0.0.0" not in mgr._domains
