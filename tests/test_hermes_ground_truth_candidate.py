from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

MATERIALIZER_PATH = (
    Path(__file__).parents[1]
    / "tools"
    / "hermes"
    / "materialize_pont_001_ground_truth_candidate.py"
)


def load_materializer() -> ModuleType:
    sys.path.insert(0, str(MATERIALIZER_PATH.parent))
    spec = importlib.util.spec_from_file_location("hermes_ground_truth", MATERIALIZER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_canonical_ground_truth_rejects_source_text() -> None:
    materializer = load_materializer()

    with pytest.raises(materializer.GroundTruthError, match="forbidden"):
        materializer.canonical_ground_truth_bytes([{"case_id": "one", "text": "leak"}])


def test_candidate_cannot_be_written_inside_repository() -> None:
    materializer = load_materializer()

    with pytest.raises(materializer.GroundTruthError, match="outside the repository"):
        materializer.write_candidate(materializer.PROJECT_ROOT / "ground-truth", [])


def test_unadjudicated_critical_case_cannot_materialize() -> None:
    materializer = load_materializer()
    units = [{"record_type": "manifest"}]
    proposals: list[dict[str, object]] = []
    for index in range(409):
        case_id = f"case-{index:03d}"
        units.append(
            {
                "case_id": case_id,
                "record_type": "literal_semicolon",
                "source_path": "content/pt-br/docs/example.md",
                "source_file_sha256": "a" * 64,
                "occurrence_index_in_document": index + 1,
                "unicode_offset": index,
                "utf8_byte_offset": index,
                "line": 1,
                "column": index + 1,
            }
        )
        proposals.append(
            {
                "case_id": case_id,
                "domain": "software",
                "truth": "violation",
                "structural_region": "visible_prose",
                "expected_diagnostics": 1,
                "rationale": "O sinal pertence à prosa técnica visível.",
                "confidence": "high",
                "requires_human": False,
                "critical_reason": "none",
            }
        )
    proposals[0].update(
        {
            "truth": "ambiguous",
            "structural_region": "ambiguous",
            "expected_diagnostics": None,
            "confidence": "low",
            "requires_human": True,
            "critical_reason": "insufficient_context",
        }
    )

    with pytest.raises(materializer.GroundTruthError, match="not adjudicated"):
        materializer.build_ground_truth_records(units, proposals)


def test_materializer_does_not_import_product_code() -> None:
    tree = ast.parse(MATERIALIZER_PATH.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)

    assert not any(name == "ste_lint" or name.startswith("ste_lint.") for name in imported)
