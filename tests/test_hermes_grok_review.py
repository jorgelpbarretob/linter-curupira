from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

RUNNER_PATH = Path(__file__).parents[1] / "tools" / "hermes" / "run_pont_001_grok_review.py"


def load_runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location("hermes_grok_review", RUNNER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def review(case_id: str, truth: str = "violation") -> dict[str, object]:
    return {
        "case_id": case_id,
        "domain": "infrastructure",
        "truth": truth,
        "structural_region": "visible_prose",
        "expected_diagnostics": 1,
        "rationale": "O sinal pertence à prosa técnica visível.",
        "confidence": "high",
        "requires_human": False,
        "critical_reason": "none",
    }


def test_structured_output_requires_exact_order_and_consistent_decisions() -> None:
    runner = load_runner()
    rows = [
        {"case_id": "one", "record_type": "literal_semicolon"},
        {"case_id": "two", "record_type": "literal_semicolon"},
    ]
    structured = {"reviews": [review("one"), review("two")]}

    assert runner.validate_structured_output(structured, rows) == structured["reviews"]

    structured["reviews"].reverse()
    with pytest.raises(runner.ReviewRunError, match="order/bijection"):
        runner.validate_structured_output(structured, rows)


def test_ambiguous_or_lower_confidence_must_escalate() -> None:
    runner = load_runner()
    ambiguous = review("one", truth="ambiguous")
    ambiguous.update(
        {
            "structural_region": "ambiguous",
            "expected_diagnostics": None,
            "confidence": "low",
        }
    )

    with pytest.raises(runner.ReviewRunError, match="not escalated"):
        runner.validate_review(ambiguous, "literal_semicolon")

    ambiguous.update({"requires_human": True, "critical_reason": "insufficient_context"})
    runner.validate_review(ambiguous, "literal_semicolon")


def test_control_contract_is_closed() -> None:
    runner = load_runner()
    control = review("control", truth="non_violation")
    control.update(
        {
            "structural_region": "document_control",
            "expected_diagnostics": 0,
        }
    )
    runner.validate_review(control, "zero_semicolon_control")

    control["truth"] = "violation"
    with pytest.raises(runner.ReviewRunError, match="inconsistent with control"):
        runner.validate_review(control, "zero_semicolon_control")


def test_truth_and_structural_region_must_agree() -> None:
    runner = load_runner()
    inconsistent = review("one")
    inconsistent["structural_region"] = "inline_code"

    with pytest.raises(runner.ReviewRunError, match="structural_region mismatch"):
        runner.validate_review(inconsistent, "literal_semicolon")


def test_runner_does_not_import_product_code() -> None:
    tree = ast.parse(RUNNER_PATH.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)

    assert not any(name == "ste_lint" or name.startswith("ste_lint.") for name in imported)
