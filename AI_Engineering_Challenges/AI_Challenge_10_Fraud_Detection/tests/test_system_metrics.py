"""System tests for src/metrics: confusion counts, natural FP by rule, thresholds, ground-truth validation."""

import json

import pytest

from metrics.evaluate import (
    GroundTruthError, THRESHOLDS, by_pattern, confusion, evaluate, extra_rule_claims,
    load_ground_truth, load_phantom_day_claims, natural_fp_by_rule, split_extra_rules, threshold_table,
)
from metrics.report import build_report
from rule_names import ALL_RULES, DUPLICATE_CLAIM, PHANTOM_BILLING, RAPID_RESUBMISSION, UPCODING


def result(claim_id, score, *rules):
    return {"claim_id": claim_id, "risk_score": score, "flags": [{"rule": r, "severity": 1, "evidence": "x"} for r in rules]}


# F1 fraud caught by own rule; F2 fraud caught only by another rule; F3 fraud missed;
# L1 legit with 2 rules; L2 legit with 1 rule; L3, L4 legit clean.
RESULTS = [
    result("F1", 70, DUPLICATE_CLAIM),
    result("F2", 40, PHANTOM_BILLING),
    result("F3", 0),
    result("L1", 53, RAPID_RESUBMISSION, UPCODING),
    result("L2", 39, UPCODING),
    result("L3", 0),
    result("L4", 0),
    result("L5", 0),
]
TRUTH = {
    "F1": (True, DUPLICATE_CLAIM), "F2": (True, UPCODING), "F3": (True, UPCODING),
    "L1": (False, ""), "L2": (False, ""), "L3": (False, ""), "L4": (False, ""), "L5": (False, ""),
}


def write_truth(tmp_path, text):
    path = tmp_path / "ground_truth.csv"
    path.write_text(text, encoding="utf-8")
    return path


def test_confusion_counts_known_example():
    c = confusion(RESULTS, TRUTH)
    assert (c["tp"], c["fp"], c["fn"], c["tn"]) == (2, 2, 1, 3)
    assert c["precision"] == pytest.approx(0.5)
    assert c["recall"] == pytest.approx(2 / 3)
    assert c["fpr"] == pytest.approx(2 / 5)


def test_fp_claim_with_two_rules_counts_under_both_and_total_row():
    fp = natural_fp_by_rule(RESULTS, TRUTH)
    rows = {r["rule"]: r for r in fp["rows"]}
    assert rows[RAPID_RESUBMISSION]["on_legit"] == 1
    assert rows[UPCODING]["on_legit"] == 2  # L1 and L2
    assert rows[UPCODING]["on_fraud"] == 0
    assert rows[DUPLICATE_CLAIM] == {"rule": DUPLICATE_CLAIM, "flags": 1, "on_fraud": 1, "on_legit": 0}
    assert sum(r["on_legit"] for r in fp["rows"]) == 3
    assert fp["fp_claims"] == 2  # L1 counted once in the total
    assert [r["rule"] for r in fp["rows"]] == list(ALL_RULES)


def test_threshold_boundaries():
    rows = {t["threshold"]: t for t in threshold_table(RESULTS, TRUTH)}
    assert [t[0] for t in THRESHOLDS] == ["> 0", ">= 40", ">= 70"]
    assert rows["> 0"]["tp"] == 2 and rows["> 0"]["fp"] == 2  # score 39 included, score 0 excluded
    assert rows[">= 40"]["tp"] == 2 and rows[">= 40"]["fp"] == 1  # F2 at exactly 40 included, 39 excluded
    assert rows[">= 70"]["tp"] == 1 and rows[">= 70"]["fp"] == 0  # F1 at exactly 70 included


def test_by_pattern_and_extra_rules():
    rows = {r["pattern"]: r for r in by_pattern(RESULTS, TRUTH)}
    assert rows[DUPLICATE_CLAIM] == {"pattern": DUPLICATE_CLAIM, "fraud": 1, "caught": 1, "caught_by_own_rule": 1}
    assert rows[UPCODING] == {"pattern": UPCODING, "fraud": 2, "caught": 1, "caught_by_own_rule": 0}
    extras = extra_rule_claims(RESULTS, TRUTH)
    assert extras == [("F2", UPCODING, [PHANTOM_BILLING])]
    assert split_extra_rules(extras, {"F2"}) == {"expected": extras, "unexpected": [], "checked": True}
    assert split_extra_rules(extras, set())["unexpected"] == extras
    assert split_extra_rules(extras, None) == {"expected": [], "unexpected": extras, "checked": False}


def test_ground_truth_claim_missing_or_extra(tmp_path):
    truth = dict(TRUTH)
    del truth["L5"]
    truth["Z9"] = (False, "")
    with pytest.raises(GroundTruthError) as exc:
        evaluate(RESULTS, truth)
    message = str(exc.value)
    assert "1 scored claim(s) missing" in message and "L5" in message
    assert "1 ground-truth claim(s) not scored" in message and "Z9" in message


def test_bad_header_and_bad_is_fraud_list_both(tmp_path):
    path = write_truth(tmp_path, "id,is_fraud,pattern\nC1,2,\nC2,1,upcoding\n")
    with pytest.raises(GroundTruthError) as exc:
        load_ground_truth(path)
    message = str(exc.value)
    assert "2 problem(s)" in message
    assert "header must be" in message
    assert "is_fraud must be 0 or 1, got '2'" in message


def test_load_ground_truth_valid(tmp_path):
    path = write_truth(tmp_path, "claim_id,is_fraud,fraud_pattern\nC1,1,upcoding\nC2,0,\n")
    assert load_ground_truth(path) == {"C1": (True, "upcoding"), "C2": (False, "")}


