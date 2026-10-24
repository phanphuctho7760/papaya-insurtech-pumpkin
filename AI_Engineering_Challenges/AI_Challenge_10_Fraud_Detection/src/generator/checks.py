"""Phase 5: structural checks on the written dataset files.

Reads the files back from disk, so format problems in the CSV writer are caught too.
These are structure checks only; checking that each rule flags its own pattern belongs to the
engine's integration test (#03), so no rule logic is duplicated here.
"""

import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path

import rule_names as R
from catalog import Catalog
from generator.dataset import CLAIMS_COLUMNS, GROUND_TRUTH_COLUMNS
from generator.fraud import CLUSTERING_AMOUNT, FRAUD_COUNTS
from generator.legit import AMOUNT_ROUNDING
from generator.models import load_providers

TOTAL_CLAIMS = 2000
MEMBER_RANGE = (480, 500)
MIN_SINGLE_CODE_CLAIMS = 30
MIN_WEEKDAY_ONLY_CLAIMS = 60
DUPLICATE_GROUPS = FRAUD_COUNTS[R.DUPLICATE_CLAIM] // 2
PHANTOM_THRESHOLD = 30
PHANTOM_DAY_CLAIMS = 31


def _read_csv(path: Path) -> tuple[list[str], list[dict]]:
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def check_dataset(data_dir: Path, catalog: Catalog) -> tuple[list[str], dict]:
    """Return (problems, stats). An empty problem list means every check passed."""
    problems = []

    def expect(ok: bool, message: str) -> None:
        if not ok:
            problems.append(message)

    columns, claims = _read_csv(data_dir / "claims.csv")
    gt_columns, truth = _read_csv(data_dir / "ground_truth.csv")
    summary = json.loads((data_dir / "generation_summary.json").read_text(encoding="utf-8"))

    # --- shape -----------------------------------------------------------------------------
    expect(columns == CLAIMS_COLUMNS, f"claims.csv columns are {columns}")
    expect(gt_columns == GROUND_TRUTH_COLUMNS, f"ground_truth.csv columns are {gt_columns}")
    expect(len(claims) == TOTAL_CLAIMS, f"{len(claims)} claims, expected {TOTAL_CLAIMS}")
    ids = [c["claim_id"] for c in claims]
    expect(len(set(ids)) == len(ids), "claim_id is not unique")
    expect([t["claim_id"] for t in truth] == ids, "ground_truth.csv claim_ids do not match claims.csv")
    if problems:
        return problems, {}  # the remaining checks assume the shape is right

    pattern_of = {t["claim_id"]: t["fraud_pattern"] for t in truth}
    for t in truth:
        expect(t["is_fraud"] == ("1" if t["fraud_pattern"] else "0"), f"{t['claim_id']}: is_fraud disagrees with fraud_pattern")
    pattern_counts = Counter(p for p in pattern_of.values() if p)
    expect(dict(pattern_counts) == FRAUD_COUNTS, f"claims per pattern {dict(pattern_counts)}, expected {FRAUD_COUNTS}")

    # --- members, providers, dates -----------------------------------------------------------
    members = {c["member_id"] for c in claims}
    expect(MEMBER_RANGE[0] <= len(members) <= MEMBER_RANGE[1], f"{len(members)} distinct members, expected {MEMBER_RANGE}")
    providers = {p.id: p for p in load_providers()}
    names = {(c["provider_id"], c["provider_name"]) for c in claims}
    expect({pid for pid, _ in names} == set(providers), "claims do not cover exactly the 50 providers")
    expect(len(names) == len(providers) and all(providers[pid].name == name for pid, name in names if pid in providers),
           "provider_id and provider_name are not one-to-one with providers.json")

    days = {}
    for c in claims:
        try:
            day = date.fromisoformat(c["claim_date"])
        except ValueError:
            problems.append(f"{c['claim_id']}: bad claim_date {c['claim_date']!r}")
            continue
        days[c["claim_id"]] = day
        expect(day.year == 2024, f"{c['claim_id']}: claim_date {day} outside 2024")
        expect(c["is_weekend"] == str(int(day.weekday() >= 5)), f"{c['claim_id']}: is_weekend does not match {day}")

    # --- codes and amounts -------------------------------------------------------------------
    bundle_components = {b.components: b.code for b in catalog.bundles.values()}
    single_code_counts = Counter()
    for c in claims:
        cid, codes, pattern = c["claim_id"], c["procedure_codes"].split("|"), pattern_of[c["claim_id"]]
        unknown = [code for code in codes if code not in catalog.procedures and code not in catalog.bundles]
        expect(not unknown, f"{cid}: unknown code(s) {unknown}")
        if unknown:
            continue
        if pattern == R.UNBUNDLING:
            expect(tuple(codes) in bundle_components, f"{cid}: unbundled codes {codes} are not the components of a bundle")
        else:
            expect(len(codes) == 1, f"{cid}: {len(codes)} codes on a claim that is not unbundling")
            single_code_counts[codes[0]] += 1
        expect(c["claim_type"] == catalog.billable(codes[0]).claim_type, f"{cid}: claim_type {c['claim_type']} does not match {codes[0]}")

        amount = c["submitted_amount"]
        expect(amount.isdigit() and int(amount) > 0 and int(amount) % AMOUNT_ROUNDING == 0,
               f"{cid}: submitted_amount {amount!r} is not a positive multiple of {AMOUNT_ROUNDING}")
        if pattern == R.AMOUNT_CLUSTERING and amount.isdigit():
            expect(CLUSTERING_AMOUNT[0] <= int(amount) <= CLUSTERING_AMOUNT[1], f"{cid}: clustering amount {amount} outside the band")

    for code in catalog.all_billable_codes():
        expect(single_code_counts[code] >= MIN_SINGLE_CODE_CLAIMS,
               f"{code}: {single_code_counts[code]} single-code claims, expected >= {MIN_SINGLE_CODE_CLAIMS}")

    # --- weekday-only hospitals --------------------------------------------------------------
    weekday_only = [p["provider_id"] for p in summary["weekday_only_providers"]]
    per_provider = Counter(c["provider_id"] for c in claims)
    for pid in weekday_only:
        expect(per_provider[pid] >= MIN_WEEKDAY_ONLY_CLAIMS, f"weekday-only {pid}: {per_provider[pid]} claims, expected >= {MIN_WEEKDAY_ONLY_CLAIMS}")
    legit_weekend = [c["claim_id"] for c in claims
                     if c["provider_id"] in weekday_only and c["is_weekend"] == "1" and pattern_of[c["claim_id"]] != R.WEEKEND_ANOMALY]
    expect(not legit_weekend, f"weekend claims at weekday-only hospitals outside the weekend pattern: {legit_weekend[:5]}")

    # --- duplicate groups and phantom provider-day -------------------------------------------
    keys = Counter((c["member_id"], c["provider_id"], c["claim_date"], c["diagnosis_code"]) for c in claims)
    groups = [n for n in keys.values() if n > 1]
    expect(groups == [2] * DUPLICATE_GROUPS, f"duplicate groups {sorted(groups)}, expected {DUPLICATE_GROUPS} groups of 2")

    provider_days = Counter((c["provider_id"], c["claim_date"]) for c in claims)
    busy = {k: n for k, n in provider_days.items() if n > PHANTOM_THRESHOLD}
    phantom = summary["phantom_provider_day"]
    expect(busy == {(phantom["provider_id"], phantom["claim_date"]): PHANTOM_DAY_CLAIMS},
           f"provider-days with > {PHANTOM_THRESHOLD} claims: {busy}, expected only the phantom day with {PHANTOM_DAY_CLAIMS}")

    by_type = Counter(providers[c["provider_id"]].type for c in claims if c["provider_id"] in providers)
    stats = {
        "claims": len(claims),
        "fraud": sum(pattern_counts.values()),
        "claims_per_pattern": dict(sorted(pattern_counts.items())),
        "members": len(members),
        "providers": len({pid for pid, _ in names}),
        "claims_per_provider_type": dict(sorted(by_type.items())),
        "weekday_only_claims": (min(per_provider[p] for p in weekday_only), max(per_provider[p] for p in weekday_only)),
        "min_single_code_claims": min(single_code_counts[c] for c in catalog.all_billable_codes()),
        "duplicate_groups": len(groups),
        "phantom_day": f"{phantom['provider_id']} {phantom['claim_date']} ({provider_days[(phantom['provider_id'], phantom['claim_date'])]} claims)",
    }
    return problems, stats
