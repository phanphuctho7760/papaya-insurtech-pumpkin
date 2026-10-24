"""Rule 3 - upcoding: amount > mean + 2 SD for the same procedure code. Spec: upcoding.md.

Only single-code claims take part. Mean and SD are population values (statistics.pstdev) over every
single-code claim of the code, flagged ones included. Codes with fewer than MIN_CLAIMS claims are skipped.
"""

from collections import defaultdict
from statistics import mean, pstdev

from catalog import Catalog
from claims import Claim
from rules.evidence import code_label, vnd

SD_MULTIPLIER = 2
MIN_CLAIMS = 10


def detect(claims: list[Claim], catalog: Catalog) -> dict[str, str]:
    by_code: dict[str, list[Claim]] = defaultdict(list)
    for claim in claims:
        if len(claim.procedure_codes) == 1:
            by_code[claim.procedure_codes[0]].append(claim)

    flagged = {}
    for code, group in by_code.items():
        if len(group) < MIN_CLAIMS:
            continue
        amounts = [c.submitted_amount for c in group]
        avg, sd = mean(amounts), pstdev(amounts)
        if sd == 0:
            continue
        threshold = avg + SD_MULTIPLIER * sd
        kind = "bundle" if code in catalog.bundles else "procedure"
        for claim in group:
            if claim.submitted_amount > threshold:
                deviations = (claim.submitted_amount - avg) / sd
                flagged[claim.claim_id] = (
                    f"Submitted amount {vnd(claim.submitted_amount)} for {kind} {code_label(code, catalog)} "
                    f"is {deviations:.1f} standard deviations above the mean of {vnd(avg)} "
                    f"(threshold {vnd(threshold)}, based on {len(group)} claims)"
                )
    return flagged
