# Upcoding

Terms (upcoding, mean, SD, masking, leave-one-out): see `glossary.md`.

## Source in the brief

- Dataset: "30 upcoded claims (amount > 2 standard deviations above mean for that procedure)".
- Rule 3: "amount > 2 standard deviations above mean for that procedure code".

## What "normal" means

- Every procedure / bundle has a standard price (see `catalog.md`).
- Legitimate claim: amount = standard price x a log-normal factor, variation about 15%.
- Legitimate claims have exactly 1 code, so "mean for that procedure" = the mean amount of the claims with that code.

## Note: "2 SD" is not "2 times"

- Rule threshold = mean + 2 x SD. With 15% variation, SD is about 15% of the mean => threshold about 1.3 x the mean.
- Dental filling example: mean 400,000, SD about 60,000 => threshold about 520,000.

## Fraud generation

- Upcoded claim: amount = standard price x a factor of 1.6-2.5 (above the 2 SD threshold, still realistic).
- Upcoded claims are spread over codes with >= 60 single-code claims, at most 2 upcoded claims per code, never P-1003 (reserved for clustering). Reason: a code with only 30 claims that holds 2 upcoded claims can have an SD of about 0.3 x the mean, pushing the threshold to about 1.65 x the mean => a 1.6x upcoded claim is missed (masking).

## How mean / SD are computed (settled in B1)

- Mean and SD are computed over **every claim with the same code**, upcoded claims included. This keeps the brief's wording ("mean for that procedure code").
- Known consequence (masking): upcoded claims raise the mean and SD => the mean + 2 SD threshold goes up and some upcoded claims may not exceed it => lower recall.
- SD = **population SD** (`statistics.pstdev`), because the data is every claim of the code, not a sample (settled 2026-10-24; see `glossary.md`). Flag when amount `>` mean + 2 x SD (the brief says "> 2 standard deviations"). SD = 0 => no flag. The evidence states `(amount - mean) / SD` with 1 decimal.
- Handling: measure the recall of the upcoding rule on the dataset first. Switch to excluding the claim under review (leave-one-out) only if the target is missed. Record the measurement and the decision in the writeup.

## Minimum number of claims

- Codes with < 10 claims: **not checked for upcoding** (not enough history to conclude an amount is inflated).
- The generator creates >= 30 claims per code so every code is checked.

## Claims with several codes (settled)

- Only claims with **exactly 1 code** take part in the mean / SD and are checked for upcoding.
- Claims with several codes only appear as unbundling fraud; their amount is a sum of individual prices, so it cannot be compared with the "mean for that procedure code".
- The minimum claim counts (10 / 30) are counted over single-code claims.
