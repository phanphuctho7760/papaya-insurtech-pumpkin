"""System test S8: evidence helpers."""

import pytest

from catalog import load_catalog
from rules.evidence import code_label, vnd


@pytest.fixture(scope="module")
def catalog():
    return load_catalog()


def test_s8_vnd_uses_thousands_separator_and_unit():
    assert vnd(48500) == "48,500 VND"
    assert vnd(19_000_000) == "19,000,000 VND"


def test_s8_code_label_covers_procedure_bundle_and_diagnosis(catalog):
    assert code_label("P-3001", catalog) == "P-3001 (Laparoscopic appendectomy)"
    assert code_label("B-3101", catalog) == "B-3101 (Appendectomy package)"
    assert code_label("K02.1", catalog) == "K02.1 (Dental caries)"


def test_s8_code_label_rejects_unknown_code(catalog):
    with pytest.raises(KeyError):
        code_label("X-0000", catalog)
