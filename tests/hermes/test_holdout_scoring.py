from __future__ import annotations

from pathlib import Path

import pytest

from tools.hermes.score_pont_001_frozen_holdout import (
    HoldoutScoringError,
    read_json,
    score,
    wilson_interval,
)


def execution() -> dict[str, object]:
    return {
        "schema_version": "hermes-holdout-execution/v1",
        "rule_id": "HERMES-PT-PONT-001",
        "detector_sha256": "detector",
        "holdout_manifest_sha256": "manifest",
        "diagnostic_count": 2,
        "unmatched_diagnostic_count": 0,
        "lintable_word_count": 1000,
        "case_results": [
            {
                "case_id": "tp",
                "record_type": "literal_semicolon",
                "source_path": "a.md",
                "start_offset": 1,
                "emitted_exact": True,
            },
            {
                "case_id": "fn",
                "record_type": "literal_semicolon",
                "source_path": "a.md",
                "start_offset": 3,
                "emitted_exact": False,
            },
            {
                "case_id": "fp",
                "record_type": "literal_semicolon",
                "source_path": "a.md",
                "start_offset": 5,
                "emitted_exact": True,
            },
            {
                "case_id": "tn",
                "record_type": "zero_semicolon_control",
                "source_path": "b.md",
                "diagnostic_count": 0,
            },
        ],
        "diagnostics": [],
    }


def label(
    case_id: str,
    truth: str,
    expected: int,
    *,
    path: str = "a.md",
    offset: int = 1,
) -> dict[str, object]:
    return {
        "case_id": case_id,
        "rule_id": "HERMES-PT-PONT-001",
        "source_path": path,
        "unicode_offset": offset,
        "truth": truth,
        "expected_diagnostics": expected,
        "domain": "operations",
    }


def test_score_reconciles_exact_unit_confusion_matrix() -> None:
    labels = [
        label("tp", "violation", 1),
        label("fn", "violation", 1, offset=3),
        label("fp", "out_of_scope", 0, offset=5),
        label("tn", "non_violation", 0, path="b.md", offset=0),
    ]

    metrics = score(execution(), labels)

    assert metrics["confusion_matrix"] == {"tp": 1, "fp": 1, "fn": 1, "tn": 1}
    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 0.5
    assert metrics["fp_per_1000_lintable_words"] == 1.0
    assert metrics["false_negative_case_ids"] == ["fn"]
    assert metrics["false_positive_case_ids"] == ["fp"]
    assert metrics["region_error_case_ids"] == ["fp"]
    assert "rationale" not in str(metrics)
    assert "text" not in str(metrics)


def test_wilson_interval_matches_preregistered_zero_error_gate() -> None:
    interval = wilson_interval(73, 73)

    assert interval is not None
    assert interval[0] == pytest.approx(0.9500, abs=0.0001)
    assert interval[1] == pytest.approx(1.0)


def test_hash_mismatch_aborts_before_scoring(tmp_path: Path) -> None:
    path = tmp_path / "execution.json"
    path.write_text("{}\n", encoding="utf-8")

    with pytest.raises(HoldoutScoringError, match="hash divergente"):
        read_json(path, "0" * 64)


def test_score_rejects_case_id_mismatch() -> None:
    labels = [label("missing", "violation", 1)]

    with pytest.raises(HoldoutScoringError, match="bijeção"):
        score(execution(), labels)
