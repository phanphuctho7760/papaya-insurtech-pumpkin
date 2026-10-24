"""Data types shared by the generator steps: providers and claims before claim_id is assigned."""

import json
import random
from dataclasses import dataclass
from datetime import date
from pathlib import Path

PROVIDERS_PATH = Path(__file__).parent.parent / "config" / "providers.json"
WEEKDAY_ONLY_COUNT = 10

# Which provider types may bill each claim type.
ELIGIBLE_PROVIDER_TYPES = {
    "OUTPATIENT": ("HOSPITAL", "CLINIC"),
    "INPATIENT": ("HOSPITAL",),
    "DENTAL": ("DENTAL",),
}


@dataclass(frozen=True)
class Provider:
    id: str
    name: str
    type: str  # HOSPITAL / CLINIC / DENTAL


@dataclass
class GeneratedClaim:
    member_id: str
    provider: Provider
    claim_date: date
    claim_type: str
    diagnosis_code: str
    procedure_codes: tuple[str, ...]
    submitted_amount: int
    fraud_pattern: str | None = None  # None = legitimate claim

    @property
    def is_weekend(self) -> bool:
        return self.claim_date.weekday() >= 5

    def duplicate_key(self) -> tuple[str, str, date, str]:
        """Unique key used by the duplicate rule: (member, provider, date, diagnosis)."""
        return (self.member_id, self.provider.id, self.claim_date, self.diagnosis_code)


def load_providers(path: Path = PROVIDERS_PATH) -> list[Provider]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return [Provider(p["id"], p["name"], p["type"]) for p in raw["providers"]]


def pick_weekday_only(rng: random.Random, providers: list[Provider]) -> list[Provider]:
    """Pick the hospitals that never operate on weekends. Kept out of providers.json on purpose:
    the engine must discover them from the data, not from config."""
    hospitals = [p for p in providers if p.type == "HOSPITAL"]
    return sorted(rng.sample(hospitals, WEEKDAY_ONLY_COUNT), key=lambda p: p.id)
