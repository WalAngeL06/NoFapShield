from datetime import datetime, timezone

from shield.core.interfaces import DomainScore, HybridScore, NSFWScore, TriggerSource


class HybridScorer:
    def score(
        self,
        nsfw: NSFWScore,
        domain: DomainScore,
        url_score: float,
        source: TriggerSource,
    ) -> HybridScore:
        """Compute hybrid score.

        formula: final_score = 0.6 * nsfw + 0.3 * domain + 0.1 * url
        All three inputs are clamped to [0.0, 1.0] before the formula.
        final_score is clamped to [0.0, 1.0] after.
        """
        nsfw_val = max(0.0, min(1.0, nsfw.model_score))
        domain_val = max(0.0, min(1.0, domain.match_score))
        url_val = max(0.0, min(1.0, url_score))

        final = 0.6 * nsfw_val + 0.3 * domain_val + 0.1 * url_val
        final = max(0.0, min(1.0, final))

        return HybridScore(
            final_score=final,
            domain=domain,
            url_score=url_score,
            source=source,
            computed_at=datetime.now(timezone.utc),
            nsfw=nsfw,
        )
