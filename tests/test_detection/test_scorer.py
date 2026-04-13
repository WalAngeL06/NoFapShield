"""Tests for HybridScorer — no mocking needed, pure logic."""
from datetime import datetime

import pytest

from shield.core.interfaces import DomainScore, HybridScore, NSFWScore, TriggerSource
from shield.detection.scorer import HybridScorer


# ---------------------------------------------------------------------------
# Required exact tests (specified in agent prompt)
# ---------------------------------------------------------------------------

def test_formula_full_score():
    scorer = HybridScorer()
    nsfw = NSFWScore(model_score=1.0, confidence=1.0)
    domain = DomainScore(domain="test.com", match_score=1.0)
    result = scorer.score(nsfw, domain, url_score=1.0, source=TriggerSource.SCREENSHOT)
    assert abs(result.final_score - 1.0) < 0.001


def test_formula_partial_score():
    scorer = HybridScorer()
    nsfw = NSFWScore(model_score=0.5, confidence=0.5)
    domain = DomainScore(domain="test.com", match_score=0.0)
    result = scorer.score(nsfw, domain, url_score=0.0, source=TriggerSource.SCREENSHOT)
    assert abs(result.final_score - 0.3) < 0.001  # 0.6 * 0.5


def test_score_clamped_to_one():
    scorer = HybridScorer()
    nsfw = NSFWScore(model_score=1.0, confidence=1.0)
    domain = DomainScore(domain="x.com", match_score=1.0)
    result = scorer.score(nsfw, domain, url_score=1.0, source=TriggerSource.SCREENSHOT)
    assert result.final_score <= 1.0


# ---------------------------------------------------------------------------
# Additional coverage
# ---------------------------------------------------------------------------

def test_formula_domain_only():
    scorer = HybridScorer()
    nsfw = NSFWScore(model_score=0.0, confidence=0.0)
    domain = DomainScore(domain="bad.com", match_score=1.0)
    result = scorer.score(nsfw, domain, url_score=0.0, source=TriggerSource.SCREENSHOT)
    assert abs(result.final_score - 0.3) < 0.001


def test_formula_url_only():
    scorer = HybridScorer()
    nsfw = NSFWScore(model_score=0.0, confidence=0.0)
    domain = DomainScore(domain="ok.com", match_score=0.0)
    result = scorer.score(nsfw, domain, url_score=1.0, source=TriggerSource.SCREENSHOT)
    assert abs(result.final_score - 0.1) < 0.001


def test_score_zero_inputs():
    scorer = HybridScorer()
    nsfw = NSFWScore(model_score=0.0, confidence=0.0)
    domain = DomainScore(domain="clean.com", match_score=0.0)
    result = scorer.score(nsfw, domain, url_score=0.0, source=TriggerSource.SCREENSHOT)
    assert result.final_score == 0.0


def test_returns_hybrid_score_instance():
    scorer = HybridScorer()
    nsfw = NSFWScore(model_score=0.4, confidence=0.4)
    domain = DomainScore(domain="example.com", match_score=0.5)
    result = scorer.score(nsfw, domain, url_score=0.2, source=TriggerSource.SCREENSHOT)
    assert isinstance(result, HybridScore)


def test_nsfw_attached_to_result():
    scorer = HybridScorer()
    nsfw = NSFWScore(model_score=0.7, confidence=0.7)
    domain = DomainScore(domain="example.com", match_score=0.0)
    result = scorer.score(nsfw, domain, url_score=0.0, source=TriggerSource.SCREENSHOT)
    assert result.nsfw is nsfw


def test_source_screenshot_requires_nsfw():
    """HybridScore.__post_init__ raises if nsfw is None for SCREENSHOT source."""
    with pytest.raises(ValueError, match="nsfw must be provided"):
        HybridScore(
            final_score=0.5,
            domain=DomainScore(domain="x.com", match_score=0.5),
            url_score=0.5,
            source=TriggerSource.SCREENSHOT,
            computed_at=datetime.utcnow(),
            nsfw=None,
        )


def test_computed_at_is_datetime():
    scorer = HybridScorer()
    nsfw = NSFWScore(model_score=0.0, confidence=0.0)
    domain = DomainScore(domain="example.com", match_score=0.0)
    result = scorer.score(nsfw, domain, url_score=0.0, source=TriggerSource.SCREENSHOT)
    assert isinstance(result.computed_at, datetime)
