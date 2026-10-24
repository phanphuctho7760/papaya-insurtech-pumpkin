"""Phase 3: inject the 200 fraudulent claims (docs/business-rule/fraud-injection.md).

Every fraud claim carries exactly one pattern. Besides building its own pattern, each claim is
placed so it does not trip another rule by accident: no new duplicate key, no other claim of the
same member + diagnosis within 7 days, no weekend claim at a weekday-only hospital, and amounts of
non-amount patterns stay within +-15% of the price.
"""

import math
import random
from collections import Counter, defaultdict
from collections.abc import Collection
from dataclasses import dataclass
from datetime import date, timedelta

import rule_names as R
from catalog import Catalog
from generator.legit import AMOUNT_SIGMA, LEGIT_CLAIMS_PER_CODE, MEMBER_IDS, YEAR_START, DAYS_IN_YEAR, random_date, round_amount
from generator.models import GeneratedClaim, Provider

FRAUD_COUNTS = {
    R.DUPLICATE_CLAIM: 30,
    R.RAPID_RESUBMISSION: 30,
    R.UPCODING: 30,
    R.UNBUNDLING: 25,
    R.PHANTOM_BILLING: 25,
    R.WEEKEND_ANOMALY: 20,
    R.DIAGNOSIS_PROCEDURE_MISMATCH: 20,
    R.AMOUNT_CLUSTERING: 20,
}

RAPID_WINDOW_DAYS = 7
AMOUNT_FACTOR_RANGE = (0.85, 1.15)  # ~ +-1 SD; factors are re-drawn until inside (truncated, no pile-up at the edges)
UPCODING_FACTOR = (1.6, 2.5)  # x standard price, well above mean + 2 SD (~1.3x)
UPCODING_MIN_CLAIMS = 60  # only codes with this many legit claims, so 2 upcoded claims cannot mask each other
UPCODING_MAX_PER_CODE = 2
CLUSTERING_CODE = "P-1003"
CLUSTERING_DIAGNOSIS = "N39.0"
CLUSTERING_AMOUNT = (47_500, 49_999)
PHANTOM_CLAIMS = 25
PHANTOM_DAY_EXTRAS = 3  # upcoding claims and mismatch claims each, on the phantom provider-day
WEEKEND_PER_PROVIDER = 2
MAX_ATTEMPTS = 10_000


@dataclass(frozen=True)
class FraudResult:
    claims: list[GeneratedClaim]
    phantom_provider: Provider
    phantom_date: date


