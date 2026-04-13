# Detection Agent — Shield Project

## Your single responsibility
Implement `src/shield/detection/` module: RAM-only screenshot capture, NudeNet NSFW classification, hybrid score calculation.

## Working directory
Y:/NoFapShield

## Files you must create
- `src/shield/detection/screenshot.py`   — mss capture, RAM only
- `src/shield/detection/classifier.py`   — NudeNet wrapper
- `src/shield/detection/scorer.py`       — hybrid score formula
- `src/shield/detection/__init__.py`     — exports DetectionService
- `tests/test_detection/test_screenshot.py`
- `tests/test_detection/test_scorer.py`
- `tests/test_detection/test_classifier.py`

## Files you must NOT touch
- Anything outside `src/shield/detection/` and `tests/test_detection/`
- `src/shield/core/interfaces.py` — read it, never edit it

## Interface contract
Read `src/shield/core/interfaces.py` carefully before implementing. Key types:

```python
from shield.core.interfaces import (
    ScreenshotResult, NSFWScore, DomainScore, HybridScore, TriggerSource
)
```

**IMPORTANT:** `HybridScore.nsfw` is `Optional[NSFWScore]` and is placed LAST in the constructor (it has a default of None). When creating a HybridScore for a screenshot event, pass nsfw explicitly:
```python
HybridScore(
    final_score=...,
    domain=domain_score,
    url_score=url_score,
    source=TriggerSource.SCREENSHOT,
    computed_at=datetime.utcnow(),
    nsfw=nsfw_score,  # required for SCREENSHOT, will raise if None
)
```

## API to implement
```python
from datetime import datetime
from shield.core.interfaces import ScreenshotResult, NSFWScore, HybridScore, DomainScore, TriggerSource

class ScreenshotCapture:
    def capture(self) -> ScreenshotResult:
        """Uses mss to capture primary monitor.
        image_bytes = PNG bytes in RAM (BytesIO), never written to disk.
        captured_at = datetime.utcnow()
        """
        ...

class NSFWClassifier:
    def __init__(self) -> None:
        """Loads NudeNet model (NudeDetector)"""
        ...
    
    def classify(self, result: ScreenshotResult) -> NSFWScore:
        """Runs NudeNet on image_bytes from RAM.
        model_score: max score from NudeNet detections, 0.0 if none detected
        confidence: same as model_score
        Uses BytesIO buffer — never writes to disk.
        """
        ...

class HybridScorer:
    def score(
        self,
        nsfw: NSFWScore,
        domain: DomainScore,
        url_score: float,
        source: TriggerSource,
    ) -> HybridScore:
        """final_score = 0.6 * nsfw.model_score + 0.3 * domain.match_score + 0.1 * url_score
        All inputs clamped to [0.0, 1.0] before formula.
        final_score clamped to [0.0, 1.0] after formula.
        """
        ...

class DetectionService:
    def __init__(self) -> None: ...
    
    def run_once(self, domain_score: DomainScore, url_score: float) -> HybridScore:
        """Capture screenshot → classify → score → return HybridScore.
        domain_score and url_score are passed in from the orchestrator.
        """
        ...
```

## Privacy constraint — CRITICAL
- `ScreenshotResult.image_bytes` is bytes in RAM only
- No method may call `open()` for writing or write to disk
- Pass image bytes via BytesIO, NOT a file path to NudeNet:
  ```python
  import io
  from PIL import Image
  buf = io.BytesIO(result.image_bytes)
  # use buf with NudeNet, never a file path
  ```

## NudeNet usage
NudeNet's NudeDetector works like this:
```python
from nudenet import NudeDetector
detector = NudeDetector()
# To detect from bytes without writing to disk:
# Option 1: save to a temp file (acceptable IF using tempfile with delete=True)
# Option 2: use NudeDetector().detect_batch([image_path]) — requires file path
# Use tempfile.NamedTemporaryFile to avoid permanent disk writes if needed
```
Note: Some versions of NudeNet may require a file path. If BytesIO is not supported,
use `tempfile.NamedTemporaryFile(suffix='.png', delete=True)` — this creates a temp
file that auto-deletes when closed. This is acceptable as it is ephemeral.

## Testing rules
- Mock `mss.mss()` — return a dummy screenshot dict
- Mock `NudeDetector` — avoid loading actual model
- test_scorer.py MUST include these exact tests:
  ```python
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
  ```
- test_screenshot.py MUST verify no disk writes (use tmp_path mock)

## Success criteria
```bash
python -m pytest tests/test_detection/ -v --timeout=30
```
All tests pass.

## Boundary
Do not implement anything outside src/shield/detection/. Do not import from db, privacy, dns_proxy, or system modules.
