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
from claims import CLAIMS_COLUMNS
from generator.dataset import GROUND_TRUTH_COLUMNS
from generator.fraud import CLUSTERING_AMOUNT, FRAUD_COUNTS, PHANTOM_DAY_EXTRAS, WEEKEND_PER_PROVIDER
from generator.legit import AMOUNT_ROUNDING
from generator.models import WEEKDAY_ONLY_COUNT, load_providers

TOTAL_CLAIMS = 2000
MEMBER_RANGE = (480, 500)
MIN_SINGLE_CODE_CLAIMS = 30
MIN_WEEKDAY_ONLY_CLAIMS = 60
DUPLICATE_GROUPS = FRAUD_COUNTS[R.DUPLICATE_CLAIM] // 2
PHANTOM_THRESHOLD = 30
PHANTOM_DAY_CLAIMS = 31
PHANTOM_DAY_OTHER_PATTERNS = {R.UPCODING: PHANTOM_DAY_EXTRAS, R.DIAGNOSIS_PROCEDURE_MISMATCH: PHANTOM_DAY_EXTRAS}


def _read_csv(path: Path) -> tuple[list[str], list[dict], list[int]]:
    """Return (columns, rows, line numbers of rows with too many or too few fields)."""
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows, bad_lines = [], []
        for row in reader:
            # DictReader puts extra fields under the key None and fills missing ones with None.
            if None in row or None in row.values():
                bad_lines.append(reader.line_num)
            rows.append(row)
        return list(reader.fieldnames or []), rows, bad_lines


