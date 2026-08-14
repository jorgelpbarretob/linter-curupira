from __future__ import annotations

import ast
import importlib.util
import sys
from copy import deepcopy
from pathlib import Path
from types import ModuleType

import pytest

VALIDATOR_PATH = (
    Path(__file__).parents[1] / "tools" / "hermes" / "validate_pont_001_human_review.py"
)


def load_validator() -> ModuleType:
    sys.path.insert(0, str(VALIDATOR_PATH.parent))
    spec = importlib.util.spec_from_file_location("hermes_human_review_validation", VALIDATOR_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def review_row(record_type: str = "literal_semicolon") -> dict[str, str]:
    validator = load_validator()
    row = {field: "" for field in validator.preparer.CSV_FIELDS}
    row.update(
        {
            "case_id": "pont-holdout-occ-0001",
            "record_type": record_type,
            "domain": "infrastructure",
            "truth": "violation",
            "structural_region": "visible_prose",
            "expected_diagnostics": "1",
            "rationale": "O sinal pertence à prosa técnica visível.",
            "review_status": "approved",
            "reviewed_by": "project-maintainer",
            "reviewer_role": "maintainer-and-language-reviewer",
            "reviewed_on": "2026-08-14",
        }
    )
    return row


def test_valid_completed_decisions_return_truth_counts() -> None:
    validator = load_validator()
    occurrence = review_row()
    control = review_row("zero_semicolon_control")
    control.update(
        {
            "case_id": "pont-holdout-ctl-001",
            "truth": "non_violation",
            "structural_region": "document_control",
            "expected_diagnostics": "0",
            "rationale": "O documento de controle não contém o sinal.",
        }
    )

    summary = validator.validate_decisions([occurrence, control])

    assert summary == {
        "case_count": 2,
        "approved": 2,
        "rejected": 0,
        "violation": 1,
        "non_violation": 1,
        "out_of_scope": 0,
        "ambiguous": 0,
    }


def test_pending_or_inconsistent_decision_fails_closed() -> None:
    validator = load_validator()
    pending = review_row()
    pending["review_status"] = "pending-human-review"
    inconsistent = review_row()
    inconsistent["truth"] = "ambiguous"

    with pytest.raises(validator.ReviewError, match="not human-reviewed"):
        validator.validate_decisions([pending])
    with pytest.raises(validator.ReviewError, match="expected_diagnostics"):
        validator.validate_decisions([inconsistent])


def test_rejected_case_requires_decision_notes() -> None:
    validator = load_validator()
    rejected = review_row()
    rejected["review_status"] = "rejected"

    with pytest.raises(validator.ReviewError, match="decision_notes"):
        validator.validate_decisions([rejected])

    rejected["decision_notes"] = "Fonte inadequada para esta unidade."
    summary = validator.validate_decisions([rejected])
    assert summary["rejected"] == 1


def test_immutable_packet_fields_cannot_change() -> None:
    validator = load_validator()
    expected = review_row()
    actual = deepcopy(expected)
    actual["source_path"] = "content/pt-br/docs/changed.md"

    with pytest.raises(validator.ReviewError, match="immutable fields changed"):
        validator.validate_immutable_fields([actual], [expected])


def test_validator_does_not_import_product_code() -> None:
    tree = ast.parse(VALIDATOR_PATH.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)

    assert not any(name == "ste_lint" or name.startswith("ste_lint.") for name in imported)
