"""System test S6 + rule contract: every rule has the same signature and returns {claim_id: evidence}."""

import inspect
from datetime import date

import pytest

from catalog import load_catalog
from claims import Claim
from rule_names import ALL_RULES
from rules import RULES


@pytest.fixture(scope="module")
def catalog():
    return load_catalog()


def make_claim(claim_id, day, member="MEM-0001", provider="PRV-001", diagnosis="J06.9", codes=("P-1001",), amount=100_000):
    return Claim(
        claim_id=claim_id, member_id=member, provider_id=provider, provider_name="Test provider",
        claim_date=day, claim_type="OUTPATIENT", diagnosis_code=diagnosis, procedure_codes=tuple(codes),
        submitted_amount=amount, is_weekend=day.weekday() >= 5,
    )


def test_rules_are_registered_in_all_rules_order():
    assert list(RULES) == list(ALL_RULES)


@pytest.mark.parametrize("name", ALL_RULES)
def test_every_rule_has_the_shared_signature(name):
    assert list(inspect.signature(RULES[name]).parameters) == ["claims", "catalog"]


def flagging_fixture(name):
    """A tiny claim list that makes the given rule raise at least one flag."""
    d = date(2024, 3, 12)  # a Tuesday
    sat = date(2024, 3, 16)
    if name in ("duplicate_claim", "rapid_resubmission"):
        other = {"duplicate_claim": {}, "rapid_resubmission": {"provider": "PRV-002"}}[name]
        return [make_claim("CLM-00001", d), make_claim("CLM-00002", d, **other)]
    if name == "upcoding":
        base = [make_claim(f"CLM-{i:05d}", d, member=f"MEM-{i:04d}", amount=100_000) for i in range(1, 12)]
        return base + [make_claim("CLM-00099", d, member="MEM-0099", amount=900_000)]
    if name == "unbundling":
        return [make_claim("CLM-00001", d, diagnosis="K35.8", codes=("P-3001", "P-3010"), amount=21_400_000)]
    if name == "phantom_billing":
        return [make_claim(f"CLM-{i:05d}", d, member=f"MEM-{i:04d}") for i in range(1, 32)]
    if name == "weekend_anomaly":
        weekdays = [make_claim(f"CLM-{i:05d}", d, member=f"MEM-{i:04d}") for i in range(1, 30)]
        return weekdays + [make_claim("CLM-00099", sat, member="MEM-0099", diagnosis="K35.8", codes=("P-3001",))]
    if name == "diagnosis_procedure_mismatch":
        return [make_claim("CLM-00001", d, diagnosis="K02.1", codes=("P-3001",))]
    if name == "amount_clustering":
        return [make_claim("CLM-00001", d, amount=48_500)]
    raise AssertionError(f"no fixture for {name}")


@pytest.mark.parametrize("name", ALL_RULES)
def test_every_rule_returns_a_dict_of_strings(name, catalog):
    result = RULES[name](flagging_fixture(name), catalog)
    assert result  # the fixture must make the rule flag something
    assert isinstance(result, dict)
    assert all(isinstance(k, str) and isinstance(v, str) for k, v in result.items())
    assert RULES[name]([], catalog) == {}


def test_s6_claim_in_two_rapid_pairs_gets_one_evidence_naming_both(catalog):
    claims = [
        make_claim("CLM-00001", date(2024, 3, 10), provider="PRV-001"),
        make_claim("CLM-00002", date(2024, 3, 12), provider="PRV-002"),
        make_claim("CLM-00003", date(2024, 3, 14), provider="PRV-003"),
    ]
    result = RULES["rapid_resubmission"](claims, catalog)
    assert set(result) == {"CLM-00001", "CLM-00002", "CLM-00003"}
    middle = result["CLM-00002"]
    assert "CLM-00001" in middle and "CLM-00003" in middle
    assert "Re-submitted 2 days after CLM-00001 (2024-03-10)" in middle
    assert "Followed 2 days later by CLM-00003 (2024-03-14)" in middle
    assert "window: 7 days" in middle


def test_rapid_skips_duplicate_key_pairs_and_pairs_beyond_the_window(catalog):
    claims = [
        make_claim("CLM-00001", date(2024, 3, 10)),
        make_claim("CLM-00002", date(2024, 3, 10)),  # same provider + date: duplicate rule, not rapid
        make_claim("CLM-00003", date(2024, 3, 18), provider="PRV-009"),  # 8 days after: outside the window
    ]
    assert RULES["rapid_resubmission"](claims, catalog) == {}
    assert set(RULES["duplicate_claim"](claims, catalog)) == {"CLM-00001", "CLM-00002"}


def test_rapid_same_day_other_provider_wording(catalog):
    claims = [
        make_claim("CLM-00001", date(2024, 3, 10), provider="PRV-001"),
        make_claim("CLM-00002", date(2024, 3, 10), provider="PRV-002"),
    ]
    result = RULES["rapid_resubmission"](claims, catalog)
    assert result["CLM-00001"].startswith("Submitted on the same day as CLM-00002 at another provider PRV-002")


def test_rapid_one_day_gap_is_singular(catalog):
    claims = [make_claim("CLM-00001", date(2024, 3, 10)), make_claim("CLM-00002", date(2024, 3, 11), provider="PRV-002")]
    result = RULES["rapid_resubmission"](claims, catalog)
    assert "Re-submitted 1 day after CLM-00001" in result["CLM-00002"]
    assert "Followed 1 day later by CLM-00002" in result["CLM-00001"]
    assert "1 days" not in result["CLM-00001"] + result["CLM-00002"]


def test_clustering_percentage_rounds_down(catalog):
    result = RULES["amount_clustering"]([make_claim("CLM-00001", date(2024, 3, 12), amount=49_999)], catalog)
    assert "is 99% of" in result["CLM-00001"]


def test_weekend_ratio_rounds_down(catalog):
    d, sat = date(2024, 3, 12), date(2024, 3, 16)
    claims = [make_claim(f"CLM-{i:05d}", d, member=f"MEM-{i:04d}") for i in range(1, 192)]
    claims += [make_claim(f"CLM-{i:05d}", sat, member=f"MEM-{i:04d}", diagnosis="K35.8", codes=("P-3001",)) for i in range(200, 210)]
    result = RULES["weekend_anomaly"](claims, catalog)  # 10 of 201 = 4.975%
    assert len(result) == 10
    assert "4.9% (10 of 201 claims" in next(iter(result.values()))


def test_unbundling_two_bundles_gets_one_clause_each(catalog):
    codes = ("P-1001", "P-1002", "P-1003", "P-1006")  # B-1001 and B-1002 components overlap
    result = RULES["unbundling"]([make_claim("CLM-00001", date(2024, 3, 12), codes=codes, amount=520_000)], catalog)
    text = result["CLM-00001"]
    assert text.startswith("Billed 4 separate procedures for 520,000 VND: ")
    assert text.count(" instead of bundle ") == 2
    assert "B-1001 (" in text and "B-1002 (" in text
