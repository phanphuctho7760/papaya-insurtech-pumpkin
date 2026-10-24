"""System test S4: load_claims validates the whole file and reports every problem in one error."""

import csv
from datetime import date

import pytest

from catalog import load_catalog
from claims import CLAIMS_COLUMNS, Claim, ClaimsError, load_claims

CATALOG = load_catalog()
PROC = next(iter(CATALOG.procedures))
PROC2 = list(CATALOG.procedures)[1]
BUNDLE = next(iter(CATALOG.bundles))
DX = next(iter(CATALOG.diagnoses))


def row(claim_id="CLM-00001", **overrides):
    base = {
        "claim_id": claim_id, "member_id": "MEM-0001", "provider_id": "PRV-001",
        "provider_name": "Test Clinic", "claim_date": "2024-03-15", "claim_type": "OUTPATIENT",
        "diagnosis_code": DX, "procedure_codes": PROC, "submitted_amount": "48500", "is_weekend": "0",
    }
    return {**base, **overrides}


def write(tmp_path, rows, header=CLAIMS_COLUMNS):
    path = tmp_path / "claims.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for r in rows:
            writer.writerow(r.values() if isinstance(r, dict) else r)
    return path


def test_valid_file_loads_typed_claims(tmp_path):
    path = write(tmp_path, [
        row("CLM-00001", procedure_codes=f"{PROC}|{PROC2}", claim_date="2024-03-16", is_weekend="1"),
        row("CLM-00002", procedure_codes=BUNDLE),
    ])
    claims = load_claims(path, CATALOG)
    assert len(claims) == 2
    first = claims[0]
    assert isinstance(first, Claim)
    assert first.claim_date == date(2024, 3, 16)
    assert first.procedure_codes == (PROC, PROC2)
    assert first.submitted_amount == 48500 and first.is_weekend is True
    assert claims[1].is_weekend is False and claims[1].procedure_codes == (BUNDLE,)


def test_s4_every_problem_is_listed_in_one_error(tmp_path):
    path = write(tmp_path, [
        row("CLM-00001"),
        row("CLM-00001"),                                  # line 3: duplicate id
        row("CLM-00003", procedure_codes="P-9999"),        # line 4
        row("CLM-00004", diagnosis_code="Z99.9"),          # line 5
        row("CLM-00005", submitted_amount="48500.5"),      # line 6
        row("CLM-00006", is_weekend="2"),                  # line 7
        row("CLM-00007", claim_date="2024-02-30"),         # line 8
        row("CLM-00008", submitted_amount="0"),            # line 9
        row("CLM-00009", claim_date="20240315"),           # line 10
    ])
    with pytest.raises(ClaimsError) as exc:
        load_claims(path, CATALOG)
    message = str(exc.value)
    assert "8 problem(s)" in message
    for fragment in [
        "line 3: claim_id 'CLM-00001' already used on line 2",
        "line 4: unknown procedure code(s) ['P-9999']",
        "line 5: unknown diagnosis_code 'Z99.9'",
        "line 6: submitted_amount must be a positive integer, got '48500.5'",
        "line 7: is_weekend must be 0 or 1, got '2'",
        "line 8: claim_date must be a valid YYYY-MM-DD date, got '2024-02-30'",
        "line 9: submitted_amount must be a positive integer, got '0'",
        "line 10: claim_date must be a valid YYYY-MM-DD date, got '20240315'",
    ]:
        assert fragment in message


def test_s4_one_row_with_several_problems_lists_all(tmp_path):
    path = write(tmp_path, [row(diagnosis_code="Z99.9", procedure_codes=f"{PROC}|P-9999", is_weekend="x")])
    with pytest.raises(ClaimsError) as exc:
        load_claims(path, CATALOG)
    message = str(exc.value)
    assert "3 problem(s)" in message
    assert "line 2: unknown diagnosis_code 'Z99.9'" in message
    assert "line 2: unknown procedure code(s) ['P-9999']" in message
    assert "line 2: is_weekend must be 0 or 1, got 'x'" in message


def test_s4_wrong_header_is_reported(tmp_path):
    swapped = [CLAIMS_COLUMNS[1], CLAIMS_COLUMNS[0], *CLAIMS_COLUMNS[2:]]
    for header in (swapped, CLAIMS_COLUMNS[:-1]):
        with pytest.raises(ClaimsError) as exc:
            load_claims(write(tmp_path, [row()], header=header), CATALOG)
        assert "line 1: header must be" in str(exc.value)
        assert "1 problem(s)" in str(exc.value)


def test_s4_wrong_field_count_and_empty_codes(tmp_path):
    path = write(tmp_path, [list(row().values())[:-1], row("CLM-00002", procedure_codes="")])
    with pytest.raises(ClaimsError) as exc:
        load_claims(path, CATALOG)
    message = str(exc.value)
    assert "2 problem(s)" in message
    assert "line 2: expected 10 fields, got 9" in message
    assert "line 3: unknown procedure code(s) ['']" in message


def test_missing_and_empty_file(tmp_path):
    with pytest.raises(ClaimsError):
        load_claims(tmp_path / "missing.csv", CATALOG)
    empty = tmp_path / "empty.csv"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(ClaimsError) as exc:
        load_claims(empty, CATALOG)
    assert "line 1: header must be" in str(exc.value)


def test_header_only_file_is_rejected(tmp_path):
    with pytest.raises(ClaimsError, match="no claims after header"):
        load_claims(write(tmp_path, []), CATALOG)
    blank_lines = tmp_path / "blank.csv"
    blank_lines.write_text(",".join(CLAIMS_COLUMNS) + "\n\n\n", encoding="utf-8")
    with pytest.raises(ClaimsError, match="no claims after header"):
        load_claims(blank_lines, CATALOG)


def test_oversized_field_is_reported_as_invalid_csv(tmp_path):
    path = tmp_path / "claims.csv"
    path.write_text(",".join(CLAIMS_COLUMNS) + "\n" + "x" * 200_000 + "\n", encoding="utf-8")
    with pytest.raises(ClaimsError, match="not valid CSV"):
        load_claims(path, CATALOG)


def test_is_weekend_must_match_the_date(tmp_path):
    path = write(tmp_path, [
        row("CLM-00001", claim_date="2024-03-15", is_weekend="1"),  # Friday
        row("CLM-00002", claim_date="2024-03-16", is_weekend="0"),  # Saturday
        row("CLM-00003", claim_date="2024-03-17", is_weekend="1"),  # Sunday, consistent
    ])
    with pytest.raises(ClaimsError) as exc:
        load_claims(path, CATALOG)
    message = str(exc.value)
    assert "2 problem(s)" in message
    assert "line 2: is_weekend=1 but 2024-03-15 is a Friday" in message
    assert "line 3: is_weekend=0 but 2024-03-16 is a Saturday" in message


def test_empty_ids_and_unknown_claim_type_are_reported(tmp_path):
    path = write(tmp_path, [
        row("", member_id="", provider_id="", claim_type="OUTPATIENT "),
    ])
    with pytest.raises(ClaimsError) as exc:
        load_claims(path, CATALOG)
    message = str(exc.value)
    assert "4 problem(s)" in message
    for fragment in ["claim_id must not be empty", "member_id must not be empty",
                     "provider_id must not be empty", "claim_type must be one of"]:
        assert fragment in message
