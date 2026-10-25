"""System tests S3, S5, S7 + risk_score + the `score` command: weights drive scores, output shape, ranking."""

import csv
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

from catalog import load_catalog
from claims import CLAIMS_COLUMNS, Claim
from rule_names import ALL_RULES, AMOUNT_CLUSTERING, DIAGNOSIS_PROCEDURE_MISMATCH
from scoring.score import SATURATION_K, rank, risk_score, score_claims, sort_flags, write_scored
from scoring.weights import load_weights

CLI = Path(__file__).parent.parent / "src" / "cli.py"
DAY = date(2024, 3, 12)  # a Tuesday


@pytest.fixture(scope="module")
def catalog():
    return load_catalog()


@pytest.fixture
def weights():
    return dict(load_weights())


def make_claim(claim_id, diagnosis="J06.9", codes=("P-1001",), amount=100_000, member="MEM-0001"):
    return Claim(
        claim_id=claim_id, member_id=member, provider_id="PRV-001", provider_name="Test provider",
        claim_date=DAY, claim_type="OUTPATIENT", diagnosis_code=diagnosis, procedure_codes=tuple(codes),
        submitted_amount=amount, is_weekend=False,
    )


def by_id(results):
    return {r["claim_id"]: r for r in results}


# --- risk_score ---

@pytest.mark.parametrize("total, expected", [(0, 0), (2, 39), (5, 71), (6, 78), (10, 92), (19, 99), (27, 100)])
def test_risk_score_reference_values(total, expected):
    assert risk_score(total) == expected


def test_risk_score_never_lands_on_a_half():
    import math
    for total in range(28):
        exact = 100 * (1 - math.exp(-SATURATION_K * total))
        assert abs(exact - int(exact) - 0.5) > 1e-6, total


# --- S3: weights are configuration, not code ---

def test_s3_changing_one_weight_changes_only_claims_with_that_rule(catalog, weights):
    claims = [make_claim("CLM-00001", amount=48_500), make_claim("CLM-00002", amount=100_000, member="MEM-0002")]
    before = by_id(score_claims(claims, catalog, weights))
    assert before["CLM-00001"]["risk_score"] == risk_score(weights[AMOUNT_CLUSTERING])

    weights[AMOUNT_CLUSTERING] = 5
    after = by_id(score_claims(claims, catalog, weights))
    assert after["CLM-00001"]["risk_score"] == risk_score(5) == 71
    assert after["CLM-00001"]["risk_score"] != before["CLM-00001"]["risk_score"]
    assert after["CLM-00001"]["flags"][0]["severity"] == 5
    assert after["CLM-00002"] == before["CLM-00002"]


# --- S5: output shape ---

def two_flag_and_clean_claims():
    return [
        make_claim("CLM-00001", amount=100_000, member="MEM-0001"),
        make_claim("CLM-00002", diagnosis="K02.1", codes=("P-3001",), amount=48_500, member="MEM-0002"),
    ]


def test_s5_every_claim_present_with_exact_keys(catalog, weights):
    results = score_claims(two_flag_and_clean_claims(), catalog, weights)
    assert [r["claim_id"] for r in results] == ["CLM-00002", "CLM-00001"]
    assert all(list(r) == ["claim_id", "risk_score", "flags"] for r in results)
    clean, flagged = results[1], results[0]
    assert clean["risk_score"] == 0 and clean["flags"] == []
    assert [f["rule"] for f in flagged["flags"]] == [DIAGNOSIS_PROCEDURE_MISMATCH, AMOUNT_CLUSTERING]
    assert all(list(f) == ["rule", "severity", "evidence"] for f in flagged["flags"])
    assert flagged["risk_score"] == risk_score(weights[DIAGNOSIS_PROCEDURE_MISMATCH] + weights[AMOUNT_CLUSTERING])


def test_s5_written_file_round_trips_and_is_not_ascii_escaped(tmp_path, catalog, weights):
    results = score_claims(two_flag_and_clean_claims(), catalog, weights)
    results[0]["flags"][0]["evidence"] += " - Phòng khám Đa khoa"
    path = write_scored(results, tmp_path / "nested" / "out")
    assert path == tmp_path / "nested" / "out" / "scored_output.json"
    text = path.read_text(encoding="utf-8")
    assert json.loads(text) == results
    assert "Phòng khám Đa khoa" in text
    assert text.startswith("[\n  {")  # indent=2


def test_s7_score_claims_sorts_flags_by_severity_not_rule_order(catalog, weights):
    weights[AMOUNT_CLUSTERING] = 5
    weights[DIAGNOSIS_PROCEDURE_MISMATCH] = 1
    claims = [make_claim("CLM-00001", diagnosis="K02.1", codes=("P-3001",), amount=48_500)]
    flags = score_claims(claims, catalog, weights)[0]["flags"]
    assert [f["rule"] for f in flags] == [AMOUNT_CLUSTERING, DIAGNOSIS_PROCEDURE_MISMATCH]
    assert [f["severity"] for f in flags] == [5, 1]


# --- S7: ranking ---

def test_s7_equal_score_ranks_by_flag_count_not_total_severity():
    many_low = result("CLM-00009", 39, "upcoding", "unbundling")  # 2 flags, severity 1 each
    one_high = result("CLM-00001", 39, "duplicate_claim")
    one_high["flags"][0]["severity"] = 2
    assert [r["claim_id"] for r in rank([one_high, many_low])] == ["CLM-00009", "CLM-00001"]


