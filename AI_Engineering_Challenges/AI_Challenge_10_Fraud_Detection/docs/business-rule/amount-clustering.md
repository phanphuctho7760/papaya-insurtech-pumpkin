# Amount clustering

Terms (auto-approval threshold, amount clustering, natural FP): see `glossary.md`.

## Source in the brief

- Dataset: "20 amount clustering (amounts just below the 50,000 auto-approval threshold)".
- Rule 8: "claim amounts within 5% below the 50,000 auto-approval threshold (47,500-49,999)".

## Data generation

- Procedure used for clustering: **P-1003 Urinalysis**, standard price 40,000, variation 15%.
- Clustering fraud claim: P-1003, amount in 47,500-49,999.
- Does not trip upcoding: SD about 6,000 => upcoding threshold about 52,000 > 49,999.
- Legitimate P-1003 claims can fall into the band by themselves (estimated at about 6% of P-1003 claims); this is an intentional natural FP, counted and reported in the metrics.
- Real-world evidence: the price of a urinalysis without public health insurance at one public hospital is 48,000 VND (see `catalog.md`, section Price sources), right inside the band.
