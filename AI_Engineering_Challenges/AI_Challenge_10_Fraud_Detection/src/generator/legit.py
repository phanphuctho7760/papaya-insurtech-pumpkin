"""Phase 2: generate the 1,800 legitimate claims."""

import math
import random
from datetime import date, timedelta

from catalog import Catalog
from generator.models import ELIGIBLE_PROVIDER_TYPES, GeneratedClaim, Provider

YEAR_START = date(2024, 1, 1)
DAYS_IN_YEAR = 366  # 2024 is a leap year

MEMBER_IDS = [f"MEM-{i:04d}" for i in range(1, 501)]

# Exact number of legitimate claims per code (sum = 1,800). Outpatient is the most frequent (it feeds
# the 20 hospitals evenly), every code gets >= 30 claims (upcoding needs history), and 18 codes
# besides P-1003 get >= 60 (P-3002 and P-3010 are the two below 60) so the 27 upcoded claims can be
# spread at most 2 per code (see upcoding.md, masking).
LEGIT_CLAIMS_PER_CODE = {
    "P-1001": 240, "P-1002": 160, "P-1003": 90, "P-1004": 110, "P-1005": 100, "P-1006": 100,
    "B-1001": 130, "B-1002": 80,
    "P-2001": 70, "P-2002": 70, "P-3001": 60, "P-3002": 50, "P-3003": 70, "P-3010": 40,
    "B-3101": 70, "B-3102": 60,
    "P-4001": 60, "P-4002": 60, "P-4003": 60, "P-4004": 60, "B-4101": 60,
}
LEGIT_TOTAL = 1800

# Every one of the 20 hospitals first gets a random number of OUTPATIENT / INPATIENT claims drawn
# from this one range, weekday-only or not, so the weekday-only ones cannot be told apart by volume.
# The lower bound keeps a weekday-only hospital at >= 60 in total (>= 58 legit + 2 weekend frauds,
# so the 2 weekend frauds stay below the 5% weekend-volume threshold). The rest of the claims are
# spread over all eligible providers with no exception.
HOSPITAL_PREASSIGNED_RANGE = (58, 62)

AMOUNT_SIGMA = 0.15  # log-normal spread of legitimate amounts around the standard price
AMOUNT_ROUNDING = 100  # VND; same rounding for every claim so the format does not leak labels


def round_amount(amount: float) -> int:
    return max(AMOUNT_ROUNDING, round(amount / AMOUNT_ROUNDING) * AMOUNT_ROUNDING)


def random_date(rng: random.Random, weekdays_only: bool) -> date:
    while True:
        day = YEAR_START + timedelta(days=rng.randrange(DAYS_IN_YEAR))
        if not weekdays_only or day.weekday() < 5:
            return day


def generate_legit_claims(
    rng: random.Random,
    catalog: Catalog,
    providers: list[Provider],
    weekday_only: list[Provider],
) -> list[GeneratedClaim]:
    assert sum(LEGIT_CLAIMS_PER_CODE.values()) == LEGIT_TOTAL
    assert set(LEGIT_CLAIMS_PER_CODE) == set(catalog.all_billable_codes())

    codes = [code for code, n in LEGIT_CLAIMS_PER_CODE.items() for _ in range(n)]
    rng.shuffle(codes)

    # The first OUTPATIENT / INPATIENT codes go to the hospitals (same range for all 20),
    # every other claim picks any eligible provider.
    hospitals = [p for p in providers if p.type == "HOSPITAL"]
    preassigned = [p for p in hospitals for _ in range(rng.randint(*HOSPITAL_PREASSIGNED_RANGE))]
    weekday_only_ids = {p.id for p in weekday_only}
    eligible_by_type = {
        claim_type: [p for p in providers if p.type in types]
        for claim_type, types in ELIGIBLE_PROVIDER_TYPES.items()
    }

    claims = []
    used_keys = set()
    for code in codes:
        claim_type = catalog.billable(code).claim_type
        if preassigned and claim_type in ("OUTPATIENT", "INPATIENT"):
            provider = preassigned.pop()
        else:
            provider = rng.choice(eligible_by_type[claim_type])

        member_id = rng.choice(MEMBER_IDS)
        diagnosis = rng.choice(catalog.diagnoses_for(code))
        price = catalog.billable(code).standard_price
        amount = round_amount(price * math.exp(rng.gauss(0, AMOUNT_SIGMA)))

        # Never create an accidental duplicate: re-draw the date until the key is new.
        while True:
            claim = GeneratedClaim(
                member_id=member_id,
                provider=provider,
                claim_date=random_date(rng, weekdays_only=provider.id in weekday_only_ids),
                claim_type=claim_type,
                diagnosis_code=diagnosis,
                procedure_codes=(code,),
                submitted_amount=amount,
            )
            if claim.duplicate_key() not in used_keys:
                break
        used_keys.add(claim.duplicate_key())
        claims.append(claim)

    assert not preassigned, "not enough OUTPATIENT / INPATIENT codes to pre-assign the hospitals"
    return claims
