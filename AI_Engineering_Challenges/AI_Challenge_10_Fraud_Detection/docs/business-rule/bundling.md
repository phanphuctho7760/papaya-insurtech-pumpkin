# Bundling and unbundling

Terms (bundle, unbundling): see `glossary.md`.

## Source in the brief

- Dataset: "25 unbundled claims (individual procedures that should be a single bundled code)".
- Rule 4: "multiple individual procedures when a bundled code exists (provide a mapping of at least 5 bundles)".

## What "normal" means

- The 5 bundles and their components: see `catalog.md`, section Bundles.
- A legitimate claim whose procedures belong to a bundle uses the bundle code (a single code).

## Rule

- Flag when the claim's `procedure_codes` contain **all** the components of a bundle.
- A claim with only some of the components: no flag.

## Fraud generation

- Unbundled claim: `procedure_codes` = every component of one bundle; amount = sum of the component prices x a variation factor.
- The diagnosis must be a valid diagnosis for that bundle (so the claim does not also trip the mismatch rule).
