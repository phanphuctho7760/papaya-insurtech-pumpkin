"""Business test cases TC01-TC19 (docs/business-rule/test-cases.md): one function per table row.

Unit level: each rule is called directly with claims built in the test; TC18/TC19 go through score_claims.
"""

from datetime import date, timedelta

import pytest

from catalog import load_catalog
from claims import Claim
from rules import RULES
from scoring.score import risk_score, score_claims
from scoring.weights import load_weights

TUE = date(2024, 3, 12)  # a Tuesday
SAT = date(2024, 3, 16)  # a Saturday


@pytest.fixture(scope="module")
def catalog():
    return load_catalog()


def make_claim(claim_id, day=TUE, member="MEM-0001", provider="PRV-001", diagnosis="J06.9", codes=("P-1001",), amount=100_000):
    return Claim(
        claim_id=claim_id, member_id=member, provider_id=provider, provider_name="Test provider",
        claim_date=day, claim_type="OUTPATIENT", diagnosis_code=diagnosis, procedure_codes=tuple(codes),
        submitted_amount=amount, is_weekend=day.weekday() >= 5,
    )


def flagged_ids(rule, claims, catalog):
    return set(RULES[rule](claims, catalog))


def upcoding_claims(total):
    """`total` single-code P-1001 claims plus one multi-code claim that must be ignored.

    For total = 10: 8 x 100,000, MID 150,000, OUTLIER 152,000 gives
      mean 110,200, pstdev 20,404.9 (stdev 21,508.7)
      threshold with pstdev = 151,009.8, with stdev = 153,217.3
    so MID (between mean + 1 SD and mean + 2 SD) is not flagged, and OUTLIER is flagged
    only by the population SD. The multi-code claim (5,000,000) would wreck mean/SD if it were counted.
    """
    claims = [make_claim(f"C{i}", member=f"MEM-{i:04d}", amount=100_000) for i in range(total - 2)]
    claims.append(make_claim("MID", member="MEM-9998", amount=150_000))
    claims.append(make_claim("OUTLIER", member="MEM-9999", amount=152_000))
    claims.append(make_claim("MULTI", member="MEM-9997", codes=("P-1001", "P-1002"), amount=5_000_000))
    return claims


def provider_day_claims(count):
    return [make_claim(f"C{i}", member=f"MEM-{i:04d}") for i in range(count)]


def weekend_provider_claims(weekend_codes):
    """30 claims of one provider: 29 on weekdays, 1 weekend claim (3.3%) billing weekend_codes."""
    claims = [make_claim(f"C{i}", member=f"MEM-{i:04d}") for i in range(29)]
    claims.append(make_claim("WEEKEND", day=SAT, member="MEM-9999", codes=weekend_codes))
    return claims


def test_tc01_duplicate_same_unique_key_flags_both(catalog):
    """Two claims sharing the unique key are both flagged, and nothing else."""
    claims = [make_claim("A"), make_claim("B"), make_claim("OTHER", member="MEM-0002")]
    result = RULES["duplicate_claim"](claims, catalog)
    assert set(result) == {"A", "B"}
    assert "Duplicate of B:" in result["A"] and "Duplicate of A:" in result["B"]


def test_tc02_duplicate_different_provider_not_flagged(catalog):
    """Same member + date + diagnosis at a different provider is not a duplicate."""
    claims = [make_claim("A", provider="PRV-001"), make_claim("B", provider="PRV-002")]
    assert flagged_ids("duplicate_claim", claims, catalog) == set()


def test_tc03_rapid_seven_days_flagged(catalog):
    """Same member + diagnosis 7 days apart: both claims are flagged."""
    claims = [make_claim("A"), make_claim("B", day=TUE + timedelta(days=7))]
    result = RULES["rapid_resubmission"](claims, catalog)
    assert set(result) == {"A", "B"}
    assert "Re-submitted 7 days after A" in result["B"]


def test_tc04_rapid_eight_days_not_flagged(catalog):
    """Same member + diagnosis 8 days apart: no flag."""
    claims = [make_claim("A"), make_claim("B", day=TUE + timedelta(days=8))]
    assert flagged_ids("rapid_resubmission", claims, catalog) == set()


def test_tc05_rapid_skips_pair_that_is_a_duplicate(catalog):
    """A pair sharing the duplicate key is left to the duplicate rule: rapid does not flag it."""
    claims = [make_claim("A"), make_claim("B")]
    assert flagged_ids("duplicate_claim", claims, catalog) == {"A", "B"}
    assert flagged_ids("rapid_resubmission", claims, catalog) == set()


def test_tc06_upcoding_above_mean_plus_two_sd_flagged(catalog):
    """10 claims of one code, one above mean + 2 SD: only that claim is flagged (not the mid claim, not the multi-code claim)."""
    result = RULES["upcoding"](upcoding_claims(10), catalog)
    assert set(result) == {"OUTLIER"}
    assert "152,000" in result["OUTLIER"] and "P-1001" in result["OUTLIER"]


