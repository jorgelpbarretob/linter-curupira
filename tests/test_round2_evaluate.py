from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

EVALUATOR_PATH = Path(__file__).parents[1] / "tools" / "product_evidence" / "round2_evaluate.py"


def load_evaluator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("round2_evaluate", EVALUATOR_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_exact_diagnostics_produce_a_unit_confusion_matrix() -> None:
    evaluator = load_evaluator()
    inventory = [
        {
            "case_id": "positive",
            "rule_id": "STE-I9-SENT-001",
            "source_id": "dapr",
            "path": "manual.md",
            "start_offset": 0,
            "end_offset": 20,
        },
        {
            "case_id": "negative",
            "rule_id": "STE-I9-SENT-001",
            "source_id": "dapr",
            "path": "manual.md",
            "start_offset": 21,
            "end_offset": 30,
        },
    ]
    labels = {"positive": "violation", "negative": "non_violation"}
    diagnostics = [
        {
            "source_id": "dapr",
            "path": "manual.md",
            "start_offset": 0,
            "end_offset": 20,
        }
    ]

    result = evaluator.evaluate_rule("STE-I9-SENT-001", inventory, labels, diagnostics)

    assert result["strict"] == {"tp": 1, "fp": 0, "fn": 0, "tn": 1}


def test_boundary_emissions_and_ambiguity_are_reported_conservatively() -> None:
    evaluator = load_evaluator()
    inventory = [
        {
            "case_id": "ambiguous",
            "rule_id": "STE-I9-SENT-001",
            "source_id": "otel",
            "path": "manual.md",
            "start_offset": 0,
            "end_offset": 10,
        },
        {
            "case_id": "excluded",
            "rule_id": "STE-I9-SENT-001",
            "source_id": "otel",
            "path": "manual.md",
            "start_offset": 11,
            "end_offset": 20,
        },
    ]
    labels = {"ambiguous": "ambiguous", "excluded": "out_of_scope"}
    diagnostics = [
        {
            "source_id": "otel",
            "path": "manual.md",
            "start_offset": 11,
            "end_offset": 20,
        },
        {
            "source_id": "otel",
            "path": "manual.md",
            "start_offset": 30,
            "end_offset": 40,
        },
    ]

    result = evaluator.evaluate_rule("STE-I9-SENT-001", inventory, labels, diagnostics)

    assert result["strict"] == {"tp": 0, "fp": 2, "fn": 0, "tn": 0}
    assert result["conservative"] == {"tp": 0, "fp": 2, "fn": 1, "tn": 0}
    assert result["boundary_false_positives"] == ["excluded"]
    assert result["unmatched_diagnostics"] == 1


def test_list_diagnostic_matches_the_reviewed_lead_in() -> None:
    evaluator = load_evaluator()
    inventory = [
        {
            "case_id": "list-run",
            "rule_id": "STE-I9-LIST-001",
            "source_id": "dapr",
            "path": "manual.md",
            "start_offset": 50,
            "end_offset": 100,
            "lead_in_start_offset": 20,
            "lead_in_end_offset": 40,
        }
    ]
    diagnostics = [
        {
            "source_id": "dapr",
            "path": "manual.md",
            "start_offset": 39,
            "end_offset": 40,
        }
    ]

    result = evaluator.evaluate_rule(
        "STE-I9-LIST-001", inventory, {"list-run": "violation"}, diagnostics
    )

    assert result["strict"] == {"tp": 1, "fp": 0, "fn": 0, "tn": 0}
    assert result["unmatched_diagnostics"] == 0


def test_wilson_interval_reports_the_preregistered_zero_fp_threshold() -> None:
    evaluator = load_evaluator()

    lower, upper = evaluator.wilson_interval(73, 73)

    assert lower == pytest.approx(0.9500, abs=0.0001)
    assert upper == pytest.approx(1.0)


def test_error_case_ids_are_preserved_for_adjudication() -> None:
    evaluator = load_evaluator()
    inventory = [
        {
            "case_id": "missed-positive",
            "rule_id": "STE-I9-PARA-001",
            "source_id": "otel",
            "path": "manual.md",
            "start_offset": 0,
            "end_offset": 10,
        },
        {
            "case_id": "emitted-negative",
            "rule_id": "STE-I9-PARA-001",
            "source_id": "otel",
            "path": "manual.md",
            "start_offset": 11,
            "end_offset": 20,
        },
    ]
    labels = {
        "missed-positive": "violation",
        "emitted-negative": "non_violation",
    }
    diagnostics = [
        {
            "source_id": "otel",
            "path": "manual.md",
            "start_offset": 11,
            "end_offset": 20,
        }
    ]

    result = evaluator.evaluate_rule("STE-I9-PARA-001", inventory, labels, diagnostics)

    assert result["false_negative_case_ids"] == ["missed-positive"]
    assert result["false_positive_case_ids"] == ["emitted-negative"]


def test_frozen_input_hash_mismatch_aborts_before_evaluation(tmp_path: Path) -> None:
    evaluator = load_evaluator()
    frozen = tmp_path / "labels.jsonl"
    frozen.write_text("changed\n", encoding="utf-8")

    with pytest.raises(evaluator.EvaluationError, match="digest mismatch"):
        evaluator.read_frozen(frozen, "0" * 64)
