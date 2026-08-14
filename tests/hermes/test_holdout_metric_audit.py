from __future__ import annotations

import json

import pytest

from tools.hermes.audit_pont_001_metrics import AuditError, compare, recompute, wilson_lower
from tools.hermes.score_pont_001_frozen_holdout import score

from .test_holdout_scoring import execution, label


def labels() -> list[dict[str, object]]:
    return [
        label("tp", "violation", 1),
        label("fn", "violation", 1, offset=3),
        label("fp", "out_of_scope", 0, offset=5),
        label("tn", "non_violation", 0, path="b.md", offset=0),
    ]


def test_independent_audit_recomputes_and_confirms_submitted_metrics() -> None:
    independent = recompute(execution(), labels())
    submitted = json.loads(json.dumps(score(execution(), labels())))

    compare(independent, submitted)

    assert independent["matrix"] == {"tp": 1, "fp": 1, "fn": 1, "tn": 1}
    assert independent["span_accuracy"] == 0.5
    assert independent["region_error_case_ids"] == ["fp"]
    assert independent["additional_error_free_tp_for_wilson_gate"] > 0
    assert independent["gate_assessment"] == {
        "point_precision_gte_0_95": False,
        "wilson_lower_gte_0_95": False,
        "zero_known_false_positives": False,
        "at_least_73_positive_units": False,
        "overall_promotion_gate": False,
    }


def test_independent_audit_refutes_a_changed_metric() -> None:
    independent = recompute(execution(), labels())
    submitted = json.loads(json.dumps(score(execution(), labels())))
    submitted["precision"] = 0.75

    with pytest.raises(AuditError, match="divergência em precision"):
        compare(independent, submitted)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("span_accuracy", 0.75, "span_accuracy"),
        ("region_error_count", 0, "region_error_count"),
        ("precision_wilson_95", [0.1, 0.9], "Wilson de precisão"),
    ],
)
def test_independent_audit_refutes_other_changed_aggregates(
    field: str, value: object, message: str
) -> None:
    independent = recompute(execution(), labels())
    submitted = json.loads(json.dumps(score(execution(), labels())))
    submitted[field] = value

    with pytest.raises(AuditError, match=message):
        compare(independent, submitted)


def test_wilson_lower_reaches_preregistered_zero_error_boundary() -> None:
    assert wilson_lower(72, 72) < 0.95
    assert wilson_lower(73, 73) >= 0.95
