"""Integration test on the committed dataset: the engine against ground_truth.csv. Spec: test-cases.md, metrics.md."""

import time
from pathlib import Path

import pytest

from catalog import load_catalog
from claims import load_claims
from metrics.evaluate import (
    check_same_claims,
    confusion,
    extra_rule_claims,
    load_ground_truth,
    load_phantom_day_claims,
    split_extra_rules,
)
from scoring.score import score_claims
from scoring.weights import load_weights

DATA_DIR = Path(__file__).parent.parent / "data"
MAX_SECONDS = 30
TARGET_RECALL = 0.70
TARGET_FPR = 0.20


@pytest.fixture(scope="module")
def scored():
    start = time.perf_counter()
    catalog = load_catalog()
    results = score_claims(load_claims(DATA_DIR / "claims.csv", catalog), catalog, load_weights())
    return results, time.perf_counter() - start


@pytest.fixture(scope="module")
def truth():
    return load_ground_truth(DATA_DIR / "ground_truth.csv")


def test_every_ground_truth_claim_is_scored(scored, truth):
    """A claim dropped by the loader or scorer would hide from every other test here."""
    results, _ = scored
    check_same_claims(truth, results)  # raises GroundTruthError naming the missing / extra claim_ids


def test_every_fraud_claim_triggers_its_own_rule(scored, truth):
    results, _ = scored
    missed = [
        (r["claim_id"], truth[r["claim_id"]][1])
        for r in results
        if truth[r["claim_id"]][0] and truth[r["claim_id"]][1] not in {f["rule"] for f in r["flags"]}
    ]
    assert missed == [], f"fraud claims not flagged by their own pattern's rule: {missed}"


def test_extra_rules_are_only_the_phantom_day_exception(scored, truth):
    """Fraud claims on the phantom provider-day may also trigger phantom_billing (fraud-injection.md); nothing else."""
    results, _ = scored
    phantom_ids = load_phantom_day_claims(DATA_DIR)
    assert phantom_ids is not None, "phantom provider-day could not be matched in generation_summary.json / claims.csv"
    split = split_extra_rules(extra_rule_claims(results, truth), phantom_ids)
    assert split["unexpected"] == [], f"fraud claims with an unexpected extra rule (claim, pattern, extra rules): {split['unexpected']}"


def test_recall_and_fpr_meet_the_brief_targets(scored, truth):
    results, _ = scored
    overall = confusion(results, truth)
    assert overall["recall"] >= TARGET_RECALL, f"recall {overall['recall']:.1%} < {TARGET_RECALL:.0%}"
    assert overall["fpr"] <= TARGET_FPR, f"FPR {overall['fpr']:.1%} > {TARGET_FPR:.0%}"


def test_scoring_2000_claims_takes_under_30_seconds(scored):
    results, elapsed = scored
    assert len(results) == 2000
    assert elapsed < MAX_SECONDS, f"load -> rules -> score took {elapsed:.1f} s (limit {MAX_SECONDS} s)"
