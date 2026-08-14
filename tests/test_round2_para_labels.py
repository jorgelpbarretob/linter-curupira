from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

LABELER_PATH = Path(__file__).parents[1] / "tools" / "product_evidence" / "round2_label_para.py"


def load_labeler() -> ModuleType:
    spec = importlib.util.spec_from_file_location("round2_label_para", LABELER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def paragraph_record(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "case_id": "case",
        "rule_id": "STE-I9-PARA-001",
        "source_id": "dapr",
        "path": "fixture.md",
        "structural_context": "visible_prose",
        "candidate_terminal_count": 1,
        "start_offset": 0,
        "end_offset": 1,
        "slice_sha256": hashlib.sha256(b"A").hexdigest(),
    }
    record.update(overrides)
    return record


def test_paragraph_threshold_and_zero_sentence_scope() -> None:
    labeler = load_labeler()

    assert labeler.propose_label(paragraph_record(candidate_terminal_count=7)) == "violation"
    assert labeler.propose_label(paragraph_record(candidate_terminal_count=6)) == "non_violation"
    assert labeler.propose_label(paragraph_record(candidate_terminal_count=1)) == "non_violation"
    assert labeler.propose_label(paragraph_record(candidate_terminal_count=0)) == "out_of_scope"


def test_uncertain_and_manually_procedural_paragraphs_abstain() -> None:
    labeler = load_labeler()
    manual_id = next(iter(labeler.MANUAL_OUT_OF_SCOPE_CASE_IDS))

    assert labeler.propose_label(paragraph_record(structural_context="uncertain")) == "ambiguous"
    assert labeler.propose_label(paragraph_record(case_id=manual_id)) == "out_of_scope"
    assert (
        labeler.propose_label(
            paragraph_record(path="content/en/docs/concepts/instrumentation/code-based.md")
        )
        == "out_of_scope"
    )


@pytest.mark.parametrize(
    "case_id",
    [
        "r2-dfe51d8e98d64be27fd8f8f771b42298ad13fd39f1f4f1a5a53e97cffcee8e22",
        "r2-398940768915abe09625062b6a6ec776de9222b94a917432db3546f628a65ed9",
        "r2-36ee340beea4bdbd53aad94ad05481489f1eeeb3430db6c62fe5f596c352ddb0",
    ],
)
def test_reviewed_descriptive_paragraphs_remain_in_scope(case_id: str) -> None:
    labeler = load_labeler()

    assert labeler.propose_label(paragraph_record(case_id=case_id)) == "non_violation"


def test_invalid_source_span_aborts() -> None:
    labeler = load_labeler()

    with pytest.raises(labeler.LabelError, match="paragraph span"):
        labeler.propose_labels(
            [paragraph_record(end_offset=99)],
            {("dapr", "fixture.md"): "A"},
            expected_total=1,
        )
