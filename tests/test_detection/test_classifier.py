"""Tests for NSFWClassifier — NudeDetector is mocked to avoid model loading."""
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from shield.core.interfaces import NSFWScore, ScreenshotResult
from shield.detection.classifier import NSFWClassifier


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _result(image_bytes: bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50) -> ScreenshotResult:
    return ScreenshotResult(image_bytes=image_bytes, captured_at=datetime.utcnow())


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@patch("shield.detection.classifier.NudeDetector")
def test_classify_no_detections_returns_zero(mock_cls):
    mock_cls.return_value.detect.return_value = []

    result = NSFWClassifier().classify(_result())

    assert isinstance(result, NSFWScore)
    assert result.model_score == 0.0
    assert result.confidence == 0.0


@patch("shield.detection.classifier.NudeDetector")
def test_classify_picks_max_score(mock_cls):
    mock_cls.return_value.detect.return_value = [
        {"class": "EXPOSED_BREAST_F", "score": 0.72},
        {"class": "EXPOSED_GENITALIA_F", "score": 0.91},
        {"class": "EXPOSED_BUTTOCKS", "score": 0.45},
    ]

    result = NSFWClassifier().classify(_result())

    assert abs(result.model_score - 0.91) < 1e-6
    assert abs(result.confidence - 0.91) < 1e-6


@patch("shield.detection.classifier.NudeDetector")
def test_classify_score_clamped_above_one(mock_cls):
    mock_cls.return_value.detect.return_value = [
        {"class": "EXPOSED_BREAST_F", "score": 1.5},
    ]

    result = NSFWClassifier().classify(_result())

    assert result.model_score <= 1.0
    assert result.confidence <= 1.0


@patch("shield.detection.classifier.NudeDetector")
def test_classify_score_clamped_below_zero(mock_cls):
    mock_cls.return_value.detect.return_value = [
        {"class": "SAFE", "score": -0.3},
    ]

    result = NSFWClassifier().classify(_result())

    assert result.model_score >= 0.0
    assert result.confidence >= 0.0


@patch("shield.detection.classifier.NudeDetector")
def test_classify_returns_nsfw_score_instance(mock_cls):
    mock_cls.return_value.detect.return_value = [{"class": "EXPOSED_BREAST_F", "score": 0.6}]

    result = NSFWClassifier().classify(_result())

    assert isinstance(result, NSFWScore)
