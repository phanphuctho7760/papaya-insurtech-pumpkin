"""The 8 rule names, shared by the generator (ground_truth.csv fraud_pattern) and the engine (flag "rule").

Names follow the rule titles in the brief; "upcoding" and "amount_clustering" match its example output.
"""

DUPLICATE_CLAIM = "duplicate_claim"
RAPID_RESUBMISSION = "rapid_resubmission"
UPCODING = "upcoding"
UNBUNDLING = "unbundling"
PHANTOM_BILLING = "phantom_billing"
WEEKEND_ANOMALY = "weekend_anomaly"
DIAGNOSIS_PROCEDURE_MISMATCH = "diagnosis_procedure_mismatch"
AMOUNT_CLUSTERING = "amount_clustering"

ALL_RULES = (
    DUPLICATE_CLAIM,
    RAPID_RESUBMISSION,
    UPCODING,
    UNBUNDLING,
    PHANTOM_BILLING,
    WEEKEND_ANOMALY,
    DIAGNOSIS_PROCEDURE_MISMATCH,
    AMOUNT_CLUSTERING,
)
