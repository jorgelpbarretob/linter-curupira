from __future__ import annotations

import ast
import hashlib
from pathlib import Path

import pytest

from tools.hermes.run_pont_001_frozen_holdout import (
    HoldoutExecutionError,
    execute_records,
    materialize,
)


def source_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_execution_maps_only_exact_visible_semicolon_without_labels(tmp_path: Path) -> None:
    visible = tmp_path / "visible.md"
    visible_text = "Use `a;b`; depois calcule $c;d$."
    visible.write_text(visible_text, encoding="utf-8")
    control = tmp_path / "control.md"
    control.write_text("Execute o procedimento.", encoding="utf-8")
    visible_offset = visible_text.index(";", visible_text.index("`", 5) + 1)
    records = [
        {
            "record_type": "manifest",
            "rule_id": "HERMES-PT-PONT-001",
            "source_commit": "snapshot",
        },
        {
            "record_type": "literal_semicolon",
            "case_id": "occ-1",
            "rule_id": "HERMES-PT-PONT-001",
            "source_path": "visible.md",
            "source_file_sha256": source_hash(visible),
            "unicode_offset": visible_offset,
        },
        {
            "record_type": "zero_semicolon_control",
            "case_id": "ctl-1",
            "rule_id": "HERMES-PT-PONT-001",
            "source_path": "control.md",
            "source_file_sha256": source_hash(control),
        },
    ]

    result = execute_records(
        tmp_path,
        records,
        detector_sha256="detector",
        manifest_sha256="manifest",
    )

    assert result["case_count"] == 2
    assert result["diagnostic_count"] == 1
    assert result["unmatched_diagnostic_count"] == 0
    assert result["case_results"] == [
        {
            "case_id": "occ-1",
            "record_type": "literal_semicolon",
            "source_path": "visible.md",
            "start_offset": visible_offset,
            "end_offset": visible_offset + 1,
            "emitted_exact": True,
        },
        {
            "case_id": "ctl-1",
            "record_type": "zero_semicolon_control",
            "source_path": "control.md",
            "diagnostic_count": 0,
        },
    ]
    assert "text" not in str(result)
    assert "truth" not in str(result)


def test_execution_rejects_a_source_hash_mismatch(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text("Texto; visível.", encoding="utf-8")
    records = [
        {
            "record_type": "manifest",
            "rule_id": "HERMES-PT-PONT-001",
            "source_commit": "snapshot",
        },
        {
            "record_type": "literal_semicolon",
            "case_id": "occ-1",
            "rule_id": "HERMES-PT-PONT-001",
            "source_path": "source.md",
            "source_file_sha256": "0" * 64,
            "unicode_offset": 5,
        },
    ]

    with pytest.raises(HoldoutExecutionError, match="hash da fonte diverge"):
        execute_records(
            tmp_path,
            records,
            detector_sha256="detector",
            manifest_sha256="manifest",
        )


def test_materialization_is_atomic_and_refuses_overwrite(tmp_path: Path) -> None:
    output = tmp_path / "execution-v1"
    result_path, digest = materialize(output, {"schema_version": "test"})

    assert hashlib.sha256(result_path.read_bytes()).hexdigest() == digest
    with pytest.raises(HoldoutExecutionError, match="já existe"):
        materialize(output, {"schema_version": "changed"})


def test_runner_has_no_label_or_custody_dependency() -> None:
    runner = Path("tools/hermes/run_pont_001_frozen_holdout.py")
    source = runner.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = [
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    ]

    assert "ground_truth" not in source
    assert "holdout-custody" not in source
    assert not any(module.startswith("tools.hermes.materialize") for module in imports)
