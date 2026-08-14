from __future__ import annotations

import ast
import hashlib
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

SCANNER_PATH = Path(__file__).parents[1] / "tools" / "product_evidence" / "round2_scanner.py"


def load_scanner() -> ModuleType:
    spec = importlib.util.spec_from_file_location("round2_scanner", SCANNER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_selection_key_is_exact_utf8_without_newline() -> None:
    scanner = load_scanner()

    expected = hashlib.sha256("seed|docs/ação.md".encode()).hexdigest()

    assert scanner.selection_key("seed", "docs/ação.md") == expected


def test_scan_is_superinclusive_but_excludes_structural_markup_from_prose() -> None:
    scanner = load_scanner()
    text = """---
title: Hidden; title.
---
# Heading?

Visible sentence one. Visible sentence two?

`code; not prose.` Then [visible label](target;).

```python
hidden; sentence.
```

Lead-in has these items.
- First item.
- Second item.
"""

    counts = scanner.scan_text(text, text_type="descriptive")

    assert counts.sentence_complete == 6
    assert counts.sentence_incomplete == 0
    assert counts.paragraphs == 3
    assert counts.punctuation == 4
    assert counts.list_runs == 1


def test_scan_counts_nested_lists_separately_and_excludes_quote_from_paragraphs() -> None:
    scanner = load_scanner()
    text = """Intro.

- Outer one.
  - Nested one.
  - Nested two.
- Outer two.

> Quoted sentence.
"""

    counts = scanner.scan_text(text, text_type="descriptive")

    assert counts.sentence_complete == 6
    assert counts.paragraphs == 1
    assert counts.list_runs == 2


def test_procedural_text_does_not_create_paragraph_units() -> None:
    scanner = load_scanner()

    counts = scanner.scan_text("First sentence.\n\nSecond sentence.\n", text_type="procedural")

    assert counts.sentence_complete == 2
    assert counts.paragraphs == 0


def test_digest_mismatch_aborts() -> None:
    scanner = load_scanner()

    with pytest.raises(scanner.AuditError, match="digest mismatch"):
        scanner.verify_digest(b"actual", "0" * 64, "fixture")


def test_sentence_reduction_does_not_remove_document_from_other_tranches() -> None:
    scanner = load_scanner()
    excluded = next(
        document
        for document in scanner.DOCUMENTS
        if document.path in scanner.SENT001_EXCLUDED_PATHS
    )
    retained = next(
        document
        for document in scanner.DOCUMENTS
        if document.text_type == "procedural"
        and document.path not in scanner.SENT001_EXCLUDED_PATHS
    )
    rows = [
        (excluded, scanner.ScanCounts(100, 27, 0, 13, 18)),
        (retained, scanner.ScanCounts(120, 14, 0, 20, 14)),
    ]

    counts = scanner.aggregate_rule_counts(rows)

    assert counts["STE-I9-SENT-001"] == 134
    assert counts["STE-I9-PUNCT-001"] == 33
    assert counts["STE-I9-LIST-001"] == 32


def test_inventory_preserves_raw_spans_and_pending_review_profile() -> None:
    scanner = load_scanner()
    document = scanner.Document("dapr", "descriptive", "key", "sha", "fixture.md")
    text = """Intro [label](destination).

- First.
  Continued.
- Second.
"""

    records = scanner.extract_document_records(text, document)
    sentence_records = [record for record in records if record["rule_id"] == "STE-I9-SENT-002"]
    paragraph_records = [record for record in records if record["rule_id"] == "STE-I9-PARA-001"]
    list_records = [record for record in records if record["rule_id"] == "STE-I9-LIST-001"]

    assert [text[record["start_offset"] : record["end_offset"]] for record in sentence_records] == [
        "Intro [label](destination).",
        "First.",
        "Continued.",
        "Second.",
    ]
    assert (
        text[paragraph_records[0]["start_offset"] : paragraph_records[0]["end_offset"]]
        == "Intro [label](destination)."
    )
    assert text[list_records[0]["start_offset"] : list_records[0]["end_offset"]] == (
        "- First.\n  Continued.\n- Second."
    )
    assert (
        text[list_records[0]["lead_in_start_offset"] : list_records[0]["lead_in_end_offset"]]
        == "Intro [label](destination)."
    )
    assert all(record["truth"] == "pending-review" for record in records)
    assert all(record["review_status"] == "pending-review" for record in records)
    assert all("rationale" not in record and "text" not in record for record in records)


def test_inventory_classifies_each_semicolon_without_dropping_markup() -> None:
    scanner = load_scanner()
    document = scanner.Document("dapr", "procedural", "key", "sha", "fixture.md")
    text = "`masked;` Visible;\n"

    records = scanner.extract_document_records(text, document)
    punctuation = [record for record in records if record["rule_id"] == "STE-I9-PUNCT-001"]

    assert len(punctuation) == 2
    assert [record["structural_context"] for record in punctuation] == [
        "markup_or_code",
        "visible_prose",
    ]
    assert all(record["end_offset"] == record["start_offset"] + 1 for record in punctuation)
    assert len({record["case_id"] for record in records}) == len(records)


def test_inventory_list_without_lead_in_uses_exact_sentinels() -> None:
    scanner = load_scanner()
    document = scanner.Document("dapr", "procedural", "key", "sha", "fixture.md")

    records = scanner.extract_document_records("- One.\n- Two.\n", document)
    list_record = next(record for record in records if record["rule_id"] == "STE-I9-LIST-001")

    assert list_record["lead_in_status"] == "not_found"
    assert list_record["lead_in_start_offset"] == -1
    assert list_record["lead_in_end_offset"] == -1
    assert list_record["lead_in_slice_sha256"] == ""
    assert list_record["blank_lines_before"] == -1
    assert list_record["list_terminal"] == "absent"
    assert list_record["blockers"] == []


def test_inventory_coordinates_and_serialization_are_canonical() -> None:
    scanner = load_scanner()
    document = scanner.Document("dapr", "descriptive", "key", "sha", "fixture.md")
    text = "A sentence.\n"
    records = scanner.extract_document_records(text, document)

    assert scanner.offset_to_position(text, len(text)) == (2, 1)
    payload = scanner.canonical_inventory_bytes(records)

    assert payload.endswith(b"\n")
    assert b'"review_status":"pending-review"' in payload
    assert b'": ' not in payload


def test_scanner_does_not_import_product_code() -> None:
    tree = ast.parse(SCANNER_PATH.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)

    assert not any(name == "ste_lint" or name.startswith("ste_lint.") for name in imported)
