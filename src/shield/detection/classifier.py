"""NSFW classifier using NudeNet.

Full-screen screenshots shrink each thumbnail to ~33 px at NudeNet's 320-px
inference resolution — too small to detect.  We split the frame into a 3×3
grid of overlapping tiles and run the model on each tile separately.  The
final score is the maximum detection score across all tiles.
"""
from __future__ import annotations

import os
import tempfile

import cv2
import numpy as np

from nudenet import NudeDetector

from shield.core.interfaces import NSFWScore, ScreenshotResult

# Tiles: 3 columns × 3 rows = 9 regions.  Each tile covers ~1/3 of the screen
# (640×400 on 1920×1200), which maps to ~107×133 px inside NudeNet's 320-px
# window — well above the ~40-px detection floor.
_GRID_COLS = 3
_GRID_ROWS = 3


def _png_bytes_to_bgr(image_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(image_bytes, np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def _score_array(detector: NudeDetector, img_bgr: np.ndarray) -> float:
    """Write *img_bgr* to a temp file, run NudeNet, return max score."""
    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            cv2.imwrite(tmp.name, img_bgr)
            tmp_path = tmp.name
        detections = detector.detect(tmp_path)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    if not detections:
        return 0.0
    return max(0.0, min(1.0, max(d.get("score", 0.0) for d in detections)))


class NSFWClassifier:
    def __init__(self) -> None:
        """Load NudeNet model once at construction time."""
        self._detector = NudeDetector()

    def classify(self, result: ScreenshotResult) -> NSFWScore:
        """Run NudeNet on a 3×3 tile grid of the screenshot.

        Splitting avoids the resolution loss that makes small thumbnails
        undetectable when the full frame is squeezed to 320×320.
        Returns the highest score found across all tiles.
        """
        img = _png_bytes_to_bgr(result.image_bytes)
        h, w = img.shape[:2]

        best = 0.0
        for row in range(_GRID_ROWS):
            for col in range(_GRID_COLS):
                y0 = row * h // _GRID_ROWS
                y1 = (row + 1) * h // _GRID_ROWS
                x0 = col * w // _GRID_COLS
                x1 = (col + 1) * w // _GRID_COLS
                tile = img[y0:y1, x0:x1]
                score = _score_array(self._detector, tile)
                if score > best:
                    best = score

        model_score = best
        return NSFWScore(model_score=model_score, confidence=model_score)
