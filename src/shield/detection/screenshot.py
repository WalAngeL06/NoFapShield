"""Screenshot capture with GPU-accelerated content support.

Capture strategy (tried in order):
1. dxcam  — DXGI Desktop Duplication API; captures hardware-accelerated content
             (GPU-rendered video, browsers, games). Requires Windows 8+.
2. mss    — GDI-layer fallback; reliable for standard windows (Paint, Explorer),
             but misses hardware-accelerated video content.

DRM-protected streams (Netflix, Prime in Edge) block both APIs by design.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import mss
import mss.tools
import numpy as np

from shield.core.interfaces import ScreenshotResult

logger = logging.getLogger(__name__)

# Lazy singleton — dxcam.create() is expensive; reuse across captures.
_dxcam_camera = None
_dxcam_available: bool | None = None  # None = not yet probed


def _try_dxcam() -> bytes | None:
    """Attempt capture via dxcam. Returns PNG bytes or None on failure."""
    global _dxcam_camera, _dxcam_available

    if _dxcam_available is False:
        return None

    try:
        import dxcam  # optional dependency

        if _dxcam_camera is None:
            _dxcam_camera = dxcam.create(output_color="BGR")
            _dxcam_available = True

        frame = _dxcam_camera.grab()  # returns np.ndarray (H, W, 3) BGR or None
        if frame is None:
            return None

        import cv2
        ok, buf = cv2.imencode(".png", frame)
        return bytes(buf) if ok else None

    except Exception as exc:
        if _dxcam_available is None:
            logger.info("dxcam unavailable, falling back to mss: %s", exc)
        _dxcam_available = False
        _dxcam_camera = None
        return None


def _capture_mss() -> bytes:
    """Capture via mss (GDI layer). Always available."""
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        shot = sct.grab(monitor)
        return mss.tools.to_png(shot.rgb, shot.size)


class ScreenshotCapture:
    def capture(self) -> ScreenshotResult:
        """Capture primary monitor.

        Tries dxcam first (GPU-accelerated content), falls back to mss.
        Image bytes are PNG data held in RAM — never written to disk here.
        """
        image_bytes = _try_dxcam() or _capture_mss()
        return ScreenshotResult(
            image_bytes=image_bytes,
            captured_at=datetime.now(timezone.utc),
        )
