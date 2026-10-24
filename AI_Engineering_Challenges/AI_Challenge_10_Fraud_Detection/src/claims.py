"""Load and validate claims.csv, the input of the rule engine.

Format: docs/decisions/dataset-format.md. Validation policy: docs/decisions/ADR-002 (any problem
stops the engine; the message lists every problem found, with line numbers).
The generator imports CLAIMS_COLUMNS from here; this module must never import from generator/.
"""

import csv
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from catalog import CLAIM_TYPES, Catalog

CLAIMS_COLUMNS = [
    "claim_id", "member_id", "provider_id", "provider_name", "claim_date", "claim_type",
    "diagnosis_code", "procedure_codes", "submitted_amount", "is_weekend",
]
DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")  # date.fromisoformat alone also accepts "20240315"


class ClaimsError(ValueError):
    """Raised when claims.csv is invalid. The message lists every problem found."""


@dataclass(frozen=True)
class Claim:
    claim_id: str
    member_id: str
    provider_id: str
    provider_name: str
    claim_date: date
    claim_type: str
    diagnosis_code: str
    procedure_codes: tuple[str, ...]
    submitted_amount: int
    is_weekend: bool


def load_claims(path: Path, catalog: Catalog) -> list[Claim]:
    try:
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(_numbered_rows(csv.reader(f)))
    except (OSError, UnicodeDecodeError) as exc:
        raise ClaimsError(f"{path}: cannot read file: {exc}") from exc
    except csv.Error as exc:
        raise ClaimsError(f"{path}: not valid CSV: {exc}") from exc

    if not rows or rows[0][1] != CLAIMS_COLUMNS:
        found = rows[0][1] if rows else "an empty file"
        raise ClaimsError(f"{path}: 1 problem(s)\n- line 1: header must be {CLAIMS_COLUMNS}, got {found}")

    claims, problems, seen_ids = [], [], {}
    for line, row in rows[1:]:
        if not row:  # blank line
            continue
        if len(row) != len(CLAIMS_COLUMNS):
            problems.append(f"line {line}: expected {len(CLAIMS_COLUMNS)} fields, got {len(row)}")
            continue
        claim, row_problems = _parse_row(row, catalog)
        first_line = seen_ids.setdefault(row[0], line)
        if first_line != line:
            row_problems.append(f"claim_id {row[0]!r} already used on line {first_line}")
        problems.extend(f"line {line}: {p}" for p in row_problems)
        if claim is not None and not row_problems:
            claims.append(claim)

    if not problems and not claims:  # header only, or header followed by blank lines
        problems.append("no claims after header")
    if problems:
        raise ClaimsError(f"{path}: {len(problems)} problem(s)\n- " + "\n- ".join(problems))
    return claims


def _numbered_rows(reader):
    """Yield (line number of the row's last line, fields)."""
    for row in reader:
        yield reader.line_num, row


def _parse_row(row: list[str], catalog: Catalog) -> tuple[Claim | None, list[str]]:
    values = dict(zip(CLAIMS_COLUMNS, row))
    problems = []

    claim_date = None
    raw_date = values["claim_date"]
    if DATE_PATTERN.fullmatch(raw_date):
        try:
            claim_date = date.fromisoformat(raw_date)
        except ValueError:
            pass
    if claim_date is None:
        problems.append(f"claim_date must be a valid YYYY-MM-DD date, got {raw_date!r}")

    raw_amount = values["submitted_amount"]
    amount = int(raw_amount) if raw_amount.isascii() and raw_amount.isdigit() else 0
    if amount <= 0:
        problems.append(f"submitted_amount must be a positive integer, got {raw_amount!r}")

    raw_weekend = values["is_weekend"]
    if raw_weekend not in ("0", "1"):
        problems.append(f"is_weekend must be 0 or 1, got {raw_weekend!r}")
    elif claim_date is not None and (claim_date.weekday() >= 5) != (raw_weekend == "1"):
        problems.append(f"is_weekend={raw_weekend} but {raw_date} is a {claim_date.strftime('%A')}")

    for column in ("claim_id", "member_id", "provider_id"):
        if not values[column]:
            problems.append(f"{column} must not be empty")
    if values["claim_type"] not in CLAIM_TYPES:
        problems.append(f"claim_type must be one of {list(CLAIM_TYPES)}, got {values['claim_type']!r}")

    diagnosis = values["diagnosis_code"]
    if diagnosis not in catalog.diagnoses:
        problems.append(f"unknown diagnosis_code {diagnosis!r}")

    codes = tuple(values["procedure_codes"].split("|"))
    unknown = [c for c in codes if c not in catalog.procedures and c not in catalog.bundles]
    if unknown:
        problems.append(f"unknown procedure code(s) {unknown}")

    if problems:
        return None, problems
    assert claim_date is not None  # no problems => the date parsed
    claim = Claim(
        claim_id=values["claim_id"],
        member_id=values["member_id"],
        provider_id=values["provider_id"],
        provider_name=values["provider_name"],
        claim_date=claim_date,
        claim_type=values["claim_type"],
        diagnosis_code=diagnosis,
        procedure_codes=codes,
        submitted_amount=amount,
        is_weekend=raw_weekend == "1",
    )
    return claim, problems
