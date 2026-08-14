from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

LABELER_PATH = Path(__file__).parents[1] / "tools" / "product_evidence" / "round2_label_list.py"


def load_labeler() -> ModuleType:
    spec = importlib.util.spec_from_file_location("round2_label_list", LABELER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def list_record(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "case_id": "case",
        "rule_id": "STE-I9-LIST-001",
        "source_id": "dapr",
        "path": "fixture.md",
        "lead_in_status": "found",
        "lead_in_start_offset": 0,
        "lead_in_end_offset": 16,
        "lead_in_slice_sha256": "unused",
        "start_offset": 0,
        "end_offset": 1,
        "slice_sha256": hashlib.sha256(b"S").hexdigest(),
        "blank_lines_before": 1,
        "indentation": 0,
        "peer_count": 2,
        "blockers": [],
    }
    record.update(overrides)
    return record


def test_narrow_public_subclass_labels_period_colon_and_other() -> None:
    labeler = load_labeler()

    assert labeler.propose_label(list_record(), "Use these tools.") == "violation"
    assert labeler.propose_label(list_record(), "Use these tools:") == "non_violation"
    assert labeler.propose_label(list_record(), "Use the following tools:") == "out_of_scope"
    assert labeler.propose_label(list_record(), "Use these equipment:") == "out_of_scope"


def test_uncertain_or_structurally_blocked_cases_do_not_expand_scope() -> None:
    labeler = load_labeler()

    assert (
        labeler.propose_label(list_record(lead_in_status="uncertain"), "Use these tools.")
        == "ambiguous"
    )
    assert (
        labeler.propose_label(list_record(blockers=["heading"]), "Use these tools.")
        == "out_of_scope"
    )
    assert (
        labeler.propose_label(list_record(blank_lines_before=2), "Use these tools.")
        == "out_of_scope"
    )
    assert labeler.propose_label(list_record(indentation=4), "Use these tools.") == "out_of_scope"


def test_missing_clone_or_inventory_span_aborts() -> None:
    labeler = load_labeler()

    with pytest.raises(labeler.LabelError, match="lead-in span"):
        labeler.propose_labels(
            [list_record(lead_in_end_offset=999)],
            {("dapr", "fixture.md"): "Short."},
            expected_total=1,
        )
