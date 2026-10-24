# Diagnosis-procedure mismatch

Terms (diagnosis-procedure mismatch, valid diagnosis-procedure pair): see `glossary.md`.

## Source in the brief

- Dataset: "20 diagnosis-procedure mismatches".
- Rule 7: "procedure not clinically associated with diagnosis (provide a mapping of at least 10 valid diagnosis-procedure pairs)".

## What "normal" means: the valid pairs

Every pair outside this table is a mismatch.

| Diagnosis | Valid procedures / bundles |
|---|---|
| J06.9 | P-1001, P-1002, P-1003, B-1001 |
| I10 | P-1001, P-1002, P-1003, B-1001 |
| E11.9 | P-1001, P-1002, P-1006, B-1002 |
| A09 | P-1001, P-1002, P-1005 |
| N39.0 | P-1001, P-1003 |
| J18.9 | P-1004, P-2001 |
| K35.8 | P-3001, P-3010, B-3101 |
| K80.2 | P-1005, P-3002, P-3010, B-3102 |
| S52.5 | P-3003, P-3010 |
| O80 | P-2002 |
| K02.1 | P-4001, P-4002, P-4003 |
| K04.0 | P-4002, P-4004, B-4101 |

Total: 35 pairs (the brief asks for >= 10).

The claim_type of a diagnosis (`icd-10.md`) is for reference only; a claim's claim_type comes from its procedure / bundle code. So a valid pair can cross claim types: `K80.2 - P-1005` (outpatient abdominal ultrasound for a gallstone patient) and `J18.9 - P-1004` (outpatient chest X-ray for a pneumonia patient) produce OUTPATIENT claims.

Constraint: a valid diagnosis of a bundle must be valid for **every** component of that bundle, otherwise an unbundled claim would also trip the mismatch rule. That is why the pairs `J06.9 - P-1003`, `I10 - P-1003` (a general check-up includes a urinalysis) and `E11.9 - P-1002` (diabetes follow-up includes a complete blood count) exist; added on 2026-10-24 when checking the components of B-1001 and B-1002.

## Fraud generation

- Mismatch claim: pick a diagnosis, then a procedure outside that diagnosis's valid list; amount based on the procedure's standard price (so the claim does not also trip upcoding). The procedure has the same claim_type; bundle codes are not used.
