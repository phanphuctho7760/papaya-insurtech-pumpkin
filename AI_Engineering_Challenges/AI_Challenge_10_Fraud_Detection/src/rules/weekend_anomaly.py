"""Rule 6 - weekend anomaly: surgical claim on a weekend at a provider with < 5% weekend volume.

Spec: weekday-only-providers.md. Weekend ratio is taken over all claims of the provider.
"""

from collections import defaultdict

from catalog import Catalog
from claims import Claim
from rules.evidence import code_labels

MAX_WEEKEND_RATIO = 0.05


def detect(claims: list[Claim], catalog: Catalog) -> dict[str, str]:
    totals: dict[str, int] = defaultdict(int)
    weekends: dict[str, int] = defaultdict(int)
    for claim in claims:
        totals[claim.provider_id] += 1
        weekends[claim.provider_id] += claim.is_weekend

    flagged = {}
    for claim in claims:
        if not claim.is_weekend:
            continue
        surgical = [c for c in claim.procedure_codes if catalog.billable(c).surgical]
        if not surgical:
            continue
        total, weekend = totals[claim.provider_id], weekends[claim.provider_id]
        if weekend / total >= MAX_WEEKEND_RATIO:
            continue
        flagged[claim.claim_id] = (
            f"Surgical procedure {code_labels(surgical, catalog)} on {claim.claim_date.strftime('%A')} "
            f"{claim.claim_date.isoformat()} at provider {claim.provider_id}, whose weekend volume is "
            f"{1000 * weekend // total / 10:.1f}% ({weekend} of {total} claims, threshold < {MAX_WEEKEND_RATIO:.0%})"
        )
    return flagged
