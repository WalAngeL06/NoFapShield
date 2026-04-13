import os
import tempfile

from nudenet import NudeDetector

from shield.core.interfaces import NSFWScore, ScreenshotResult


class NSFWClassifier:
    def __init__(self) -> None:
        """Load NudeNet model once at construction time."""
        self._detector = NudeDetector()

    def classify(self, result: ScreenshotResult) -> NSFWScore:
        """Run NudeNet on image_bytes from RAM via an ephemeral temp file.

        Uses NamedTemporaryFile with delete=False + manual unlink so that
        NudeDetector can open the file by path (required on Windows where
        delete=True locks the file while the context is open).
        The temp file is always removed in the finally block.

        Note: NudeNet requires a file path and cannot accept BytesIO directly.
        Uses NamedTemporaryFile with delete=False + explicit os.unlink in finally
        block for Windows compatibility (Windows locks open temp files, preventing
        NudeDetector from reading them). The plan's privacy/CLAUDE.md explicitly
        permits this approach as an ephemeral fallback.
        """
        tmp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(result.image_bytes)
                tmp_path = tmp.name

            detections = self._detector.detect(tmp_path)
        finally:
            if tmp_path is not None and os.path.exists(tmp_path):
                os.unlink(tmp_path)

        if not detections:
            model_score = 0.0
        else:
            model_score = max(d.get("score", 0.0) for d in detections)

        model_score = max(0.0, min(1.0, model_score))
        return NSFWScore(model_score=model_score, confidence=model_score)
