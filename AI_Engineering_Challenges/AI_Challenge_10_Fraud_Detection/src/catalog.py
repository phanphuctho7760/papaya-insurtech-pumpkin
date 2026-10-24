"""Load and validate the shared catalog (procedures, bundles, diagnoses, valid pairs).

Both the dataset generator and the rule engine read the catalog through this module,
so they can never disagree on prices, bundle contents or valid diagnosis-procedure pairs.
"""

import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PATH = Path(__file__).parent / "config" / "catalog.json"
CLAIM_TYPES = ("OUTPATIENT", "INPATIENT", "DENTAL")


class CatalogError(ValueError):
    """Raised when catalog.json is inconsistent. The message lists every problem found."""


@dataclass(frozen=True)
class Procedure:
    code: str
    name: str
    claim_type: str
    standard_price: int
    surgical: bool


@dataclass(frozen=True)
class Bundle:
    code: str
    name: str
    claim_type: str
    components: tuple[str, ...]
    standard_price: int
    surgical: bool


@dataclass(frozen=True)
class Diagnosis:
    code: str
    name: str
    claim_type: str


@dataclass(frozen=True)
class Catalog:
    procedures: dict[str, Procedure]
    bundles: dict[str, Bundle]
    diagnoses: dict[str, Diagnosis]
    valid_pairs: dict[str, frozenset[str]]  # diagnosis code -> valid procedure / bundle codes

    def billable(self, code: str) -> Procedure | Bundle:
        """Return the procedure or bundle for a code that can appear in procedure_codes."""
        return self.procedures.get(code) or self.bundles[code]

    def all_billable_codes(self) -> list[str]:
        return list(self.procedures) + list(self.bundles)

    def is_valid_pair(self, diagnosis_code: str, code: str) -> bool:
        return code in self.valid_pairs.get(diagnosis_code, frozenset())

    def diagnoses_for(self, code: str) -> list[str]:
        """Diagnoses for which a procedure / bundle code is clinically valid, in catalog order."""
        return [dx for dx, codes in self.valid_pairs.items() if code in codes]

    def components_price(self, bundle_code: str) -> int:
        """Sum of the standard prices of a bundle's components (the unbundled price)."""
        return sum(self.procedures[c].standard_price for c in self.bundles[bundle_code].components)


def load_catalog(path: Path = DEFAULT_PATH) -> Catalog:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    catalog = Catalog(
        procedures={
            code: Procedure(code, p["name"], p["claim_type"], p["standard_price"], p["surgical"])
            for code, p in raw["procedures"].items()
        },
        bundles={
            code: Bundle(code, b["name"], b["claim_type"], tuple(b["components"]), b["standard_price"], b["surgical"])
            for code, b in raw["bundles"].items()
        },
        diagnoses={
            code: Diagnosis(code, d["name"], d["claim_type"])
            for code, d in raw["diagnoses"].items()
        },
        valid_pairs={dx: frozenset(codes) for dx, codes in raw["valid_pairs"].items()},
    )
    problems = validate(catalog)
    if problems:
        raise CatalogError(f"{path}: {len(problems)} problem(s)\n- " + "\n- ".join(problems))
    return catalog


def validate(catalog: Catalog) -> list[str]:
    """Return a list of human-readable problems; an empty list means the catalog is consistent."""
    problems = []
    procedures, bundles = catalog.procedures, catalog.bundles

    for code in procedures.keys() & bundles.keys():
        problems.append(f"{code} is defined both as a procedure and as a bundle")

    for item in [*procedures.values(), *bundles.values(), *catalog.diagnoses.values()]:
        if item.claim_type not in CLAIM_TYPES:
            problems.append(f"{item.code}: unknown claim_type {item.claim_type!r}")

    for item in [*procedures.values(), *bundles.values()]:
        if not isinstance(item.standard_price, int) or item.standard_price <= 0:
            problems.append(f"{item.code}: standard_price must be a positive integer, got {item.standard_price!r}")

    for bundle in bundles.values():
        if len(bundle.components) < 2:
            problems.append(f"{bundle.code}: a bundle needs at least 2 components")
        missing = [c for c in bundle.components if c not in procedures]
        if missing:
            problems.append(f"{bundle.code}: unknown component(s) {missing}")
            continue
        other_types = [c for c in bundle.components if procedures[c].claim_type != bundle.claim_type]
        if other_types:
            problems.append(f"{bundle.code}: component(s) {other_types} are not {bundle.claim_type}")
        if bundle.standard_price >= catalog.components_price(bundle.code):
            problems.append(f"{bundle.code}: bundle price must be lower than the sum of its components")

    for dx, codes in catalog.valid_pairs.items():
        if dx not in catalog.diagnoses:
            problems.append(f"valid_pairs: unknown diagnosis {dx}")
        unknown = sorted(c for c in codes if c not in procedures and c not in bundles)
        if unknown:
            problems.append(f"valid_pairs[{dx}]: unknown code(s) {unknown}")

    for dx in catalog.diagnoses:
        if not catalog.valid_pairs.get(dx):
            problems.append(f"{dx}: diagnosis has no valid procedure")

    # An unbundled claim lists every component of the bundle with the bundle's diagnosis.
    # If a component is not valid for that diagnosis, the claim would also trip the mismatch rule.
    for dx, codes in catalog.valid_pairs.items():
        for code in codes & bundles.keys():
            invalid = [c for c in bundles[code].components if c not in codes]
            if invalid:
                problems.append(f"{dx} is valid for {code} but not for its component(s) {invalid}")

    return problems
