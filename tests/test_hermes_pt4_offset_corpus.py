from __future__ import annotations

import ast
import importlib.util
import sys
from collections import Counter
from pathlib import Path
from types import ModuleType

import pytest

TOOL_PATH = Path(__file__).parents[1] / "tools" / "hermes" / "prepare_pt4_offset_corpus.py"


def load_tool() -> ModuleType:
    sys.path.insert(0, str(TOOL_PATH.parent))
    spec = importlib.util.spec_from_file_location("hermes_pt4_offset_corpus", TOOL_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_proposal_is_balanced_deterministic_and_pending() -> None:
    tool = load_tool()
    records = tool.build_records()

    assert len(records) == 160
    assert Counter(record["family"] for record in records) == {
        "unicode-newlines": 40,
        "contractions-clitics": 40,
        "technical-tokens": 40,
        "markdown-boundaries": 40,
    }
    assert len({record["case_id"] for record in records}) == 160
    assert all(record["review_status"] == "pending-human-review" for record in records)
    assert tool.PROPOSAL_PATH.read_bytes() == tool.proposal_bytes(records)
    assert tool.PROPOSAL_HASH_PATH.read_text(encoding="utf-8") == (
        f"{tool.sha256_bytes(tool.proposal_bytes(records))}  {tool.PROPOSAL_PATH.name}\n"
    )


def test_every_token_sentence_and_word_respects_the_offset_contract() -> None:
    tool = load_tool()
    records = tool.build_records()

    for record in records:
        tool.validate_case(record)
        text = record["text"]
        for token in record["surface_tokens"]:
            assert text[token["start"] : token["end"]] == token["text"]
        for sentence in record["sentences"]:
            selected = record["surface_tokens"][
                sentence["first_surface_token"] : sentence["past_last_surface_token"]
            ]
            assert sentence["start"] == selected[0]["start"]
            assert sentence["end"] == selected[-1]["end"]


def test_proposal_covers_mwt_unicode_and_structural_abstention() -> None:
    tool = load_tool()
    records = tool.build_records()

    assert any("\r\n" in record["text"] for record in records)
    assert any("\u200d" in record["text"] for record in records)
    assert any(
        len(
            [
                word
                for word in record["syntactic_words"]
                if word["surface_token_index"] == surface_index
            ]
        )
        > 1
        for record in records
        for surface_index in range(len(record["surface_tokens"]))
    )
    structural = [record for record in records if record["family"] == "markdown-boundaries"]
    assert any(record["abstention_spans"] for record in structural)
    assert any(not record["analysis_segments"] for record in structural)


def test_completed_review_requires_a_second_human_to_approve_every_case(tmp_path: Path) -> None:
    tool = load_tool()
    records = tool.build_records()
    rows = tool.review_rows(records)
    review_path = tmp_path / "review.csv"
    review_path.write_bytes(tool.canonical_review_csv(rows))

    with pytest.raises(tool.CorpusError, match="not human-reviewed"):
        tool.validate_completed_review(review_path, records)

    for row in rows:
        row.update(
            {
                "review_status": "approved",
                "reviewed_by": "independent-human-reviewer",
                "reviewer_role": "pt-BR-language-reviewer",
                "reviewed_on": "2026-08-16",
            }
        )
    review_path.write_bytes(tool.canonical_review_csv(rows))

    assert tool.validate_completed_review(review_path, records) == {
        "case_count": 160,
        "approved": 160,
        "rejected": 0,
    }


def test_builder_is_model_blind_and_does_not_import_product_code() -> None:
    tree = ast.parse(TOOL_PATH.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)

    assert not any(
        name == "hermes_lint" or name.startswith("hermes_lint.") or name in {"spacy", "stanza"}
        for name in imported
    )
