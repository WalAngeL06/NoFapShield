from datetime import datetime, timezone

import mss
import mss.tools

from shield.core.interfaces import ScreenshotResult


class ScreenshotCapture:
    def capture(self) -> ScreenshotResult:
        """Capture primary monitor; image_bytes are PNG bytes in RAM only."""
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            image_bytes = mss.tools.to_png(screenshot.rgb, screenshot.size)
        return ScreenshotResult(
            image_bytes=image_bytes,
            captured_at=datetime.now(timezone.utc),
        )
