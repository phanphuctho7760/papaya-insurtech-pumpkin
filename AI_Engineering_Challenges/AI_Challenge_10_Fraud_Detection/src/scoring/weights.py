"""Load and validate the configurable severity weights (one integer 1-5 per rule).

Weights are the only configurable part of the engine (ADR-003); rule thresholds stay in code.
"""

import json
from pathlib import Path

from rule_names import ALL_RULES

DEFAULT_PATH = Path(__file__).parent.parent / "config" / "weights.json"
MIN_WEIGHT, MAX_WEIGHT = 1, 5


class WeightsError(ValueError):
    """Raised when the weights file is invalid. The message lists every problem found."""


def _object_with_duplicates(pairs):
    """object_pairs_hook: keep duplicate keys visible instead of letting the last one win silently."""
    result, duplicates = {}, []
    for key, value in pairs:
        if key in result:
            duplicates.append(key)
        result[key] = value
    return _Parsed(result, duplicates)


class _Parsed(dict):
    def __init__(self, data, duplicates):
        super().__init__(data)
        self.duplicates = duplicates


def load_weights(path: Path = DEFAULT_PATH) -> dict[str, int]:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_object_with_duplicates)
    except (OSError, ValueError) as exc:  # ValueError covers JSON and Unicode decode errors
        raise WeightsError(f"{path}: cannot read weights: {exc}") from exc
    if not isinstance(raw, dict):
        raise WeightsError(f"{path}: 1 problem(s)\n- top level must be a JSON object of rule -> weight")

    problems = [f"{key}: duplicate key" for key in raw.duplicates]
    problems += [f"{rule}: missing weight" for rule in ALL_RULES if rule not in raw]
    problems += [f"{key}: unknown rule" for key in raw if key not in ALL_RULES]
    for rule in ALL_RULES:
        if rule not in raw:
            continue
        value = raw[rule]
        # bool is a subclass of int, so it must be excluded explicitly
        if type(value) is not int or not MIN_WEIGHT <= value <= MAX_WEIGHT:
            problems.append(f"{rule}: weight must be an integer {MIN_WEIGHT}-{MAX_WEIGHT}, got {value!r}")
    if problems:
        raise WeightsError(f"{path}: {len(problems)} problem(s)\n- " + "\n- ".join(problems))
    return {rule: raw[rule] for rule in ALL_RULES}
