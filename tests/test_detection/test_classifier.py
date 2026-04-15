"""Tests for NSFWClassifier — NudeDetector is mocked to avoid model loading."""
from datetime import datetime, timezone
from unittest.mock import patch

import cv2
import numpy as np
import pytest

from shield.core.interfaces import NSFWScore, ScreenshotResult
from shield.detection.classifier import NSFWClassifier


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_png(width: int = 100, height: int = 100) -> bytes:
    """Return valid PNG bytes for a solid-colour image (cv2-decodable)."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return bytes(buf)


def _result(image_bytes: bytes | None = None) -> ScreenshotResult:
    return ScreenshotResult(
        image_bytes=image_bytes if image_bytes is not None else _make_png(),
        captured_at=datetime.now(timezone.utc),
    )


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
    """Each tile writes+unlinks a temp file — 3×3 grid = 9 calls."""
    mock_cls.return_value.detect.return_value = []
    NSFWClassifier().classify(_result())
    assert mock_unlink.call_count == 9  # one per tile


@patch("shield.detection.classifier.os.unlink")
@patch("shield.detection.classifier.NudeDetector")
def test_temp_file_unlinked_on_exception(mock_cls, mock_unlink):
    """Temp file is cleaned up even when NudeNet raises on first tile."""
    mock_cls.return_value.detect.side_effect = RuntimeError("model crash")
    with pytest.raises(RuntimeError):
        NSFWClassifier().classify(_result())
    # At least the first tile's temp file must be unlinked.
    assert mock_unlink.call_count >= 1
