"""Phase 4: build the full dataset, assign claim IDs, write the CSV files and the generation summary.

File formats: docs/decisions/dataset-format.md.
"""

import csv
import json
import random
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from catalog import load_catalog
from claims import CLAIMS_COLUMNS
from generator.fraud import inject_fraud
from generator.legit import generate_legit_claims
from generator.models import GeneratedClaim, Provider, load_providers, pick_weekday_only

DEFAULT_SEED = 2024
GROUND_TRUTH_COLUMNS = ["claim_id", "is_fraud", "fraud_pattern"]


@dataclass(frozen=True)
class Dataset:
    seed: int
    claims: list[tuple[str, GeneratedClaim]]  # (claim_id, claim), ordered by claim_id
    weekday_only: list[Provider]
    phantom_provider: Provider
    phantom_date: str


def build_dataset(seed: int = DEFAULT_SEED) -> Dataset:
    rng = random.Random(seed)
    catalog, providers = load_catalog(), load_providers()
    weekday_only = pick_weekday_only(rng, providers)
    legit = generate_legit_claims(rng, catalog, providers, weekday_only)
    fraud = inject_fraud(rng, catalog, weekday_only, legit)

    # Sort by date with a random tie-break, then number: fraud claims spread over the whole ID
    # range instead of sitting at the end where they were generated.
    claims = legit + fraud.claims
    rng.shuffle(claims)
    claims.sort(key=lambda c: c.claim_date)  # stable sort keeps the shuffled order within a day
    numbered = [(f"CLM-{i:05d}", claim) for i, claim in enumerate(claims, 1)]
    return Dataset(seed, numbered, weekday_only, fraud.phantom_provider, fraud.phantom_date.isoformat())


def write_dataset(dataset: Dataset, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "claims.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)  # default dialect: comma, CRLF line endings, minimal quoting (RFC 4180)
        writer.writerow(CLAIMS_COLUMNS)
        for claim_id, c in dataset.claims:
            writer.writerow([
                claim_id, c.member_id, c.provider.id, c.provider.name, c.claim_date.isoformat(), c.claim_type,
                c.diagnosis_code, "|".join(c.procedure_codes), c.submitted_amount, int(c.is_weekend),
            ])

    with open(out_dir / "ground_truth.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(GROUND_TRUTH_COLUMNS)
        for claim_id, c in dataset.claims:
            writer.writerow([claim_id, int(c.fraud_pattern is not None), c.fraud_pattern or ""])

    summary_path = out_dir / "generation_summary.json"
    summary_path.write_text(json.dumps(summary(dataset), indent=2) + "\n", encoding="utf-8")


def summary(dataset: Dataset) -> dict:
    claims = [c for _, c in dataset.claims]
    phantom_count = sum(1 for c in claims
                        if c.provider.id == dataset.phantom_provider.id and c.claim_date.isoformat() == dataset.phantom_date)
    return {
        "seed": dataset.seed,
        "total_claims": len(claims),
        "fraud_claims": sum(1 for c in claims if c.fraud_pattern),
        "claims_per_pattern": dict(sorted(Counter(c.fraud_pattern for c in claims if c.fraud_pattern).items())),
        "weekday_only_providers": [{"provider_id": p.id, "provider_name": p.name} for p in dataset.weekday_only],
        "phantom_provider_day": {
            "provider_id": dataset.phantom_provider.id,
            "provider_name": dataset.phantom_provider.name,
            "claim_date": dataset.phantom_date,
            "claims": phantom_count,
        },
        "single_code_claims_per_code": dict(sorted(
            Counter(c.procedure_codes[0] for c in claims if len(c.procedure_codes) == 1).items())),
        "multi_code_claims": sum(1 for c in claims if len(c.procedure_codes) > 1),
    }
