"""Rule 8 - amount clustering: amount within 5% below the 50,000 auto-approval threshold. Spec: amount-clustering.md."""

from catalog import Catalog
from claims import Claim
from rules.evidence import vnd

AUTO_APPROVAL_THRESHOLD = 50_000
BAND_LOW = 47_500  # 5% below the threshold
BAND_HIGH = AUTO_APPROVAL_THRESHOLD - 1


def detect(claims: list[Claim], catalog: Catalog) -> dict[str, str]:
    return {
        c.claim_id: (
            f"Amount {vnd(c.submitted_amount)} is {100 * c.submitted_amount // AUTO_APPROVAL_THRESHOLD}% of the "
            f"{vnd(AUTO_APPROVAL_THRESHOLD)} auto-approval threshold (band {BAND_LOW:,}-{BAND_HIGH:,})"
        )
        for c in claims
        if BAND_LOW <= c.submitted_amount <= BAND_HIGH
    }
