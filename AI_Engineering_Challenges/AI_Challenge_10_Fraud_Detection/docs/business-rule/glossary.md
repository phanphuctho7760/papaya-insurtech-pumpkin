# Glossary

**Read when:** a business doc, the code or the writeup uses a term you are not sure about.
**Does not contain:** rule conditions (see `detection-rules.md`), reference data (see `catalog.md`).

Single source for the terms used in `docs/business-rule/`. Other docs link here instead of defining terms again.

## Claims and parties

| Term | Meaning |
|---|---|
| Claim | A request from a member (through a provider) for the insurer to pay for a medical service. One row of `claims.csv`. |
| Member | The insured person who received the service (`member_id`). |
| Provider | The hospital, clinic or dental clinic that delivered the service and bills it (`provider_id`). |
| Insurer / TPA | The company that pays claims / the third-party administrator that processes claims for it. |
| Claim adjuster | The person who reviews a claim by hand before it is paid. Evidence is written for this reader. |
| claim_type | `OUTPATIENT` (no overnight stay), `INPATIENT` (admitted to hospital), `DENTAL`. A claim's claim_type comes from its procedure / bundle code. |
| Diagnosis | The medical condition the member was treated for, coded in ICD-10 (`diagnosis_code`). See `icd-10.md`. |
| ICD-10 | The WHO's international classification of diseases, 10th revision. The dataset uses real ICD-10 codes. |

## Procedures and prices

| Term | Meaning |
|---|---|
| Procedure | A medical service or intervention that was performed (consultation, test, surgery...). Codes `P-xxxx`, made up for this project. |
| Surgical | A procedure (or bundle) that is a surgery. Only surgical claims are checked by the weekend rule. |
| Bundle | A group of procedures that are always done together and billed under one bundle code (`B-xxxx`), cheaper than the sum of the individual prices. |
| Standard price | The reference price of a procedure / bundle; the centre of the amount distribution of legitimate claims. |
| Variation | How far legitimate claim amounts spread around the standard price (15% => most amounts within +-15% of the standard price). Generated with a log-normal factor. |
| Valid diagnosis-procedure pair | A procedure / bundle that is clinically appropriate for a diagnosis. The list is in `diagnosis-procedure-mismatch.md`; any other pair is a mismatch. |
| Auto-approval threshold | Claims below this amount are approved automatically, without a claim adjuster. The brief uses 50,000 VND. |

## Fraud patterns

| Term | Meaning |
|---|---|
| Duplicate claim | Two or more claims with the same unique key, i.e. the same visit billed twice. |
| Unique key | `(member_id, provider_id, claim_date, diagnosis_code)`. A legitimate claim is unique on this key. |
| Rapid re-submission | Claims for the same member and the same diagnosis within 7 days of each other (pairs on the same unique key belong to duplicate instead). |
| Upcoding | Billing a higher amount (or a more expensive code) than the service actually performed. Example: a dental filling with a standard price of 400,000 billed at 900,000. |
| Unbundling | Billing the individual procedures of a bundle instead of the bundle code, to be paid more. Example: P-3001 (Laparoscopic appendectomy) + P-3010 (General anesthesia) instead of bundle B-3101. |
| Phantom billing | Billing for services that never happened. Detected as a provider submitting more than 30 claims on a single day. |
| Weekday-only provider | A hospital that never operates on weekends in the legitimate data. 10 such hospitals exist; see `weekday-only-providers.md`. |
| Weekend anomaly | A surgical claim on a Saturday / Sunday at a provider whose weekend volume is below 5%. |
| Diagnosis-procedure mismatch | A procedure that is not clinically appropriate for the diagnosis. Example: diagnosis K02.1 (Dental caries) with procedure P-3001 (Laparoscopic appendectomy). |
| Amount clustering | Amounts packed just below the auto-approval threshold (47,500-49,999 VND) to avoid manual review. |

## Statistics

| Term | Meaning |
|---|---|
| Mean | The average: sum of the values / number of values. |
| Standard deviation (SD) | How spread out values are around the mean. Most values of a roughly normal distribution lie within mean +- 2 SD, so a value above mean + 2 SD is unusual. The upcoding rule flags amounts above this threshold. |
| Population SD (`statistics.pstdev`) | SD computed with divisor n. Used when the data is the whole group being described, as in the upcoding rule, where mean / SD are computed over every single-code claim of the code in the dataset. |
| Sample SD (`statistics.stdev`) | SD computed with divisor n - 1. Used when the data is a sample and the SD of a larger population is being estimated. It is slightly larger than the population SD (under 1.2% for n >= 44). |
| Masking | Outliers inflate the mean and SD they are compared against, so the threshold rises and some outliers no longer exceed it. Lowers the recall of the upcoding rule. |
| Leave-one-out | Computing the mean / SD for a claim without that claim itself. The fallback against masking, used only if upcoding recall is too low. |
| Log-normal | A distribution whose logarithm is normal: always positive and skewed to the right. Used to generate legitimate amounts, so a few legitimate claims land above mean + 2 SD. |

## Detection output and scoring

| Term | Meaning |
|---|---|
| Rule | One of the 8 checks in `detection-rules.md`. |
| Flag | A rule's verdict that a claim is suspicious, with severity and evidence. A rule raises at most one flag per claim. |
| Evidence | The text attached to a flag: the claim's observed value, the rule's comparison value and threshold, and the related claims. See `evidence.md`. |
| Severity / weight | A configurable number 1-5 per rule, saying how strongly a flag points to fraud. See `scoring-weights.md`. |
| Risk score | 0-100 per claim, computed from the weights of the rules that flagged it. See `scoring.md`. |

## Evaluation (metrics)

Engine results are compared with the ground truth.

| Term | Meaning | Example |
|---|---|---|
| Ground truth | The correct answer: which claims really are fraud (`ground_truth.csv`). The engine never reads it. | |
| TP (True Positive) | The engine flags the claim and it **is** fraud. | An upcoded claim is caught |
| FP (False Positive) | The engine flags the claim but it is **not** fraud (a false alarm). | A legitimate urinalysis claim at 48,000 flagged by amount clustering |
| FN (False Negative) | The engine does not flag the claim but it **is** fraud (a miss). | A weekend fraud claim missed because the provider's weekend volume is above 5% |
| TN (True Negative) | The engine does not flag the claim and it is not fraud. | An ordinary legitimate claim |
| Precision | TP / (TP + FP): of the flagged claims, the share that really is fraud. | |
| Recall | TP / (TP + FN): of the fraudulent claims, the share that is caught. | The brief targets >= 70% |
| FPR (False Positive Rate) | FP / (FP + TN): of the legitimate claims, the share flagged by mistake. | The brief targets <= 20% |
| Natural FP | A legitimate claim that falls into a rule's condition by itself, not because fraud was injected. The dataset keeps natural FPs on purpose so the metrics stay honest; they are counted and reported in the metrics report. | |
