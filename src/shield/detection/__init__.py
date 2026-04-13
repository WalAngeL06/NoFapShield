from shield.core.interfaces import DomainScore, HybridScore, TriggerSource
from shield.detection.classifier import NSFWClassifier
from shield.detection.scorer import HybridScorer
from shield.detection.screenshot import ScreenshotCapture

__all__ = ["DetectionService"]


class DetectionService:
    def __init__(self) -> None:
        self._capture = ScreenshotCapture()
        self._classifier = NSFWClassifier()
        self._scorer = HybridScorer()

    def run_once(self, domain_score: DomainScore, url_score: float) -> HybridScore:
        """Capture → classify → score. Returns a HybridScore."""
        screenshot = self._capture.capture()
        nsfw_score = self._classifier.classify(screenshot)
        return self._scorer.score(
            nsfw_score,
            domain_score,
            url_score,
            source=TriggerSource.SCREENSHOT,
        )