class _Injector:
    def __init__(self, rng: random.Random, catalog: Catalog,
                 weekday_only: list[Provider], legit: list[GeneratedClaim]):
        self.rng = rng
        self.catalog = catalog
        self.weekday_only_ids = {p.id for p in weekday_only}
        self.claims: list[GeneratedClaim] = []
        self.keys = set()
        self.dates_by_member_dx = defaultdict(list)
        self.provider_days = Counter()
        # Provider of every legit claim, per claim type (list, so draws follow legit volume and stay deterministic).
        self.legit_providers = defaultdict(list)
        for claim in legit:
            self.legit_providers[claim.claim_type].append(claim.provider)
            self._index(claim)

    # --- bookkeeping -------------------------------------------------------------------------

    def _index(self, claim: GeneratedClaim) -> None:
        self.keys.add(claim.duplicate_key())
        self.dates_by_member_dx[(claim.member_id, claim.diagnosis_code)].append(claim.claim_date)
        self.provider_days[(claim.provider.id, claim.claim_date)] += 1

    def _rapid_conflict(self, member_id: str, dx: str, day: date) -> bool:
        return any(abs((d - day).days) <= RAPID_WINDOW_DAYS for d in self.dates_by_member_dx[(member_id, dx)])

    def _is_free(self, member_id: str, provider: Provider, day: date, dx: str) -> bool:
        return (member_id, provider.id, day, dx) not in self.keys and not self._rapid_conflict(member_id, dx, day)

    def _add(self, pattern: str, member_id: str, provider: Provider, day: date, dx: str,
             codes: tuple[str, ...], amount: int) -> None:
        claim = GeneratedClaim(
            member_id=member_id,
            provider=provider,
            claim_date=day,
            claim_type=self.catalog.billable(codes[0]).claim_type,
            diagnosis_code=dx,
            procedure_codes=codes,
            submitted_amount=amount,
            fraud_pattern=pattern,
        )
        self._index(claim)
        self.claims.append(claim)

    # --- random choices ----------------------------------------------------------------------

    def _provider(self, claim_type: str, exclude: Collection[str] = ()) -> Provider:
        """Weighted by legit volume: the provider of a random legit claim of this type, so fraud does
        not over-use small providers (which would leak the label through the provider type)."""
        eligible = [p for p in self.legit_providers[claim_type] if p.id not in exclude]
        if not eligible:
            raise RuntimeError(f"no legit {claim_type} claim to take a provider from (exclude={sorted(exclude)})")
        return self.rng.choice(eligible)

    def _weekday_date(self, provider: Provider) -> date:
        return random_date(self.rng, weekdays_only=provider.id in self.weekday_only_ids)

    def _free_member(self, provider: Provider, day: date, dx: str) -> str:
        for _ in range(MAX_ATTEMPTS):
            member_id = self.rng.choice(MEMBER_IDS)
            if self._is_free(member_id, provider, day, dx):
                return member_id
        raise RuntimeError(f"no free member for {provider.id} {day} {dx}")

    def _normal_amount(self, price: int) -> int:
        while True:
            factor = math.exp(self.rng.gauss(0, AMOUNT_SIGMA))
            if AMOUNT_FACTOR_RANGE[0] <= factor <= AMOUNT_FACTOR_RANGE[1]:
                return round_amount(price * factor)

    def _single_code_claim(self, pattern: str, code: str, dx: str, amount: int,
                           provider: Provider | None = None, day: date | None = None) -> None:
        """Add one single-code claim; provider and date are drawn when not given."""
        provider = provider or self._provider(self.catalog.billable(code).claim_type)
        day = day or self._weekday_date(provider)
        self._add(pattern, self._free_member(provider, day, dx), provider, day, dx, (code,), amount)

    def _mismatch_pair(self, claim_type: str) -> tuple[str, str]:
        """A diagnosis plus a procedure of the same claim type that is not valid for it (no bundles)."""
        diagnoses = [dx for dx, d in self.catalog.diagnoses.items() if d.claim_type == claim_type]
        while True:
            dx = self.rng.choice(diagnoses)
            invalid = [code for code, p in self.catalog.procedures.items()
                       if p.claim_type == claim_type and not self.catalog.is_valid_pair(dx, code)]
            if invalid:
                return dx, self.rng.choice(invalid)

    # --- patterns ----------------------------------------------------------------------------

    def duplicates(self, pairs: int) -> None:
        for _ in range(pairs):
            code = self.rng.choice(self.catalog.all_billable_codes())
            dx = self.rng.choice(self.catalog.diagnoses_for(code))
            provider = self._provider(self.catalog.billable(code).claim_type)
            day = self._weekday_date(provider)
            member_id = self._free_member(provider, day, dx)
            price = self.catalog.billable(code).standard_price
            for _ in range(2):  # the second claim shares the key on purpose
                self._add(R.DUPLICATE_CLAIM, member_id, provider, day, dx, (code,), self._normal_amount(price))

    def rapid_resubmissions(self, pairs: int) -> None:
        for _ in range(pairs):
            dx = self.rng.choice(list(self.catalog.diagnoses))
            valid_codes = sorted(self.catalog.valid_pairs[dx])
            for _ in range(MAX_ATTEMPTS):
                first_code, second_code = self.rng.choice(valid_codes), self.rng.choice(valid_codes)
                first_provider = self._provider(self.catalog.billable(first_code).claim_type)
                second_provider = self._provider(self.catalog.billable(second_code).claim_type)
                first_day = self._weekday_date(first_provider)
                second_day = first_day + timedelta(days=self.rng.randint(1, RAPID_WINDOW_DAYS))
                if second_day.year != YEAR_START.year:
                    continue
                if second_provider.id in self.weekday_only_ids and second_day.weekday() >= 5:
                    continue
                member_id = self.rng.choice(MEMBER_IDS)
                if (self._is_free(member_id, first_provider, first_day, dx)
                        and self._is_free(member_id, second_provider, second_day, dx)):
                    break
            else:
                raise RuntimeError(f"no free rapid re-submission pair for {dx}")
            for code, provider, day in ((first_code, first_provider, first_day),
                                        (second_code, second_provider, second_day)):
                amount = self._normal_amount(self.catalog.billable(code).standard_price)
                self._add(R.RAPID_RESUBMISSION, member_id, provider, day, dx, (code,), amount)

    def unbundled(self, per_bundle: int) -> None:
        for bundle in self.catalog.bundles.values():
            for _ in range(per_bundle):
                dx = self.rng.choice(self.catalog.diagnoses_for(bundle.code))
                provider = self._provider(bundle.claim_type)
                day = self._weekday_date(provider)
                amount = self._normal_amount(self.catalog.components_price(bundle.code))
                self._add(R.UNBUNDLING, self._free_member(provider, day, dx), provider, day, dx,
                          bundle.components, amount)

    def weekend_surgeries(self, weekday_only: list[Provider]) -> None:
        surgical = [code for code in self.catalog.all_billable_codes() if self.catalog.billable(code).surgical]
        for provider in weekday_only:
            for _ in range(WEEKEND_PER_PROVIDER):
                code = self.rng.choice(surgical)
                dx = self.rng.choice(self.catalog.diagnoses_for(code))
                while True:
                    day = YEAR_START + timedelta(days=self.rng.randrange(DAYS_IN_YEAR))
                    if day.weekday() >= 5:
                        break
                amount = self._normal_amount(self.catalog.billable(code).standard_price)
                self._single_code_claim(R.WEEKEND_ANOMALY, code, dx, amount, provider, day)

    def clustered_amounts(self, count: int) -> None:
        low, high = CLUSTERING_AMOUNT
        for _ in range(count):
            amount = self.rng.randrange(low, high + 1, 100)  # 47,500 .. 49,900, same rounding as every claim
            self._single_code_claim(R.AMOUNT_CLUSTERING, CLUSTERING_CODE, CLUSTERING_DIAGNOSIS, amount)

    def upcoded(self, code: str, provider: Provider | None = None, day: date | None = None) -> None:
        dx = self.rng.choice(self.catalog.diagnoses_for(code))
        amount = round_amount(self.catalog.billable(code).standard_price * self.rng.uniform(*UPCODING_FACTOR))
        self._single_code_claim(R.UPCODING, code, dx, amount, provider, day)

    def mismatched(self, claim_type: str, provider: Provider | None = None, day: date | None = None) -> None:
        dx, code = self._mismatch_pair(claim_type)
        amount = self._normal_amount(self.catalog.procedures[code].standard_price)
        self._single_code_claim(R.DIAGNOSIS_PROCEDURE_MISMATCH, code, dx, amount, provider, day)

    def phantom_day(self, upcoding_codes: list[str]) -> tuple[Provider, date]:
        """One regular hospital on a weekday it had no claims: 25 phantom + 3 upcoding + 3 mismatch = 31."""
        provider = self._provider("INPATIENT", exclude=self.weekday_only_ids)  # INPATIENT => hospitals only
        while True:
            day = random_date(self.rng, weekdays_only=True)
            if self.provider_days[(provider.id, day)] == 0:
                break
        outpatient = [code for code in self.catalog.all_billable_codes()
                      if self.catalog.billable(code).claim_type == "OUTPATIENT"]
        for _ in range(PHANTOM_CLAIMS):
            code = self.rng.choice(outpatient)
            dx = self.rng.choice(self.catalog.diagnoses_for(code))
            amount = self._normal_amount(self.catalog.billable(code).standard_price)
            self._single_code_claim(R.PHANTOM_BILLING, code, dx, amount, provider, day)
        for code in upcoding_codes:
            self.upcoded(code, provider, day)
        for _ in range(PHANTOM_DAY_EXTRAS):
            self.mismatched("OUTPATIENT", provider, day)
        return provider, day