def test_zero_predictions_does_not_crash():
    results = [result("A", 0), result("B", 0)]
    truth = {"A": (True, UPCODING), "B": (False, "")}
    c = confusion(results, truth)
    assert (c["tp"], c["fp"], c["fn"], c["tn"]) == (0, 0, 1, 1)
    assert c["precision"] == 0.0 and c["recall"] == 0.0 and c["fpr"] == 0.0
    weights = {rule: 1 for rule in ALL_RULES}
    assert "# Metrics report" in build_report(evaluate(results, truth), weights, 0.1)


def test_report_has_four_parts_and_runtime_line():
    weights = {rule: 2 for rule in ALL_RULES}
    text = build_report(evaluate(RESULTS, TRUTH), weights, 1.2345)
    for heading in ("## 1. Overall", "## 2. By pattern", "## 3. Natural false positives by rule", "## 4. Threshold table"):
        assert heading in text
    assert "Scored 8 claims in 1.234 s" in text or "Scored 8 claims in 1.235 s" in text
    assert "seed unknown" in text  # no data dir given


def test_unknown_or_missing_pattern_and_legit_with_pattern_list_all(tmp_path):
    path = write_truth(tmp_path, "claim_id,is_fraud,fraud_pattern\nC1,1,unbundlng\nC2,1,\nC3,0,upcoding\nC4,0,\n")
    with pytest.raises(GroundTruthError) as exc:
        load_ground_truth(path)
    message = str(exc.value)
    assert "3 problem(s)" in message
    assert "fraud claim C1 has unknown fraud_pattern 'unbundlng'" in message
    assert "fraud claim C2 has unknown fraud_pattern ''" in message
    assert "legit claim C3 must have an empty fraud_pattern" in message


def test_wrong_field_count_and_duplicate_claim_id_list_both(tmp_path):
    path = write_truth(tmp_path, "claim_id,is_fraud,fraud_pattern\nC1,0,\nC1,0,\nC2,0\n")
    with pytest.raises(GroundTruthError) as exc:
        load_ground_truth(path)
    message = str(exc.value)
    assert "2 problem(s)" in message
    assert "line 3: duplicate claim_id C1" in message
    assert "line 4: expected 3 fields, got 2" in message


def test_report_pattern_without_fraud_is_n_a_and_extra_sections():
    results = [result("A", 40, UPCODING), result("B", 0)]
    truth = {"A": (True, UPCODING), "B": (False, "")}
    text = build_report(evaluate(results, truth, set()), {rule: 1 for rule in ALL_RULES}, 0.5)
    assert "| duplicate_claim | 0 | 0 | 0 | n/a |" in text
    assert "No fraud claims for: duplicate_claim" in text
    assert "None." in text
    results = [result("A", 40, UPCODING, PHANTOM_BILLING), result("B", 0)]
    text = build_report(evaluate(results, truth, None), {rule: 1 for rule in ALL_RULES}, 0.5)
    assert "1 fraud claim carries" in text and "could not be checked" in text


def test_thousands_separator_in_counts():
    results = [result(f"L{i}", 0) for i in range(1200)] + [result("F", 40, UPCODING)]
    truth = {r["claim_id"]: (False, "") for r in results}
    truth["F"] = (True, UPCODING)
    text = build_report(evaluate(results, truth), {rule: 1 for rule in ALL_RULES}, 0.5)
    assert "1,201 claims" in text and "| 1,200 |" in text


def test_split_extra_rules_requires_phantom_billing_only_on_phantom_day():
    ids = {"A", "B", "C", "D"}
    extras = [
        ("A", UPCODING, [PHANTOM_BILLING]),
        ("B", UPCODING, [RAPID_RESUBMISSION]),
        ("C", UPCODING, [PHANTOM_BILLING, RAPID_RESUBMISSION]),
        ("Z", UPCODING, [PHANTOM_BILLING]),  # right rule, not on the phantom day
    ]
    split = split_extra_rules(extras, ids)
    assert split["expected"] == [extras[0]]
    assert split["unexpected"] == extras[1:]


def write_phantom_files(tmp_path, summary_date="2024-12-26", count=2):
    summary = {"phantom_provider_day": {"provider_id": "PRV-1", "claim_date": summary_date, "claims": count}}
    (tmp_path / "generation_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (tmp_path / "claims.csv").write_text(
        "claim_id,provider_id,claim_date\nC1,PRV-1,2024-12-26\nC2,PRV-1,2024-12-26\n"
        "C3,PRV-1,2024-12-27\nC4,PRV-2,2024-12-26\n", encoding="utf-8")


def test_load_phantom_day_claims_exact_ids(tmp_path):
    write_phantom_files(tmp_path)
    assert load_phantom_day_claims(tmp_path) == {"C1", "C2"}  # other date and other provider excluded


def test_load_phantom_day_claims_none_on_count_mismatch_or_missing(tmp_path):
    write_phantom_files(tmp_path, summary_date="26/12/2024", count=2)  # matches 0 claims, summary says 2
    assert load_phantom_day_claims(tmp_path) is None
    assert load_phantom_day_claims(tmp_path / "nowhere") is None


def test_report_lists_unexpected_extra_rule_claim_when_checked():
    results = [result("A", 40, UPCODING, RAPID_RESUBMISSION), result("B", 0)]
    truth = {"A": (True, UPCODING), "B": (False, "")}
    text = build_report(evaluate(results, truth, {"X"}), {rule: 1 for rule in ALL_RULES}, 0.5)
    unexpected = text.split("### Unexpected")[1]
    assert "| A | upcoding | rapid_resubmission |" in unexpected
    assert "could not be checked" not in text