def test_tc07_upcoding_code_with_fewer_than_ten_claims_skipped(catalog):
    """A code with only 9 claims is not evaluated, so nothing is flagged.

    8 x 100,000 + 1 x 200,000: mean 111,111.1, pstdev 31,427.0, the outlier sits 2.83 SD above the mean,
    so it would be flagged if the code were evaluated.
    """
    claims = [make_claim(f"C{i}", member=f"MEM-{i:04d}", amount=100_000) for i in range(8)]
    claims.append(make_claim("OUTLIER", member="MEM-9999", amount=200_000))
    assert flagged_ids("upcoding", claims, catalog) == set()


def test_tc08_unbundling_all_components_flagged(catalog):
    """A claim billing every component of bundle B-1001 is flagged; a claim with one code is not."""
    claims = [
        make_claim("BUNDLED", codes=("P-1001", "P-1002", "P-1003"), amount=340_000),
        make_claim("PLAIN", member="MEM-0002", codes=("P-1001",)),
    ]
    result = RULES["unbundling"](claims, catalog)
    assert set(result) == {"BUNDLED"}
    assert "B-1001" in result["BUNDLED"]


def test_tc09_unbundling_missing_component_not_flagged(catalog):
    """A claim missing one component of the bundle is not flagged."""
    claims = [make_claim("A", codes=("P-1001", "P-1002"))]
    assert flagged_ids("unbundling", claims, catalog) == set()


def test_tc10_phantom_31_claims_in_a_day_flagged(catalog):
    """A provider with 31 claims on one day: all 31 are flagged."""
    claims = provider_day_claims(31)
    result = RULES["phantom_billing"](claims, catalog)
    assert set(result) == {c.claim_id for c in claims}
    assert "31 claims" in result["C0"]


def test_tc11_phantom_exactly_30_claims_not_flagged(catalog):
    """Exactly 30 claims in a day is within the limit: no flag."""
    assert flagged_ids("phantom_billing", provider_day_claims(30), catalog) == set()


def test_tc12_weekend_surgical_at_low_weekend_provider_flagged(catalog):
    """A surgical weekend claim at a provider with 3.3% weekend claims is flagged; at exactly 5% it is not."""
    at_five_percent = [make_claim(f"F{i}", provider="PRV-002", member=f"MEM-{i:04d}") for i in range(19)]
    at_five_percent.append(make_claim("FIVE", day=SAT, provider="PRV-002", member="MEM-9999", codes=("P-3001",)))
    claims = weekend_provider_claims(("P-3001",)) + at_five_percent
    result = RULES["weekend_anomaly"](claims, catalog)
    assert set(result) == {"WEEKEND"}
    assert "P-3001" in result["WEEKEND"] and "3.3%" in result["WEEKEND"]


def test_tc13_weekend_non_surgical_not_flagged(catalog):
    """A weekend claim without a surgical code is not flagged, even at the same 3.3% ratio."""
    assert flagged_ids("weekend_anomaly", weekend_provider_claims(("P-1001",)), catalog) == set()


def test_tc14_mismatch_caries_with_appendectomy_flagged(catalog):
    """Diagnosis K02.1 billed with procedure P-3001 is flagged."""
    claims = [make_claim("A", diagnosis="K02.1", codes=("P-3001",))]
    result = RULES["diagnosis_procedure_mismatch"](claims, catalog)
    assert set(result) == {"A"}
    assert "P-3001" in result["A"] and "K02.1" in result["A"]


def test_tc15_mismatch_valid_pair_not_flagged(catalog):
    """A valid diagnosis-procedure pair is not flagged."""
    claims = [make_claim("A", diagnosis="K02.1", codes=("P-4001",))]
    assert flagged_ids("diagnosis_procedure_mismatch", claims, catalog) == set()


@pytest.mark.parametrize("amount", [47_500, 49_999])
def test_tc16_clustering_inside_band_flagged(catalog, amount):
    """Amounts 47,500 and 49,999 (inside the 5% band below 50,000) are flagged."""
    result = RULES["amount_clustering"]([make_claim("A", amount=amount)], catalog)
    assert set(result) == {"A"}
    assert f"Amount {amount:,} VND" in result["A"]


@pytest.mark.parametrize("amount", [47_499, 50_000])
def test_tc17_clustering_outside_band_not_flagged(catalog, amount):
    """Amounts 47,499 and 50,000 (just outside the band) are not flagged."""
    assert flagged_ids("amount_clustering", [make_claim("A", amount=amount)], catalog) == set()


def test_tc18_scoring_total_six_gives_78(catalog):
    """Total severity 6 (mismatch 4 + clustering 2) -> risk_score 78 with exactly those 2 flags."""
    assert risk_score(6) == 78
    claim = make_claim("A", diagnosis="K02.1", codes=("P-3001",), amount=49_000)
    [result] = score_claims([claim], catalog, load_weights())
    assert result["risk_score"] == 78
    assert {f["rule"]: f["severity"] for f in result["flags"]} == {
        "diagnosis_procedure_mismatch": 4, "amount_clustering": 2,
    }


def test_tc19_scoring_no_flags_gives_zero(catalog):
    """A clean claim has risk_score 0 and an empty flags list."""
    [result] = score_claims([make_claim("A")], catalog, load_weights())
    assert result["risk_score"] == 0
    assert result["flags"] == []
