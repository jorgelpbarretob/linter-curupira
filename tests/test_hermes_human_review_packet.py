from __future__ import annotations

import ast
import csv
import hashlib
import importlib.util
import io
from pathlib import Path
from types import ModuleType

import pytest

PREPARER_PATH = Path(__file__).parents[1] / "tools" / "hermes" / "prepare_pont_001_human_review.py"


def load_preparer() -> ModuleType:
    spec = importlib.util.spec_from_file_location("hermes_human_review", PREPARER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_record(path: Path, source_root: Path, *, control: bool = False) -> dict[str, object]:
    payload = path.read_bytes()
    common: dict[str, object] = {
        "case_id": "pont-holdout-ctl-001" if control else "pont-holdout-occ-0001",
        "record_type": "zero_semicolon_control" if control else "literal_semicolon",
        "source_path": path.relative_to(source_root).as_posix(),
        "source_file_sha256": hashlib.sha256(payload).hexdigest(),
    }
    if control:
        common["selection_rank"] = 1
    else:
        text = payload.decode()
        offset = text.index(";")
        common.update(
            {
                "line": 2,
                "column": 5,
                "unicode_offset": offset,
                "utf8_byte_offset": len(text[:offset].encode()),
                "occurrence_index_in_document": 1,
            }
        )
    return common


def test_review_rows_preserve_context_but_leave_human_decisions_blank(tmp_path: Path) -> None:
    preparer = load_preparer()
    candidate = tmp_path / "content/pt-br/docs/candidate.md"
    control = tmp_path / "content/pt-br/docs/control.md"
    candidate.parent.mkdir(parents=True)
    candidate.write_text("Antes.\nAção; depois.\nFim.\n", encoding="utf-8")
    control.write_text("Documento sem o sinal.\n", encoding="utf-8")
    records = [
        {"record_type": "manifest"},
        source_record(candidate, tmp_path),
        source_record(control, tmp_path, control=True),
    ]

    rows = preparer.build_review_rows(tmp_path, records)
    payload = preparer.canonical_csv_bytes(rows)
    decoded = list(csv.DictReader(io.StringIO(payload.decode())))

    assert len(decoded) == 2
    assert "Ação; depois." in decoded[0]["context"]
    assert decoded[0]["truth"] == ""
    assert decoded[0]["domain"] == ""
    assert decoded[0]["rationale"] == ""
    assert decoded[0]["review_status"] == "pending-human-review"
    assert decoded[0]["reviewer_role"] == ""
    assert decoded[1]["truth"] == ""
    assert decoded[1]["context"] == ""


def test_source_digest_mismatch_fails_closed(tmp_path: Path) -> None:
    preparer = load_preparer()
    source = tmp_path / "content/pt-br/docs/candidate.md"
    source.parent.mkdir(parents=True)
    source.write_text("Ação; depois.\n", encoding="utf-8")
    record = source_record(source, tmp_path)
    record["source_file_sha256"] = "0" * 64

    with pytest.raises(preparer.AuditError, match="source digest mismatch"):
        preparer.build_review_rows(tmp_path, [{"record_type": "manifest"}, record])


def test_review_packet_cannot_be_written_inside_repository(tmp_path: Path) -> None:
    preparer = load_preparer()

    with pytest.raises(preparer.AuditError, match="outside the repository"):
        preparer.write_packet(preparer.PROJECT_ROOT / "review-packet", [])

    summary = preparer.write_packet(tmp_path / "external-review", [])
    assert summary["case_count"] == 0

    review_csv = tmp_path / "external-review" / "pont-001-human-review-v2.csv"
    review_csv.write_text("human edits\n", encoding="utf-8")
    with pytest.raises(preparer.AuditError, match="refusing to overwrite"):
        preparer.write_packet(tmp_path / "external-review", [])


def test_preparer_does_not_import_product_code() -> None:
    tree = ast.parse(PREPARER_PATH.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)

    assert not any(name == "ste_lint" or name.startswith("ste_lint.") for name in imported)
