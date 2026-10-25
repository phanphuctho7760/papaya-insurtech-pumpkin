"""Compare scored claims with the ground truth. Pure functions on lists. Spec: docs/business-rule/metrics.md.

Only this package may read ground_truth.csv; the engine never sees it.
"""

import csv
import json
from pathlib import Path
from typing import Callable

from generator.dataset import GROUND_TRUTH_COLUMNS
from rule_names import ALL_RULES, PHANTOM_BILLING

MAIN_PREDICATE: Callable[[int], bool] = lambda score: score > 0
THRESHOLDS: list[tuple[str, Callable[[int], bool]]] = [
    ("> 0", lambda score: score > 0),
    (">= 40", lambda score: score >= 40),
    (">= 70", lambda score: score >= 70),
]
SAMPLE_IDS = 5


class GroundTruthError(ValueError):
    """Raised when ground_truth.csv is invalid or does not match the scored claims. The message lists every problem."""


def load_ground_truth(path: Path) -> dict[str, tuple[bool, str]]:
    """Return claim_id -> (is_fraud, pattern); pattern is "" for a legit claim."""
    try:
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
    except (OSError, UnicodeDecodeError) as exc:
        raise GroundTruthError(f"{path}: cannot read file: {exc}") from exc
    except csv.Error as exc:
        raise GroundTruthError(f"{path}: not valid CSV: {exc}") from exc

    problems = []
    if not rows or rows[0] != GROUND_TRUTH_COLUMNS:
        found = rows[0] if rows else "an empty file"
        problems.append(f"line 1: header must be {GROUND_TRUTH_COLUMNS}, got {found}")

    truth: dict[str, tuple[bool, str]] = {}
    for line, row in enumerate(rows[1:], start=2):
        if not row:
            continue
        if len(row) != len(GROUND_TRUTH_COLUMNS):
            problems.append(f"line {line}: expected {len(GROUND_TRUTH_COLUMNS)} fields, got {len(row)}")
            continue
        claim_id, is_fraud, pattern = row
        if is_fraud not in ("0", "1"):
            problems.append(f"line {line}: is_fraud must be 0 or 1, got {is_fraud!r}")
            continue
        if is_fraud == "1" and pattern not in ALL_RULES:
            problems.append(f"line {line}: fraud claim {claim_id} has unknown fraud_pattern {pattern!r}")
            continue
        if is_fraud == "0" and pattern:
            problems.append(f"line {line}: legit claim {claim_id} must have an empty fraud_pattern, got {pattern!r}")
            continue
        if claim_id in truth:
            problems.append(f"line {line}: duplicate claim_id {claim_id}")
            continue
        truth[claim_id] = (is_fraud == "1", pattern)

    if problems:
        raise GroundTruthError(f"{path}: {len(problems)} problem(s)\n" + "\n".join(f"- {p}" for p in problems))
    return truth


def check_same_claims(truth: dict[str, tuple[bool, str]], results: list[dict]) -> None:
    """The ground truth and the scored output must cover exactly the same claim_ids."""
    scored = {r["claim_id"] for r in results}
    missing = sorted(scored - truth.keys())  # scored but absent from the ground truth
    extra = sorted(truth.keys() - scored)  # in the ground truth but never scored
    problems = []
    if missing:
        problems.append(f"{len(missing)} scored claim(s) missing from ground truth, e.g. {', '.join(missing[:SAMPLE_IDS])}")
    if extra:
        problems.append(f"{len(extra)} ground-truth claim(s) not scored, e.g. {', '.join(extra[:SAMPLE_IDS])}")
    if problems:
        raise GroundTruthError("ground truth does not match the scored claims\n" + "\n".join(f"- {p}" for p in problems))


def ratio(numerator: int, denominator: int) -> float:
    """numerator / denominator, or 0.0 when the denominator is 0 (e.g. precision with no predictions)."""
    return numerator / denominator if denominator else 0.0


def confusion(results: list[dict], truth: dict[str, tuple[bool, str]], predicate: Callable[[int], bool] = MAIN_PREDICATE) -> dict:
    """TP / FP / FN / TN plus precision, recall, FPR at the given score predicate."""
    tp = fp = fn = tn = 0
    for r in results:
        predicted = predicate(r["risk_score"])
        actual = truth[r["claim_id"]][0]
        if predicted and actual:
            tp += 1
        elif predicted:
            fp += 1
        elif actual:
            fn += 1
        else:
            tn += 1
    return {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": ratio(tp, tp + fp),
        "recall": ratio(tp, tp + fn),
        "fpr": ratio(fp, fp + tn),
    }


