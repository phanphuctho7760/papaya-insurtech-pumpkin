"""Rule 2 - rapid re-submission: same member + same diagnosis within 7 days. Spec: duplicate-and-rapid-resubmission.md.

A pair sharing the duplicate key (same provider and same date) is left to the duplicate rule.
A claim in several pairs gets one evidence string listing every related claim.
"""

from collections import defaultdict

from catalog import Catalog
from claims import Claim
from rules.evidence import code_label, days

WINDOW_DAYS = 7


def detect(claims: list[Claim], catalog: Catalog) -> dict[str, str]:
    groups: dict[tuple, list[Claim]] = defaultdict(list)
    for claim in claims:
        groups[(claim.member_id, claim.diagnosis_code)].append(claim)

    related: dict[str, list[tuple[Claim, Claim]]] = defaultdict(list)  # claim_id -> [(earlier, later)] pairs
    for group in groups.values():
        group.sort(key=lambda c: (c.claim_date, c.claim_id))
        for i, earlier in enumerate(group):
            for later in group[i + 1:]:
                if (later.claim_date - earlier.claim_date).days > WINDOW_DAYS:
                    break
                if earlier.provider_id == later.provider_id and earlier.claim_date == later.claim_date:
                    continue  # duplicate key, handled by rule 1
                related[earlier.claim_id].append((earlier, later))
                related[later.claim_id].append((earlier, later))

    by_id = {c.claim_id: c for c in claims}
    flagged = {}
    for claim_id, pairs in related.items():
        claim = by_id[claim_id]
        clauses = [_clause(claim, earlier, later) for earlier, later in pairs]
        flagged[claim_id] = (
            "; ".join(clauses) + f" for the same member {claim.member_id} and diagnosis "
            f"{code_label(claim.diagnosis_code, catalog)} - window: {days(WINDOW_DAYS)}"
        )
    return flagged


def _clause(claim: Claim, earlier: Claim, later: Claim) -> str:
    if earlier.claim_date == later.claim_date:
        other = later if claim is earlier else earlier
        return f"Submitted on the same day as {other.claim_id} at another provider {other.provider_id}"
    gap = (later.claim_date - earlier.claim_date).days
    if claim is later:
        return f"Re-submitted {days(gap)} after {earlier.claim_id} ({earlier.claim_date.isoformat()})"
    return f"Followed {days(gap)} later by {later.claim_id} ({later.claim_date.isoformat()})"
