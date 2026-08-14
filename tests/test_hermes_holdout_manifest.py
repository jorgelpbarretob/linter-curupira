from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

GENERATOR_PATH = (
    Path(__file__).parents[1] / "tools" / "hermes" / "generate_pont_001_holdout_manifest.py"
)


def load_generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("hermes_holdout_manifest", GENERATOR_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_source(root: Path, relative_path: str, text: str) -> None:
    path = root / "content" / "pt-br" / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def test_selection_key_uses_commit_nul_and_repository_relative_path() -> None:
    generator = load_generator()
    source_path = "content/pt-br/docs/ação.md"
    expected = hashlib.sha256(
        generator.SOURCE_COMMIT.encode("ascii") + b"\0" + source_path.encode("utf-8")
    ).hexdigest()

    assert generator.selection_key(source_path) == expected


def test_manifest_is_complete_deterministic_and_contains_no_text_or_labels(tmp_path: Path) -> None:
    generator = load_generator()
    write_source(tmp_path, "docs/a.md", "Árvore; válida;\n")
    write_source(tmp_path, "docs/b.md", "Controle B.\n")
    write_source(tmp_path, "docs/c.md", "Controle C.\n")
    write_source(tmp_path, "docs/d.md", "Controle D.\n")
    write_source(tmp_path, "docs/sitemap.md", "Excluído;\n")
    write_source(tmp_path, "docs/reference/setup-tools/kubeadm/generated/x.md", "Excluído;\n")

    first = generator.build_manifest_records(tmp_path, control_count=2)
    second = generator.build_manifest_records(tmp_path, control_count=2)
    payload = generator.canonical_manifest_bytes(first)
    decoded = [json.loads(line) for line in payload.decode("utf-8").splitlines()]

    assert first == second
    assert decoded[0]["markdown_file_count"] == 6
    assert decoded[0]["eligible_file_count"] == 4
    assert decoded[0]["occurrence_file_count"] == 1
    assert decoded[0]["literal_semicolon_count"] == 2
    assert decoded[0]["control_document_count"] == 2
    assert [record["case_id"] for record in decoded[1:3]] == [
        "pont-holdout-occ-0001",
        "pont-holdout-occ-0002",
    ]
    assert decoded[1]["unicode_offset"] == 6
    assert decoded[1]["utf8_byte_offset"] == 7
    assert decoded[1]["line"] == 1
    assert decoded[1]["column"] == 7
    assert all(not generator.FORBIDDEN_FIELDS.intersection(record) for record in decoded)
    assert "Árvore".encode() not in payload
    assert b"Controle" not in payload
    assert b"sitemap.md" in payload[0 : payload.find(b"\n")]
    assert b"generated/x.md" not in payload


def test_forbidden_field_fails_closed() -> None:
    generator = load_generator()

    with pytest.raises(generator.AuditError, match="forbidden"):
        generator.canonical_manifest_bytes([{"text": "must not leak"}])


def test_generator_does_not_import_product_code() -> None:
    tree = ast.parse(GENERATOR_PATH.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)

    assert not any(name == "ste_lint" or name.startswith("ste_lint.") for name in imported)