def threshold_table(results: list[dict], truth: dict[str, tuple[bool, str]]) -> list[dict]:
    """One confusion row per threshold, with its label."""
    return [{"threshold": label, **confusion(results, truth, predicate)} for label, predicate in THRESHOLDS]


def by_pattern(results: list[dict], truth: dict[str, tuple[bool, str]]) -> list[dict]:
    """Per pattern (ALL_RULES order): fraud claims, caught (score > 0), caught by their own rule."""
    rows = []
    for pattern in ALL_RULES:
        total = caught = own = 0
        for r in results:
            is_fraud, claim_pattern = truth[r["claim_id"]]
            if not is_fraud or claim_pattern != pattern:
                continue
            total += 1
            caught += MAIN_PREDICATE(r["risk_score"])
            own += any(f["rule"] == pattern for f in r["flags"])
        rows.append({"pattern": pattern, "fraud": total, "caught": caught, "caught_by_own_rule": own})
    return rows


def natural_fp_by_rule(results: list[dict], truth: dict[str, tuple[bool, str]]) -> dict:
    """Per rule: flags, flags on fraud claims, flags on legit claims (FP). An FP claim with 2 rules counts under both.

    Returns {"rows": [...], "fp_claims": number of distinct FP claims}.
    """
    counts = {rule: {"flags": 0, "on_fraud": 0, "on_legit": 0} for rule in ALL_RULES}
    fp_claims = 0
    for r in results:
        is_fraud = truth[r["claim_id"]][0]
        if not is_fraud and MAIN_PREDICATE(r["risk_score"]):
            fp_claims += 1
        for flag in r["flags"]:
            row = counts[flag["rule"]]
            row["flags"] += 1
            row["on_fraud" if is_fraud else "on_legit"] += 1
    rows = [{"rule": rule, **counts[rule]} for rule in ALL_RULES]
    return {"rows": rows, "fp_claims": fp_claims}


def extra_rule_claims(results: list[dict], truth: dict[str, tuple[bool, str]]) -> list[tuple[str, str, list[str]]]:
    """Fraud claims flagged by rules outside their own pattern: (claim_id, pattern, extra rules), in claim_id order."""
    found = []
    for r in results:
        is_fraud, pattern = truth[r["claim_id"]]
        extras = [f["rule"] for f in r["flags"] if f["rule"] != pattern]
        if is_fraud and extras:
            found.append((r["claim_id"], pattern, extras))
    return sorted(found)


def load_phantom_day_claims(data_dir: Path) -> set[str] | None:
    """claim_ids on the phantom provider-day (generation_summary.json + claims.csv), or None if it cannot be determined."""
    try:
        day = json.loads((Path(data_dir) / "generation_summary.json").read_text(encoding="utf-8"))["phantom_provider_day"]
        provider_id, claim_date = day["provider_id"], day["claim_date"]
        with open(Path(data_dir) / "claims.csv", newline="", encoding="utf-8") as f:
            ids = {row["claim_id"] for row in csv.DictReader(f)
                   if row["provider_id"] == provider_id and row["claim_date"] == claim_date}
        return ids if len(ids) == day["claims"] else None  # a count mismatch means the match is wrong (e.g. date format)
    except (OSError, ValueError, KeyError, TypeError, csv.Error):
        return None


def split_extra_rules(extras: list[tuple[str, str, list[str]]], phantom_ids: set[str] | None) -> dict:
    """Expected = on the phantom provider-day and the only extra rule is phantom_billing; everything else is unexpected."""
    ids = phantom_ids or set()
    expected = [e for e in extras if e[0] in ids and e[2] == [PHANTOM_BILLING]]
    unexpected = [e for e in extras if e not in expected]
    return {"expected": expected, "unexpected": unexpected, "checked": phantom_ids is not None}


def evaluate(results: list[dict], truth: dict[str, tuple[bool, str]], phantom_ids: set[str] | None = None) -> dict:
    """All four report parts plus the extra-rule lists. Raises GroundTruthError if the claim sets differ."""
    check_same_claims(truth, results)
    return {
        "overall": confusion(results, truth),
        "by_pattern": by_pattern(results, truth),
        "natural_fp": natural_fp_by_rule(results, truth),
        "thresholds": threshold_table(results, truth),
        "extra_rules": split_extra_rules(extra_rule_claims(results, truth), phantom_ids),
    }
