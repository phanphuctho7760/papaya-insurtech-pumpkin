"""Rule 1 - duplicate claim: same member + provider + date + diagnosis. Spec: duplicate-and-rapid-resubmission.md."""

from collections import defaultdict

from catalog import Catalog
from claims import Claim
from rules.evidence import code_label

MIN_GROUP_SIZE = 2


def detect(claims: list[Claim], catalog: Catalog) -> dict[str, str]:
    groups: dict[tuple, list[Claim]] = defaultdict(list)
    for claim in claims:
        groups[(claim.member_id, claim.provider_id, claim.claim_date, claim.diagnosis_code)].append(claim)

    flagged = {}
    for group in groups.values():
        if len(group) < MIN_GROUP_SIZE:
            continue
        for claim in group:
            others = ", ".join(c.claim_id for c in group if c is not claim)
            flagged[claim.claim_id] = (
                f"Duplicate of {others}: same member {claim.member_id}, provider {claim.provider_id}, "
                f"date {claim.claim_date.isoformat()}, diagnosis {code_label(claim.diagnosis_code, catalog)} "
                f"- {len(group)} claims share this key"
            )
    return flagged