def result(claim_id, score, *rules):
    return {"claim_id": claim_id, "risk_score": score, "flags": [{"rule": r, "severity": 1, "evidence": ""} for r in rules]}


def test_s7_rank_by_score_then_flag_count_then_claim_id():
    results = [
        result("CLM-00005", 50, "upcoding"),
        result("CLM-00003", 50, "upcoding", "unbundling"),
        result("CLM-00001", 50, "upcoding"),
        result("CLM-00004", 71, "duplicate_claim"),
        result("CLM-00002", 0),
    ]
    assert [r["claim_id"] for r in rank(results)] == ["CLM-00004", "CLM-00003", "CLM-00001", "CLM-00005", "CLM-00002"]


def test_s7_flags_sorted_by_severity_then_rule_order():
    def flag(rule, severity):
        return {"rule": rule, "severity": severity, "evidence": ""}

    flags = [flag("amount_clustering", 2), flag("unbundling", 3), flag("upcoding", 3), flag("duplicate_claim", 5)]
    ordered = [f["rule"] for f in sort_flags(flags)]
    assert ordered == ["duplicate_claim", "upcoding", "unbundling", "amount_clustering"]
    assert ALL_RULES.index("upcoding") < ALL_RULES.index("unbundling")


# --- CLI ---

def write_claims(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CLAIMS_COLUMNS)
        writer.writerows(rows)


def run_score(*args):
    return subprocess.run([sys.executable, str(CLI), "score", *args], capture_output=True, text=True, encoding="utf-8")


def test_cli_score_writes_ranked_output(tmp_path):
    rows = [
        ["CLM-00001", "MEM-0001", "PRV-001", "Test Clinic", "2024-03-12", "OUTPATIENT", "J06.9", "P-1001", "100000", "0"],
        ["CLM-00002", "MEM-0002", "PRV-001", "Test Clinic", "2024-03-12", "OUTPATIENT", "J06.9", "P-1001", "48500", "0"],
    ]
    write_claims(tmp_path / "claims.csv", rows)
    proc = run_score("--data", str(tmp_path), "--out", str(tmp_path / "out"))
    assert proc.returncode == 0, proc.stderr
    assert "Scored 2 claims in" in proc.stdout and "1 of 2" in proc.stdout
    data = json.loads((tmp_path / "out" / "scored_output.json").read_text(encoding="utf-8"))
    assert [r["claim_id"] for r in data] == ["CLM-00002", "CLM-00001"]
    assert data[0]["risk_score"] == 39


def test_cli_score_reports_every_claims_problem_without_traceback(tmp_path):
    rows = [
        ["CLM-00001", "MEM-0001", "PRV-001", "Test Clinic", "2024-03-12", "OUTPATIENT", "J06.9", "P-9999", "100000", "0"],
        ["CLM-00002", "MEM-0002", "PRV-001", "Test Clinic", "not-a-date", "OUTPATIENT", "J06.9", "P-1001", "100000", "0"],
    ]
    write_claims(tmp_path / "claims.csv", rows)
    proc = run_score("--data", str(tmp_path), "--out", str(tmp_path / "out"))
    assert proc.returncode == 1
    assert "Traceback" not in proc.stderr
    assert "line 2" in proc.stderr and "line 3" in proc.stderr
    assert not (tmp_path / "out").exists()


CLUSTER_ROW = ["CLM-00001", "MEM-0001", "PRV-001", "Test Clinic", "2024-03-12", "OUTPATIENT", "J06.9", "P-1001", "48500", "0"]


def test_cli_score_uses_the_weights_file(tmp_path):
    write_claims(tmp_path / "claims.csv", [CLUSTER_ROW])
    custom = {**load_weights(), AMOUNT_CLUSTERING: 5}
    (tmp_path / "w.json").write_text(json.dumps(custom), encoding="utf-8")
    proc = run_score("--data", str(tmp_path), "--out", str(tmp_path / "out"), "--weights", str(tmp_path / "w.json"))
    assert proc.returncode == 0, proc.stderr
    data = json.loads((tmp_path / "out" / "scored_output.json").read_text(encoding="utf-8"))
    assert data[0]["risk_score"] == risk_score(5) == 71
    assert data[0]["flags"][0]["severity"] == 5


def test_cli_score_invalid_weights_exit_1_without_traceback(tmp_path):
    write_claims(tmp_path / "claims.csv", [CLUSTER_ROW])
    (tmp_path / "w.json").write_text('{"upcoding": 9}', encoding="utf-8")
    proc = run_score("--data", str(tmp_path), "--out", str(tmp_path / "out"), "--weights", str(tmp_path / "w.json"))
    assert proc.returncode == 1
    assert "Traceback" not in proc.stderr
    assert "upcoding" in proc.stderr and "missing weight" in proc.stderr


def test_cli_score_out_is_an_existing_file_exit_1_without_traceback(tmp_path):
    write_claims(tmp_path / "claims.csv", [CLUSTER_ROW])
    (tmp_path / "out").write_text("not a directory", encoding="utf-8")
    proc = run_score("--data", str(tmp_path), "--out", str(tmp_path / "out"))
    assert proc.returncode == 1
    assert "Traceback" not in proc.stderr
    assert "Cannot write" in proc.stderr
