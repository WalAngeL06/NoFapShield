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


@patch("shield.detection.classifier.os.unlink")
@patch("shield.detection.classifier.NudeDetector")
def test_temp_file_is_always_unlinked(mock_cls, mock_unlink):
    """Verifies temp file cleanup runs in the normal (success) path."""
    mock_cls.return_value.detect.return_value = []
    # get a valid ScreenshotResult from the existing test helper or create one inline
    from datetime import datetime
    result = ScreenshotResult(image_bytes=b"\x89PNG\r\n", captured_at=datetime.utcnow())
    NSFWClassifier().classify(result)
    assert mock_unlink.call_count == 1

@patch("shield.detection.classifier.os.unlink")
@patch("shield.detection.classifier.NudeDetector")
def test_temp_file_unlinked_on_exception(mock_cls, mock_unlink):
    """Verifies temp file cleanup runs even when NudeNet raises."""
    mock_cls.return_value.detect.side_effect = RuntimeError("model crash")
    from datetime import datetime
    result = ScreenshotResult(image_bytes=b"\x89PNG\r\n", captured_at=datetime.utcnow())
    with pytest.raises(RuntimeError):
        NSFWClassifier().classify(result)
    assert mock_unlink.call_count == 1
