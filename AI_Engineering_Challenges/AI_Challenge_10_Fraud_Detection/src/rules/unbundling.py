"""Rule 4 - unbundling: every component of a bundle is billed separately. Spec: bundling.md."""

from catalog import Bundle, Catalog
from claims import Claim
from rules.evidence import code_label, code_labels, vnd


def detect(claims: list[Claim], catalog: Catalog) -> dict[str, str]:
    flagged = {}
    for claim in claims:
        billed = set(claim.procedure_codes)
        hits = [b for b in catalog.bundles.values() if set(b.components) <= billed]
        if not hits:
            continue
        if len(hits) == 1:
            flagged[claim.claim_id] = (
                f"Procedures {code_labels(hits[0].components, catalog)} billed separately for "
                f"{vnd(claim.submitted_amount)} instead of {_instead_of(hits[0], catalog)}"
            )
        else:  # several bundles matched: one clause per bundle, each with its own components
            clauses = "; ".join(f"{code_labels(b.components, catalog)} instead of {_instead_of(b, catalog)}" for b in hits)
            flagged[claim.claim_id] = (
                f"Billed {len(claim.procedure_codes)} separate procedures for {vnd(claim.submitted_amount)}: {clauses}"
            )
    return flagged


def _instead_of(bundle: Bundle, catalog: Catalog) -> str:
    return f"bundle {code_label(bundle.code, catalog)} at {vnd(bundle.standard_price)}"