def check_dataset(data_dir: Path, catalog: Catalog) -> tuple[list[str], dict]:
    """Return (problems, stats). An empty problem list means every check passed."""
    problems = []

    def expect(ok: bool, message: str) -> None:
        if not ok:
            problems.append(message)

    missing = [name for name in ("claims.csv", "ground_truth.csv", "generation_summary.json") if not (data_dir / name).is_file()]
    if missing:
        return [f"missing file(s) in {data_dir}: {missing}"], {}

    read = {}
    for name in ("claims.csv", "ground_truth.csv"):
        try:
            read[name] = _read_csv(data_dir / name)
        except UnicodeDecodeError as e:
            return [f"{name} is not UTF-8: {e.reason} at byte {e.start}"], {}
        except csv.Error as e:
            return [f"{name} is not valid CSV: {e}"], {}
    columns, claims, bad_claims = read["claims.csv"]
    gt_columns, truth, bad_truth = read["ground_truth.csv"]
    weekday_only, phantom_key = [], ("", "")  # replaced below; only read when the summary is valid
    try:
        summary = json.loads((data_dir / "generation_summary.json").read_text(encoding="utf-8"))
        weekday_only = [p["provider_id"] for p in summary["weekday_only_providers"]]
        phantom = summary["phantom_provider_day"]
        phantom_key = (phantom["provider_id"], phantom["claim_date"])
        if not all(isinstance(v, str) for v in [*weekday_only, *phantom_key]):
            raise TypeError("provider_id / claim_date values must be strings")
    except (ValueError, KeyError, TypeError) as e:
        # Still run the shape checks below, so CSV problems are reported in the same run.
        problems.append(f"generation_summary.json is unreadable or incomplete: {e!r}")

    # --- shape -----------------------------------------------------------------------------
    expect(not bad_claims, f"claims.csv rows with a wrong number of fields at lines {bad_claims[:5]}")
    expect(not bad_truth, f"ground_truth.csv rows with a wrong number of fields at lines {bad_truth[:5]}")
    expect(columns == CLAIMS_COLUMNS, f"claims.csv columns are {columns}")
    expect(gt_columns == GROUND_TRUTH_COLUMNS, f"ground_truth.csv columns are {gt_columns}")
    if problems:
        return problems, {}  # the checks below read columns by name and need the summary
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

    for c in claims:
        try:
            day = date.fromisoformat(c["claim_date"])
        except ValueError:
            problems.append(f"{c['claim_id']}: bad claim_date {c['claim_date']!r}")
            continue
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
        expect(amount.isascii() and amount.isdigit() and int(amount) > 0 and int(amount) % AMOUNT_ROUNDING == 0,
               f"{cid}: submitted_amount {amount!r} is not a positive multiple of {AMOUNT_ROUNDING}")
        if pattern == R.AMOUNT_CLUSTERING and amount.isascii() and amount.isdigit():
            expect(CLUSTERING_AMOUNT[0] <= int(amount) <= CLUSTERING_AMOUNT[1], f"{cid}: clustering amount {amount} outside the band")

    for code in catalog.all_billable_codes():
        expect(single_code_counts[code] >= MIN_SINGLE_CODE_CLAIMS,
               f"{code}: {single_code_counts[code]} single-code claims, expected >= {MIN_SINGLE_CODE_CLAIMS}")

    # --- weekday-only hospitals --------------------------------------------------------------
    # The list comes from the summary, so validate it first: an empty list would pass every check below.
    expect(len(weekday_only) == WEEKDAY_ONLY_COUNT and len(set(weekday_only)) == WEEKDAY_ONLY_COUNT
           and all(pid in providers and providers[pid].type == "HOSPITAL" for pid in weekday_only),
           f"weekday_only_providers in the summary {weekday_only} is not {WEEKDAY_ONLY_COUNT} distinct hospitals of providers.json")
    if not weekday_only:
        return problems, {}  # the stats below need at least one weekday-only hospital
    per_provider = Counter(c["provider_id"] for c in claims)
    for pid in weekday_only:
        expect(per_provider[pid] >= MIN_WEEKDAY_ONLY_CLAIMS, f"weekday-only {pid}: {per_provider[pid]} claims, expected >= {MIN_WEEKDAY_ONLY_CLAIMS}")
    legit_weekend = [c["claim_id"] for c in claims
                     if c["provider_id"] in weekday_only and c["is_weekend"] == "1" and pattern_of[c["claim_id"]] != R.WEEKEND_ANOMALY]
    expect(not legit_weekend, f"weekend claims at weekday-only hospitals outside the weekend pattern: {legit_weekend[:5]}")

    surgical = {code for code in catalog.all_billable_codes() if catalog.billable(code).surgical}
    weekend_claims = [c for c in claims if pattern_of[c["claim_id"]] == R.WEEKEND_ANOMALY]
    for c in weekend_claims:
        cid = c["claim_id"]
        expect(c["is_weekend"] == "1", f"{cid}: weekend_anomaly claim is not on a weekend")
        expect(c["provider_id"] in weekday_only, f"{cid}: weekend_anomaly claim at {c['provider_id']}, not a weekday-only hospital")
        expect(c["procedure_codes"] in surgical, f"{cid}: weekend_anomaly code {c['procedure_codes']} is not surgical")
    weekend_per_provider = Counter(c["provider_id"] for c in weekend_claims)
    expect(all(weekend_per_provider[pid] == WEEKEND_PER_PROVIDER for pid in weekday_only) and len(weekend_per_provider) == len(weekday_only),
           f"weekend_anomaly claims per weekday-only hospital {dict(weekend_per_provider)}, expected {WEEKEND_PER_PROVIDER} each")

    # --- duplicate groups and phantom provider-day -------------------------------------------
    keys = Counter((c["member_id"], c["provider_id"], c["claim_date"], c["diagnosis_code"]) for c in claims)
    groups = [n for n in keys.values() if n > 1]
    expect(groups == [2] * DUPLICATE_GROUPS, f"duplicate groups {sorted(groups)}, expected {DUPLICATE_GROUPS} groups of 2")

    duplicate_keys = {k for k, n in keys.items() if n > 1}
    in_groups = {c["claim_id"] for c in claims
                 if (c["member_id"], c["provider_id"], c["claim_date"], c["diagnosis_code"]) in duplicate_keys}
    labelled = {cid for cid, p in pattern_of.items() if p == R.DUPLICATE_CLAIM}
    expect(in_groups == labelled, f"claims in duplicate-key groups differ from duplicate_claim labels: {sorted(in_groups ^ labelled)[:5]}")

    provider_days = Counter((c["provider_id"], c["claim_date"]) for c in claims)
    busy = {k: n for k, n in provider_days.items() if n > PHANTOM_THRESHOLD}
    expect(busy == {phantom_key: PHANTOM_DAY_CLAIMS},
           f"provider-days with > {PHANTOM_THRESHOLD} claims: {busy}, expected only the phantom day with {PHANTOM_DAY_CLAIMS}")

    phantom_labelled = [c for c in claims if pattern_of[c["claim_id"]] == R.PHANTOM_BILLING]
    expect(all((c["provider_id"], c["claim_date"]) == phantom_key for c in phantom_labelled),
           "phantom_billing claims outside the phantom provider-day of the summary")
    on_phantom_day = Counter(pattern_of[c["claim_id"]] or "legit" for c in claims
                             if (c["provider_id"], c["claim_date"]) == phantom_key)
    expected_on_day = {R.PHANTOM_BILLING: FRAUD_COUNTS[R.PHANTOM_BILLING], **PHANTOM_DAY_OTHER_PATTERNS}
    expect(dict(on_phantom_day) == expected_on_day, f"phantom provider-day holds {dict(on_phantom_day)}, expected {expected_on_day}")

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
        "phantom_day": f"{phantom_key[0]} {phantom_key[1]} ({provider_days[phantom_key]} claims)",
    }
    return problems, stats
