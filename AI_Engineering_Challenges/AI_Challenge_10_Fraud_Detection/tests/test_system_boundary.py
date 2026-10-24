"""System test S9: the engine never touches ground truth or the generator."""

import re
from pathlib import Path

SRC = Path(__file__).parent.parent / "src"
ENGINE_FILES = [SRC / "claims.py", *sorted((SRC / "rules").glob("*.py")), *sorted((SRC / "scoring").glob("*.py"))]
GENERATOR_REFERENCE = re.compile(
    r"^\s*(from|import)\s+[\w.]*\bgenerator\b|import_module\([^)]*generator", re.MULTILINE
)  # any import line, incl. "from src.generator"
FORBIDDEN = ("ground_truth", "generation_summary")


def test_s9_engine_file_list_is_complete():
    assert (SRC / "claims.py").is_file()
    assert len(list((SRC / "rules").glob("*.py"))) == 10  # __init__, evidence, 8 rules
    assert list((SRC / "scoring").glob("*.py"))


def test_s9_engine_source_never_mentions_ground_truth_files():
    offenders = [(p.name, w) for p in ENGINE_FILES for w in FORBIDDEN if w in p.read_text(encoding="utf-8")]
    assert offenders == []


def test_s9_engine_source_never_imports_generator():
    offenders = [p.name for p in ENGINE_FILES if GENERATOR_REFERENCE.search(p.read_text(encoding="utf-8"))]
    assert offenders == []
