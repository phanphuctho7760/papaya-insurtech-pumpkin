"""Score claims: run the 8 rules, attach weights, compute risk_score 0-100, rank. Spec: scoring.md."""

import json
import math
from pathlib import Path

from catalog import Catalog
from claims import Claim
from rule_names import ALL_RULES
from rules import RULES

SATURATION_K = 0.25
OUTPUT_NAME = "scored_output.json"


def risk_score(total: int) -> int:
    """100 x (1 - e^(-0.25 x total)). For total 0-27 no value lands on .5, so banker's rounding never matters."""
    return round(100 * (1 - math.exp(-SATURATION_K * total)))


def sort_flags(flags: list[dict]) -> list[dict]:
    """Severity descending; ties keep ALL_RULES order."""
    return sorted(flags, key=lambda f: (-f["severity"], ALL_RULES.index(f["rule"])))


def rank(results: list[dict]) -> list[dict]:
    """risk_score descending, then more flags first, then claim_id ascending."""
    return sorted(results, key=lambda r: (-r["risk_score"], -len(r["flags"]), r["claim_id"]))


def score_claims(claims: list[Claim], catalog: Catalog, weights: dict[str, int]) -> list[dict]:
    """Return every claim as {claim_id, risk_score, flags}, ranked. Unflagged claims get score 0 and no flags."""
    flags_by_claim: dict[str, list[dict]] = {c.claim_id: [] for c in claims}
    for rule in ALL_RULES:
        for claim_id, evidence in RULES[rule](claims, catalog).items():
            flags_by_claim[claim_id].append({"rule": rule, "severity": weights[rule], "evidence": evidence})

    results = []
    for claim in claims:
        flags = sort_flags(flags_by_claim[claim.claim_id])
        total = sum(f["severity"] for f in flags)
        results.append({"claim_id": claim.claim_id, "risk_score": risk_score(total), "flags": flags})
    return rank(results)


def write_scored(results: list[dict], out_dir: Path) -> Path:
    """Write the ranked list to out_dir/scored_output.json (UTF-8, indent 2, not ASCII-escaped)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / OUTPUT_NAME
    path.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
