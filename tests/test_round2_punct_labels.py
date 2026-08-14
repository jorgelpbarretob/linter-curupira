from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

LABELER_PATH = Path(__file__).parents[1] / "tools" / "product_evidence" / "round2_label_punct.py"


def load_labeler() -> ModuleType:
    spec = importlib.util.spec_from_file_location("round2_label_punct", LABELER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_label_records_are_bijective_and_do_not_copy_source_metadata() -> None:
    labeler = load_labeler()
    records = [
        {
            "case_id": "case-code",
            "rule_id": "STE-I9-PUNCT-001",
            "structural_context": "markup_or_code",
        },
        {
            "case_id": next(iter(labeler.VIOLATION_CASE_IDS)),
            "rule_id": "STE-I9-PUNCT-001",
            "structural_context": "visible_prose",
        },
    ]

    labels = labeler.propose_labels(records, expected_total=2)

    assert [record["proposed_label"] for record in labels] == [
        "non_violation",
        "violation",
    ]
    assert all(set(record) == labeler.LABEL_FIELDS for record in labels)


def test_unreviewed_visible_or_uncertain_case_aborts() -> None:
    labeler = load_labeler()

    with pytest.raises(labeler.LabelError, match="not in reviewed violation allowlist"):
        labeler.propose_labels(
            [
                {
                    "case_id": "unreviewed",
                    "rule_id": "STE-I9-PUNCT-001",
                    "structural_context": "visible_prose",
                }
            ],
            expected_total=1,
        )

    with pytest.raises(labeler.LabelError, match="uncertain case requires adjudication"):
        labeler.propose_labels(
            [
                {
                    "case_id": "uncertain",
                    "rule_id": "STE-I9-PUNCT-001",
                    "structural_context": "uncertain",
                }
            ],
            expected_total=1,
        )
