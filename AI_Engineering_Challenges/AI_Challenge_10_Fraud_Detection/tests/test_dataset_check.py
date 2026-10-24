"""Mutation tests for check_dataset: break the committed dataset in exactly one way, expect the matching problem."""

import csv
import json
import shutil
from collections import Counter
from datetime import date
from pathlib import Path

import pytest

import rule_names as R
from catalog import load_catalog
from generator.checks import check_dataset
from generator.models import load_providers

DATA_DIR = Path(__file__).parent.parent / "data"
CATALOG = load_catalog()
PROVIDER_TYPE = {p.id: p.type for p in load_providers()}


# --- file helpers ---------------------------------------------------------------------------


def read_table(path: Path) -> tuple[list[str], list[dict]]:
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def write_table(path: Path, header: list[str], rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:  # csv default terminator is CRLF, as in the writer
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


def edit_csv(path: Path, edit) -> None:
    header, rows = read_table(path)
    edit(rows)
    write_table(path, header, rows)


def edit_raw_lines(path: Path, edit) -> None:
    """Edit rows as plain lists, so a row can get more or fewer fields than the header."""
    with open(path, encoding="utf-8", newline="") as f:
        table = list(csv.reader(f))
    edit(table)
    with open(path, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(table)


def edit_summary(data_dir: Path, edit) -> None:
    path = data_dir / "generation_summary.json"
    summary = json.loads(path.read_text(encoding="utf-8"))
    edit(summary)
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def edit_both(data_dir: Path, edit) -> None:
    """Edit claims and labels together; edit(claims, labels) gets both row lists and the labels by claim_id."""
    claims_path, truth_path = data_dir / "claims.csv", data_dir / "ground_truth.csv"
    claims_header, claims = read_table(claims_path)
    truth_header, truth = read_table(truth_path)
    edit(claims, truth)
    write_table(claims_path, claims_header, claims)
    write_table(truth_path, truth_header, truth)


# --- row pickers ----------------------------------------------------------------------------


def legit_claims(claims, truth):
    pattern = {t["claim_id"]: t["fraud_pattern"] for t in truth}
    return [c for c in claims if not pattern[c["claim_id"]]]


def claims_of(claims, truth, rule):
    return [c for c in claims if {t["claim_id"]: t["fraud_pattern"] for t in truth}[c["claim_id"]] == rule]


def set_date(claim: dict, day: str) -> None:
    claim["claim_date"] = day
    claim["is_weekend"] = str(int(date.fromisoformat(day).weekday() >= 5))


def phantom_key(data_dir: Path) -> tuple[str, str]:
    phantom = json.loads((data_dir / "generation_summary.json").read_text(encoding="utf-8"))["phantom_provider_day"]
    return phantom["provider_id"], phantom["claim_date"]


def weekday_only_ids(data_dir: Path) -> list[str]:
    summary = json.loads((data_dir / "generation_summary.json").read_text(encoding="utf-8"))
    return [p["provider_id"] for p in summary["weekday_only_providers"]]


def set_label(truth: list[dict], claim_id: str, pattern: str) -> None:
    for t in truth:
        if t["claim_id"] == claim_id:
            t["fraud_pattern"], t["is_fraud"] = pattern, "1" if pattern else "0"


def ordinary_claims(data_dir: Path, claims, truth) -> list[dict]:
    """Legit single-code weekday claims away from weekday-only hospitals and the phantom day: safe to edit alone."""
    pk, weekday_only = phantom_key(data_dir), weekday_only_ids(data_dir)
    return [c for c in legit_claims(claims, truth)
            if "|" not in c["procedure_codes"] and c["is_weekend"] == "0"
            and c["provider_id"] not in weekday_only and (c["provider_id"], c["claim_date"]) != pk]


def other_hospital(excluded: set[str]) -> str:
    return next(pid for pid, kind in PROVIDER_TYPE.items() if kind == "HOSPITAL" and pid not in excluded)


def provider_name(pid: str) -> str:
    return next(p.name for p in load_providers() if p.id == pid)


def move_to_provider(claim: dict, pid: str) -> None:
    claim["provider_id"], claim["provider_name"] = pid, provider_name(pid)


# --- shape and file breaks ------------------------------------------------------------------


def break_missing_ground_truth(d):
    (d / "ground_truth.csv").unlink()


def break_bom(d):
    path = d / "claims.csv"
    path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())


def break_gt_column_name(d):
    path = d / "ground_truth.csv"
    path.write_bytes(path.read_bytes().replace(b"claim_id", b"claimid", 1))


def break_non_utf8(d):
    path = d / "claims.csv"
    path.write_bytes(path.read_bytes().replace(b"Benh", b"B\xe0nh", 1))


def break_extra_field(d):
    edit_raw_lines(d / "claims.csv", lambda table: table[5].append("x"))


def break_missing_field(d):
    edit_raw_lines(d / "claims.csv", lambda table: table[5].pop())


def break_duplicate_claim_id(d):
    def edit(claims):
        claims[1]["claim_id"] = claims[0]["claim_id"]
    edit_csv(d / "claims.csv", edit)


def break_claim_count(d):
    def edit(claims, truth):
        gone = legit_claims(claims, truth)[-1]["claim_id"]
        claims[:] = [c for c in claims if c["claim_id"] != gone]
        truth[:] = [t for t in truth if t["claim_id"] != gone]
    edit_both(d, edit)


def break_gt_order(d):
    def edit(claims, truth):
        truth[0], truth[1] = truth[1], truth[0]
    edit_both(d, edit)


def break_gt_extra_field(d):
    edit_raw_lines(d / "ground_truth.csv", lambda table: table[5].append("x"))


# --- summary breaks -------------------------------------------------------------------------


def break_summary_not_json(d):
    (d / "generation_summary.json").write_text("{not json", encoding="utf-8")


def break_summary_no_phantom(d):
    edit_summary(d, lambda s: s.pop("phantom_provider_day"))


def break_summary_empty_weekday_only(d):
    edit_summary(d, lambda s: s.update(weekday_only_providers=[]))


def break_summary_clinic_weekday_only(d):
    clinic = next(pid for pid, kind in PROVIDER_TYPE.items() if kind == "CLINIC")
    edit_summary(d, lambda s: s["weekday_only_providers"].__setitem__(0, {"provider_id": clinic}))


def break_summary_provider_id_list(d):
    edit_summary(d, lambda s: s["phantom_provider_day"].update(provider_id=["PRV-049"]))


def break_summary_and_extra_field(d):
    break_summary_not_json(d)
    break_extra_field(d)


# --- content breaks -------------------------------------------------------------------------


def break_is_weekend(d):
    def edit(claims, truth):
        ordinary_claims(d, claims, truth)[0]["is_weekend"] = "1"
    edit_both(d, edit)


def break_amount_off_by_50(d):
    def edit(claims, truth):
        c = ordinary_claims(d, claims, truth)[0]
        c["submitted_amount"] = str(int(c["submitted_amount"]) + 50)
    edit_both(d, edit)


def break_amount_superscript(d):
    def edit(claims, truth):
        ordinary_claims(d, claims, truth)[0]["submitted_amount"] = "\u00b2"  # str.isdigit() is True for it, int() fails
    edit_both(d, edit)


def break_extra_duplicate_group(d):
    def edit(claims, truth):
        # Ordinary claims keep the other checks quiet.
        src, dst = ordinary_claims(d, claims, truth)[:2]
        for field in ("member_id", "provider_id", "provider_name", "claim_date", "is_weekend", "diagnosis_code"):
            dst[field] = src[field]
    edit_both(d, edit)


def break_two_codes_on_legit(d):
    def edit(claims, truth):
        c = ordinary_claims(d, claims, truth)[0]
        c["procedure_codes"] += "|" + c["procedure_codes"]
    edit_both(d, edit)


def break_claim_type(d):
    def edit(claims, truth):
        c = ordinary_claims(d, claims, truth)[0]
        c["claim_type"] = "DENTAL" if c["claim_type"] != "DENTAL" else "INPATIENT"
    edit_both(d, edit)


def break_pattern_count(d):
    def edit(claims, truth):
        set_label(truth, claims_of(claims, truth, R.UPCODING)[0]["claim_id"], "")
    edit_both(d, edit)


def break_provider_name(d):
    def edit(claims):
        for c in claims:
            if c["provider_id"] == "PRV-001":
                c["provider_name"] = "Renamed Provider"
    edit_csv(d / "claims.csv", edit)


def break_year_2023(d):
    def edit(claims, truth):
        set_date(ordinary_claims(d, claims, truth)[0], "2023-06-07")
    edit_both(d, edit)


def break_legit_weekend_at_weekday_only(d):
    def edit(claims, truth):
        weekday_only = weekday_only_ids(d)
        c = next(c for c in legit_claims(claims, truth) if c["provider_id"] in weekday_only)
        set_date(c, "2024-01-06")  # a Saturday
    edit_both(d, edit)


def break_second_busy_provider_day(d):
    def edit(claims, truth):
        pk = phantom_key(d)
        days = Counter((c["provider_id"], c["claim_date"]) for c in claims)
        # Busiest ordinary weekday of a hospital: the same provider donates legit claims from other days to reach 31.
        (pid, day), n = max(((k, v) for k, v in days.items() if k != pk and PROVIDER_TYPE[k[0]] == "HOSPITAL"
                             and date.fromisoformat(k[1]).weekday() < 5), key=lambda kv: kv[1])
        donors = [c for c in legit_claims(claims, truth)
                  if c["provider_id"] == pid and c["claim_date"] != day and (pid, c["claim_date"]) != pk]
        assert len(donors) >= 31 - n, f"{pid} has only {len(donors)} donors for {day}, needs {31 - n}"
        for c in donors[: 31 - n]:
            set_date(c, day)
    edit_both(d, edit)


def break_phantom_label_moved(d):
    def edit(claims, truth):
        pk = phantom_key(d)
        phantom = claims_of(claims, truth, R.PHANTOM_BILLING)[0]
        other = next(c for c in legit_claims(claims, truth) if (c["provider_id"], c["claim_date"]) != pk)
        set_label(truth, phantom["claim_id"], "")
        set_label(truth, other["claim_id"], R.PHANTOM_BILLING)
    edit_both(d, edit)


def break_duplicate_label_moved(d):
    def edit(claims, truth):
        dup = claims_of(claims, truth, R.DUPLICATE_CLAIM)[0]
        set_label(truth, dup["claim_id"], "")
        set_label(truth, legit_claims(claims, truth)[0]["claim_id"], R.DUPLICATE_CLAIM)
    edit_both(d, edit)


def break_weekend_code_not_surgical(d):
    def edit(claims, truth):
        code = next(c for c in CATALOG.procedures.values() if not c.surgical)
        claim = claims_of(claims, truth, R.WEEKEND_ANOMALY)[0]
        claim["procedure_codes"], claim["claim_type"] = code.code, code.claim_type
    edit_both(d, edit)


def break_is_fraud_flag(d):
    def edit(claims, truth):
        fraud = next(t for t in truth if t["fraud_pattern"])
        fraud["is_fraud"] = "0"
    edit_both(d, edit)


def break_too_few_members(d):
    def edit(claims, truth):
        counts = Counter(c["member_id"] for c in claims)
        rare = [m for m, _ in counts.most_common()[:-31:-1]]  # the 30 rarest members
        keep = counts.most_common(1)[0][0]
        for c in claims:
            if c["member_id"] in rare:
                c["member_id"] = keep
    edit_both(d, edit)


def break_provider_coverage(d):
    def edit(claims, truth):
        gone, kept = [pid for pid, kind in PROVIDER_TYPE.items() if kind == "CLINIC"][:2]
        for c in claims:
            if c["provider_id"] == gone:
                move_to_provider(c, kept)
    edit_both(d, edit)


def break_bad_calendar_date(d):
    def edit(claims, truth):
        ordinary_claims(d, claims, truth)[0]["claim_date"] = "2024-13-01"
    edit_both(d, edit)


def break_unknown_code(d):
    def edit(claims, truth):
        ordinary_claims(d, claims, truth)[0]["procedure_codes"] = "P-9999"
    edit_both(d, edit)


def break_unbundling_drops_code(d):
    def edit(claims, truth):
        c = claims_of(claims, truth, R.UNBUNDLING)[0]
        c["procedure_codes"] = c["procedure_codes"].split("|")[0]
    edit_both(d, edit)


def break_clustering_amount(d):
    def edit(claims, truth):
        claims_of(claims, truth, R.AMOUNT_CLUSTERING)[0]["submitted_amount"] = "50000"
    edit_both(d, edit)


def break_rare_single_code(d):
    def edit(claims, truth):
        # Move every legit single-code P-3010 claim to another code of the same claim_type.
        code = "P-3010"
        target = next(p.code for p in CATALOG.procedures.values()
                      if p.code != code and p.claim_type == CATALOG.procedures[code].claim_type)
        for c in legit_claims(claims, truth):
            if c["procedure_codes"] == code:
                c["procedure_codes"] = target
    edit_both(d, edit)


def break_weekday_only_too_small(d):
    def edit(claims, truth):
        weekday_only = weekday_only_ids(d)
        pid = weekday_only[0]
        target = other_hospital(set(weekday_only))
        mine = [c for c in legit_claims(claims, truth) if c["provider_id"] == pid]
        surplus = sum(c["provider_id"] == pid for c in claims) - 59
        assert len(mine) >= surplus, f"{pid}: {len(mine)} legit claims, need to move {surplus}"
        for c in mine[:surplus]:
            move_to_provider(c, target)
    edit_both(d, edit)


def break_weekend_anomaly_on_monday(d):
    def edit(claims, truth):
        set_date(claims_of(claims, truth, R.WEEKEND_ANOMALY)[0], "2024-01-08")  # a Monday
    edit_both(d, edit)


def break_weekend_anomaly_regular_hospital(d):
    def edit(claims, truth):
        move_to_provider(claims_of(claims, truth, R.WEEKEND_ANOMALY)[0], other_hospital(set(weekday_only_ids(d))))
    edit_both(d, edit)


def break_weekend_anomaly_uneven(d):
    def edit(claims, truth):
        first, second = weekday_only_ids(d)[:2]
        move_to_provider(next(c for c in claims_of(claims, truth, R.WEEKEND_ANOMALY) if c["provider_id"] == first), second)
    edit_both(d, edit)


def break_phantom_day_composition(d):
    def edit(claims, truth):
        pk = phantom_key(d)
        on_day = {c["claim_id"] for c in claims if (c["provider_id"], c["claim_date"]) == pk}
        upcoding_on_day = next(c for c in claims_of(claims, truth, R.UPCODING) if c["claim_id"] in on_day)
        mismatch_off_day = next(c for c in claims_of(claims, truth, R.DIAGNOSIS_PROCEDURE_MISMATCH) if c["claim_id"] not in on_day)
        set_label(truth, upcoding_on_day["claim_id"], R.DIAGNOSIS_PROCEDURE_MISMATCH)
        set_label(truth, mismatch_off_day["claim_id"], R.UPCODING)  # every pattern total stays the same
    edit_both(d, edit)


# (id, break function, substring that must appear in at least one problem)
CASES = [
    ("missing-ground-truth", break_missing_ground_truth, "missing file(s)"),
    ("claims-bom", break_bom, "claims.csv columns are"),
    ("gt-column-renamed", break_gt_column_name, "ground_truth.csv columns are"),
    ("claims-not-utf8", break_non_utf8, "claims.csv is not UTF-8"),
    ("row-extra-field", break_extra_field, "claims.csv rows with a wrong number of fields"),
    ("row-missing-field", break_missing_field, "claims.csv rows with a wrong number of fields"),
    ("duplicate-claim-id", break_duplicate_claim_id, "claim_id is not unique"),
    ("summary-not-json", break_summary_not_json, "generation_summary.json is unreadable"),
    ("summary-no-phantom-key", break_summary_no_phantom, "generation_summary.json is unreadable"),
    ("summary-empty-weekday-only", break_summary_empty_weekday_only, "weekday_only_providers in the summary"),
    ("summary-clinic-weekday-only", break_summary_clinic_weekday_only, "weekday_only_providers in the summary"),
    ("summary-provider-id-list", break_summary_provider_id_list, "generation_summary.json is unreadable"),
    ("is-weekend-wrong", break_is_weekend, "is_weekend does not match"),
    ("amount-off-by-50", break_amount_off_by_50, "is not a positive multiple"),
    ("amount-superscript", break_amount_superscript, "is not a positive multiple"),
    ("extra-duplicate-group", break_extra_duplicate_group, "duplicate groups"),
    ("legit-claim-two-codes", break_two_codes_on_legit, "codes on a claim that is not unbundling"),
    ("claim-type-wrong", break_claim_type, ": claim_type "),
    ("pattern-count-off-by-one", break_pattern_count, "claims per pattern"),
    ("provider-renamed", break_provider_name, "not one-to-one with providers.json"),
    ("date-in-2023", break_year_2023, "outside 2024"),
    ("legit-weekend-at-weekday-only", break_legit_weekend_at_weekday_only, "weekend claims at weekday-only hospitals"),
    ("second-busy-provider-day", break_second_busy_provider_day, "provider-days with > 30 claims"),
    ("phantom-label-moved", break_phantom_label_moved, "phantom_billing claims outside the phantom provider-day"),
    ("duplicate-label-moved", break_duplicate_label_moved, "differ from duplicate_claim labels"),
    ("weekend-code-not-surgical", break_weekend_code_not_surgical, "is not surgical"),
    ("claim-count-1999", break_claim_count, "claims, expected 2000"),
    ("gt-order-swapped", break_gt_order, "do not match claims.csv"),
    ("gt-row-extra-field", break_gt_extra_field, "ground_truth.csv rows with a wrong number of fields"),
    ("is-fraud-flag-wrong", break_is_fraud_flag, "is_fraud disagrees with fraud_pattern"),
    ("too-few-members", break_too_few_members, "distinct members"),
    ("provider-not-covered", break_provider_coverage, "do not cover exactly the 50 providers"),
    ("calendar-date-invalid", break_bad_calendar_date, "bad claim_date"),
    ("unknown-code", break_unknown_code, "unknown code(s)"),
    ("unbundling-missing-component", break_unbundling_drops_code, "are not the components of a bundle"),
    ("clustering-amount-outside-band", break_clustering_amount, "outside the band"),
    ("code-has-few-single-claims", break_rare_single_code, "single-code claims, expected >= 30"),
    ("weekday-only-too-small", break_weekday_only_too_small, "claims, expected >= 60"),
    ("weekend-anomaly-on-monday", break_weekend_anomaly_on_monday, "weekend_anomaly claim is not on a weekend"),
    ("weekend-anomaly-regular-hospital", break_weekend_anomaly_regular_hospital, "not a weekday-only hospital"),
    ("weekend-anomaly-uneven-per-hospital", break_weekend_anomaly_uneven, "weekend_anomaly claims per weekday-only hospital"),
    ("phantom-day-composition", break_phantom_day_composition, "phantom provider-day holds"),
]


@pytest.fixture
def data_copy(tmp_path):
    shutil.copytree(DATA_DIR, tmp_path / "data")
    return tmp_path / "data"


def test_committed_dataset_passes():
    problems, _ = check_dataset(DATA_DIR, CATALOG)
    assert problems == []


@pytest.mark.parametrize("break_it, expected", [(fn, text) for _, fn, text in CASES], ids=[c[0] for c in CASES])
def test_broken_dataset_is_caught(data_copy, break_it, expected):
    break_it(data_copy)
    problems, _ = check_dataset(data_copy, CATALOG)  # an exception here fails the test
    assert problems
    assert any(expected in p for p in problems), problems


def test_broken_summary_and_extra_field_are_both_reported(data_copy):
    break_summary_and_extra_field(data_copy)
    problems, _ = check_dataset(data_copy, CATALOG)
    assert any("generation_summary.json is unreadable" in p for p in problems), problems
    assert any("wrong number of fields" in p for p in problems), problems
