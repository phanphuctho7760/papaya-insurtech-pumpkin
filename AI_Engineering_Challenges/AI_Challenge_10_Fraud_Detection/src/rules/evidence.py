"""Shared formatting helpers for rule evidence strings. Templates: docs/business-rule/evidence.md."""

from catalog import Catalog


def vnd(amount: int | float) -> str:
    """48500 -> '48,500 VND'."""
    return f"{round(amount):,} VND"


def days(n: int) -> str:
    """1 -> '1 day', 3 -> '3 days'."""
    return f"{n} day" if n == 1 else f"{n} days"


def code_label(code: str, catalog: Catalog) -> str:
    """'P-3001' -> 'P-3001 (Laparoscopic appendectomy)'. Works for procedures, bundles and diagnoses."""
    item = catalog.procedures.get(code) or catalog.bundles.get(code) or catalog.diagnoses[code]
    return f"{code} ({item.name})"


def code_labels(codes, catalog: Catalog, separator: str = " + ") -> str:
    return separator.join(code_label(code, catalog) for code in codes)