def _upcoding_codes(rng: random.Random, catalog: Catalog, total: int, on_phantom_day: int) -> tuple[list[str], list[str]]:
    """Spread upcoded claims over codes with >= 60 legit claims, at most 2 per code, never P-1003.
    The phantom-day share must be OUTPATIENT. Returns (regular codes, phantom-day codes)."""
    eligible = [c for c, n in LEGIT_CLAIMS_PER_CODE.items() if n >= UPCODING_MIN_CLAIMS and c != CLUSTERING_CODE]
    phantom = rng.sample([c for c in eligible if catalog.billable(c).claim_type == "OUTPATIENT"], on_phantom_day)
    slots = [c for c in eligible for _ in range(UPCODING_MAX_PER_CODE - phantom.count(c))]
    rng.shuffle(slots)
    return slots[: total - on_phantom_day], phantom


def inject_fraud(rng: random.Random, catalog: Catalog,
                 weekday_only: list[Provider], legit: list[GeneratedClaim]) -> FraudResult:
    injector = _Injector(rng, catalog, weekday_only, legit)
    regular_upcoding, phantom_upcoding = _upcoding_codes(
        rng, catalog, FRAUD_COUNTS[R.UPCODING], PHANTOM_DAY_EXTRAS)

    injector.duplicates(FRAUD_COUNTS[R.DUPLICATE_CLAIM] // 2)
    injector.rapid_resubmissions(FRAUD_COUNTS[R.RAPID_RESUBMISSION] // 2)
    injector.unbundled(FRAUD_COUNTS[R.UNBUNDLING] // len(catalog.bundles))
    injector.weekend_surgeries(weekday_only)
    injector.clustered_amounts(FRAUD_COUNTS[R.AMOUNT_CLUSTERING])
    for code in regular_upcoding:
        injector.upcoded(code)
    for _ in range(FRAUD_COUNTS[R.DIAGNOSIS_PROCEDURE_MISMATCH] - PHANTOM_DAY_EXTRAS):
        injector.mismatched(rng.choice(["OUTPATIENT", "INPATIENT", "DENTAL"]))
    # Last, so no later claim can land on the phantom provider-day and push it past 31.
    phantom_provider, phantom_date = injector.phantom_day(phantom_upcoding)

    counts = Counter(c.fraud_pattern for c in injector.claims)
    assert counts == FRAUD_COUNTS, counts
    return FraudResult(injector.claims, phantom_provider, phantom_date)
