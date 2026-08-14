from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

LABELER_PATH = Path(__file__).parents[1] / "tools" / "product_evidence" / "round2_label_sent002.py"


def load_labeler() -> ModuleType:
    spec = importlib.util.spec_from_file_location("round2_label_sent002", LABELER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sentence_record(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "case_id": "reviewed-control",
        "rule_id": "STE-I9-SENT-002",
        "source_id": "otel",
        "path": "fixture.md",
        "structural_context": "visible_prose",
        "sentence_status": "complete",
        "raw_alpha_token_count": 10,
        "start_offset": 0,
        "end_offset": 1,
        "slice_sha256": hashlib.sha256(b"A").hexdigest(),
    }
    record.update(overrides)
    return record


def test_reviewed_sentence_labels_do_not_infer_truth_from_raw_count() -> None:
    labeler = load_labeler()
    violation_id = next(iter(labeler.VIOLATION_CASE_IDS))
    ambiguous_id = next(iter(labeler.AMBIGUOUS_CASE_IDS))

    assert labeler.propose_label(sentence_record(case_id=violation_id)) == "violation"
    assert labeler.propose_label(sentence_record(case_id=ambiguous_id)) == "ambiguous"
    assert labeler.propose_label(sentence_record(raw_alpha_token_count=43)) == "non_violation"


def test_non_sentence_and_non_descriptive_cases_abstain() -> None:
    labeler = load_labeler()
    manual_id = next(iter(labeler.MANUAL_OUT_OF_SCOPE_CASE_IDS))

    assert labeler.propose_label(sentence_record(sentence_status="incomplete")) == "out_of_scope"
    assert (
        labeler.propose_label(
            sentence_record(path="content/en/docs/concepts/instrumentation/code-based.md")
        )
        == "out_of_scope"
    )
    assert labeler.propose_label(sentence_record(case_id=manual_id)) == "out_of_scope"
    assert labeler.propose_label(sentence_record(structural_context="uncertain")) == "ambiguous"


def test_invalid_source_span_aborts() -> None:
    labeler = load_labeler()

    with pytest.raises(labeler.LabelError, match="sentence span"):
        labeler.propose_labels(
            [sentence_record(end_offset=99)],
            {("otel", "fixture.md"): "A"},
            expected_total=1,
        )
