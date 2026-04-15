"""Tests for ScreenshotCapture — verifies RAM-only operation and correct return type."""
from datetime import datetime
from unittest.mock import MagicMock, patch

from shield.core.interfaces import ScreenshotResult
from shield.detection.screenshot import ScreenshotCapture


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_to_png(data, size, /, *, level=6, output=None):
    """Return minimal PNG bytes when output is None (new mss ≥10 API)."""
    if output is None:
        return b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
    # output is a path — write and return None (legacy path, not used by capture)
    with open(output, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)
    return None


def _make_mss_ctx():
    """Return a mock context manager that looks like mss.mss()."""
    grab_result = MagicMock()
    grab_result.rgb = b"\x00" * 30_000
    grab_result.size = (100, 100)

    sct = MagicMock()
    sct.monitors = [None, {"top": 0, "left": 0, "width": 100, "height": 100}]
    sct.grab.return_value = grab_result

    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=sct)
    ctx.__exit__ = MagicMock(return_value=False)
    return ctx


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@patch("mss.tools.to_png", side_effect=_fake_to_png)
@patch("mss.mss")
def test_capture_returns_screenshot_result(mock_mss, mock_to_png):
    mock_mss.return_value = _make_mss_ctx()

    result = ScreenshotCapture().capture()

    assert isinstance(result, ScreenshotResult)
    assert isinstance(result.image_bytes, bytes)
    assert len(result.image_bytes) > 0
    assert isinstance(result.captured_at, datetime)


@patch("mss.tools.to_png", side_effect=_fake_to_png)
@patch("mss.mss")
def test_capture_image_bytes_non_empty(mock_mss, mock_to_png):
    mock_mss.return_value = _make_mss_ctx()

    result = ScreenshotCapture().capture()

    # Should contain PNG signature bytes we injected
    assert result.image_bytes.startswith(b"\x89PNG")


@patch("mss.tools.to_png", side_effect=_fake_to_png)
@patch("mss.mss")
def test_capture_no_disk_writes(mock_mss, mock_to_png, tmp_path):
    """ScreenshotCapture must never open a file for writing."""
    mock_mss.return_value = _make_mss_ctx()

    files_before = set(tmp_path.iterdir())

    # Wrap builtins.open to detect any write-mode calls
    import builtins
    original_open = builtins.open
    write_paths: list[str] = []

    def tracking_open(file, mode="r", *args, **kwargs):
        if isinstance(mode, str) and any(c in mode for c in ("w", "a", "x")):
            write_paths.append(str(file))
        return original_open(file, mode, *args, **kwargs)

    with patch("builtins.open", side_effect=tracking_open):
        result = ScreenshotCapture().capture()

    assert isinstance(result.image_bytes, bytes)
    # No files should have been written anywhere under tmp_path
    assert set(tmp_path.iterdir()) == files_before
    # ScreenshotCapture itself must not call open() in write mode
    assert write_paths == [], f"Unexpected write-mode open() calls: {write_paths}"
