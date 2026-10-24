"""System tests S1, S2: weights loading reports every problem in one error."""

import json

import pytest

from rule_names import ALL_RULES
from scoring.weights import DEFAULT_PATH, WeightsError, load_weights

VALID = {rule: 3 for rule in ALL_RULES}


def write(tmp_path, data):
    path = tmp_path / "weights.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_default_weights_load_all_rules_in_order():
    weights = load_weights(DEFAULT_PATH)
    assert list(weights) == list(ALL_RULES)
    assert sum(weights.values()) == 27


def test_s1_bad_values_are_all_listed_in_one_error(tmp_path):
    bad = {
        "duplicate_claim": 0,
        "rapid_resubmission": 6,
        "upcoding": "4",
        "unbundling": True,
        "phantom_billing": 4.0,
    }
    path = write(tmp_path, {**VALID, **bad})
    with pytest.raises(WeightsError) as exc:
        load_weights(path)
    message = str(exc.value)
    assert "5 problem(s)" in message
    for fragment in [
        "duplicate_claim: weight must be an integer 1-5, got 0",
        "rapid_resubmission: weight must be an integer 1-5, got 6",
        "upcoding: weight must be an integer 1-5, got '4'",
        "unbundling: weight must be an integer 1-5, got True",
        "phantom_billing: weight must be an integer 1-5, got 4.0",
    ]:
        assert fragment in message
    for rule in ALL_RULES:
        if rule not in bad:
            assert rule not in message


def test_s2_missing_and_unknown_rules_are_named(tmp_path):
    data = {rule: 3 for rule in ALL_RULES if rule != "upcoding"}
    data["made_up_rule"] = 2
    with pytest.raises(WeightsError) as exc:
        load_weights(write(tmp_path, data))
    message = str(exc.value)
    assert "2 problem(s)" in message
    assert "upcoding: missing weight" in message
    assert "made_up_rule: unknown rule" in message


def test_s2_missing_unknown_and_bad_value_together(tmp_path):
    data = {rule: 3 for rule in ALL_RULES if rule != "upcoding"}
    data["made_up_rule"] = 2
    data["unbundling"] = 9
    with pytest.raises(WeightsError) as exc:
        load_weights(write(tmp_path, data))
    message = str(exc.value)
    assert "3 problem(s)" in message
    assert "upcoding: missing weight" in message
    assert "made_up_rule: unknown rule" in message
    assert "unbundling: weight must be an integer 1-5, got 9" in message


def test_valid_custom_weights_are_returned(tmp_path):
    assert load_weights(write(tmp_path, {**VALID, "upcoding": 5}))["upcoding"] == 5


def test_non_object_and_invalid_json_raise_weights_error(tmp_path):
    with pytest.raises(WeightsError):
        load_weights(write(tmp_path, [1, 2]))
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    with pytest.raises(WeightsError):
        load_weights(broken)
    with pytest.raises(WeightsError):
        load_weights(tmp_path / "missing.json")


def test_duplicate_json_key_is_reported_even_if_last_value_is_valid(tmp_path):
    path = tmp_path / "weights.json"
    text = json.dumps({**VALID, "upcoding": 9})
    path.write_text(text[:-1] + ', "upcoding": 4}', encoding="utf-8")
    with pytest.raises(WeightsError) as exc:
        load_weights(path)
    message = str(exc.value)
    assert "upcoding: duplicate key" in message
