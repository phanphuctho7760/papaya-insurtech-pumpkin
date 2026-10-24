"""Rule 5 - phantom billing: a provider submits more than 30 claims in one day. Spec: detection-rules.md."""

from collections import defaultdict

from catalog import Catalog
from claims import Claim

MAX_CLAIMS_PER_DAY = 30


def detect(claims: list[Claim], catalog: Catalog) -> dict[str, str]:
    per_day: dict[tuple, list[Claim]] = defaultdict(list)
    for claim in claims:
        per_day[(claim.provider_id, claim.claim_date)].append(claim)

    flagged = {}
    for (provider_id, day), group in per_day.items():
        if len(group) <= MAX_CLAIMS_PER_DAY:
            continue
        text = (
            f"Provider {provider_id} submitted {len(group)} claims on {day.isoformat()} "
            f"(threshold: more than {MAX_CLAIMS_PER_DAY} per day)"
        )
        for claim in group:
            flagged[claim.claim_id] = text
    return flagged
