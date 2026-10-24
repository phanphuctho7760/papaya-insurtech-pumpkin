"""Rule 7 - diagnosis-procedure mismatch: a code that is not valid for the diagnosis. Spec: diagnosis-procedure-mismatch.md."""

from catalog import Catalog
from claims import Claim
from rules.evidence import code_label, code_labels


def detect(claims: list[Claim], catalog: Catalog) -> dict[str, str]:
    flagged = {}
    for claim in claims:
        valid = catalog.valid_pairs[claim.diagnosis_code]
        invalid = [c for c in claim.procedure_codes if c not in valid]
        if not invalid:
            continue
        noun, verb = ("Procedure", "is") if len(invalid) == 1 else ("Procedures", "are")
        flagged[claim.claim_id] = (
            f"{noun} {code_labels(invalid, catalog, ', ')} {verb} not valid for diagnosis "
            f"{code_label(claim.diagnosis_code, catalog)}; valid procedures: {', '.join(sorted(valid))}"
        )
    return flagged
