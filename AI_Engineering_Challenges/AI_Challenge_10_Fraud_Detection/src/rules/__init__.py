"""The 8 detection rules. RULES maps rule name -> detect(claims, catalog) -> {claim_id: evidence}, in ALL_RULES order."""

from rule_names import (
    ALL_RULES, AMOUNT_CLUSTERING, DIAGNOSIS_PROCEDURE_MISMATCH, DUPLICATE_CLAIM, PHANTOM_BILLING,
    RAPID_RESUBMISSION, UNBUNDLING, UPCODING, WEEKEND_ANOMALY,
)
from rules import (
    amount_clustering, diagnosis_procedure_mismatch, duplicate_claim, phantom_billing,
    rapid_resubmission, unbundling, upcoding, weekend_anomaly,
)

_DETECTORS = {
    DUPLICATE_CLAIM: duplicate_claim.detect,
    RAPID_RESUBMISSION: rapid_resubmission.detect,
    UPCODING: upcoding.detect,
    UNBUNDLING: unbundling.detect,
    PHANTOM_BILLING: phantom_billing.detect,
    WEEKEND_ANOMALY: weekend_anomaly.detect,
    DIAGNOSIS_PROCEDURE_MISMATCH: diagnosis_procedure_mismatch.detect,
    AMOUNT_CLUSTERING: amount_clustering.detect,
}
RULES = {name: _DETECTORS[name] for name in ALL_RULES}
