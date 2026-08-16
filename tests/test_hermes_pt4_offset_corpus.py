from __future__ import annotations

import ast
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from types import ModuleType

import pytest

TOOL_PATH = Path(__file__).parents[1] / "tools" / "hermes" / "prepare_pt4_offset_corpus.py"
KIMI_REVIEW_PATH = (
    Path(__file__).parents[1]
    / "artifacts"
    / "hermes"
    / "pt4-corpora"
    / "kimi-k2.7-supplementary-review-v1.json"
)
PANEL_REVIEW_PATH = KIMI_REVIEW_PATH.with_name("model-panel-review-v2.json")
CANONICAL_CORPUS_PATH = (
    Path(__file__).parents[1] / "corpus" / "hermes" / "pt4" / "pt4-offset-development-v1.jsonl"
)


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
    assert all(record["review_status"] == "pending-model-panel" for record in records)
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


def test_validation_rejects_overlap_between_analysis_and_structural_abstention() -> None:
    tool = load_tool()
    record = tool.build_records()[134]
    record["abstention_spans"][1]["start"] = 22

    with pytest.raises(tool.CorpusError, match="overlapping analysis and abstention"):
        tool.validate_case(record)


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


def test_every_contraction_and_clitic_in_mixed_cases_has_a_syntactic_expansion() -> None:
    records = {record["case_id"]: record for record in load_tool().build_records()}

    expected_forms = {
        "pt4-offset-dev-063": ["Afaste", "se", "de", "aquele", "painel", "."],
        "pt4-offset-dev-076": ["Dê", "lhe", "acesso", "a", "o", "painel", "."],
        "pt4-offset-dev-078": ["Aplique", "as", "em", "a", "superfície", "."],
    }
    for case_id, forms in expected_forms.items():
        assert [word["form"] for word in records[case_id]["syntactic_words"]] == forms


def test_equivalent_decimal_and_slash_units_use_consistent_surface_tokens() -> None:
    records = {record["case_id"]: record for record in load_tool().build_records()}

    expected_tokens = {
        "pt4-offset-dev-098": "7,2",
        "pt4-offset-dev-099": "120,00",
        "pt4-offset-dev-105": "L/s",
        "pt4-offset-dev-113": "2,1",
    }
    for case_id, expected_token in expected_tokens.items():
        assert expected_token in [token["text"] for token in records[case_id]["surface_tokens"]]


def test_kimi_review_is_supplementary_complete_and_does_not_open_gates() -> None:
    review = json.loads(KIMI_REVIEW_PATH.read_text(encoding="utf-8"))

    assert review["input"]["case_count"] == 160
    assert sum(batch["approve"] + batch["change_required"] for batch in review["batches"]) == 160
    assert review["response_validation"]["case_id_bijection"] == "pass"
    assert review["response_validation"]["strict_shape"] == "fail"
    assert review["local_reconciliation"]["automatic_corpus_changes"] == 0
    assert review["local_reconciliation"]["human_approval_granted"] is False
    assert review["local_reconciliation"]["canonical_hash_granted"] is False
    assert review["response_validation"]["confirmed_boundaries"] == {
        "candidate_outputs_seen": False,
        "human_review_replaced": False,
        "inference_authorized": False,
        "pont_001_data_seen": False,
    }


def test_committed_canonical_corpus_matches_unanimous_panel_audit() -> None:
    tool = load_tool()
    audit = json.loads(PANEL_REVIEW_PATH.read_text(encoding="utf-8"))
    payload = CANONICAL_CORPUS_PATH.read_bytes()
    records = [json.loads(line) for line in payload.decode().splitlines()]

    assert audit["status"] == "approved-unanimous"
    assert audit["freeze"]["canonical_corpus_sha256"] == tool.sha256_bytes(payload)
    assert audit["confirmed_boundaries"] == {
        "candidate_outputs_seen": False,
        "pont_001_data_seen": False,
        "inference_authorized": False,
    }
    assert all(provider["approved"] == 160 for provider in audit["providers"].values())
    assert all(record["review_status"] == "model-panel-approved" for record in records)
    for record in records:
        tool.validate_case(record)


def model_vote(
    tool: ModuleType,
    records: list[dict[str, object]],
    provider: str,
    *,
    changed_case: str | None = None,
) -> dict[str, object]:
    model = tool.PANEL_MODELS[provider]
    cases = []
    for record in records:
        changed = record["case_id"] == changed_case
        cases.append(
            {
                "case_id": record["case_id"],
                "decision": "change_required" if changed else "approve",
                "severity": "minor" if changed else "none",
                "fields": ["surface_tokens"] if changed else [],
                "rationale": "Requer ajuste." if changed else "",
                "proposed_change": "Ajustar tokenização." if changed else "",
            }
        )
    return {
        "schema_version": "hermes-pt4-model-vote/v1",
        "provider": provider,
        "model_requested": model,
        "model_returned": model,
        "proposal_sha256": tool.sha256_bytes(tool.proposal_bytes(records)),
        "verdict": "change_required" if changed_case else "approve",
        "cases": cases,
        "confirmed_boundaries": {
            "candidate_outputs_seen": False,
            "pont_001_data_seen": False,
            "inference_authorized": False,
        },
    }


def write_vote(path: Path, tool: ModuleType, vote: dict[str, object]) -> None:
    path.write_bytes(tool.canonical_record(vote))


def test_model_vote_requires_exact_identity_coverage_order_and_shape(tmp_path: Path) -> None:
    tool = load_tool()
    records = tool.build_records()
    vote = model_vote(tool, records, "maritaca")
    vote_path = tmp_path / "maritaca.json"
    write_vote(vote_path, tool, vote)

    assert tool.validate_model_vote(vote_path, "maritaca", records) == {
        "case_count": 160,
        "approved": 160,
        "change_required": 0,
        "provider": "maritaca",
        "model_requested": "sabia-4-thinking",
        "model_returned": "sabia-4-thinking",
        "vote_sha256": tool.sha256_bytes(vote_path.read_bytes()),
    }

    vote["cases"][0], vote["cases"][1] = vote["cases"][1], vote["cases"][0]
    write_vote(vote_path, tool, vote)
    with pytest.raises(tool.CorpusError, match="canonical order"):
        tool.validate_model_vote(vote_path, "maritaca", records)


def test_panel_refuses_missing_provider_and_change_required(tmp_path: Path) -> None:
    tool = load_tool()
    records = tool.build_records()
    vote_paths = {}
    for provider in ("maritaca", "grok"):
        path = tmp_path / f"{provider}.json"
        write_vote(path, tool, model_vote(tool, records, provider))
        vote_paths[provider] = path

    with pytest.raises(tool.CorpusError, match="exactly maritaca, grok and kimi"):
        tool.validate_model_panel(vote_paths, records)

    kimi_path = tmp_path / "kimi.json"
    write_vote(
        kimi_path,
        tool,
        model_vote(tool, records, "kimi", changed_case="pt4-offset-dev-063"),
    )
    vote_paths["kimi"] = kimi_path
    with pytest.raises(tool.CorpusError, match="rework is required"):
        tool.validate_model_panel(vote_paths, records)


def test_freeze_writes_unanimous_canonical_corpus_votes_and_manifest(tmp_path: Path) -> None:
    tool = load_tool()
    records = tool.build_records()
    vote_paths = {}
    for provider in tool.PANEL_MODELS:
        path = tmp_path / f"{provider}.json"
        write_vote(path, tool, model_vote(tool, records, provider))
        vote_paths[provider] = path
    output_dir = tmp_path / "canonical"

    summary = tool.freeze_model_panel(vote_paths, records, output_dir)

    corpus_path = output_dir / "pt4-offset-development-v1.jsonl"
    hash_path = output_dir / "pt4-offset-development-v1.jsonl.sha256"
    manifest_path = output_dir / "freeze-manifest.json"
    assert set(path.name for path in output_dir.iterdir()) == {
        corpus_path.name,
        hash_path.name,
        "maritaca-model-vote-v1.json",
        "grok-model-vote-v1.json",
        "kimi-model-vote-v1.json",
        manifest_path.name,
    }
    corpus_payload = corpus_path.read_bytes()
    frozen_records = [tool.json.loads(line) for line in corpus_payload.decode().splitlines()]
    assert len(frozen_records) == 160
    assert all(record["review_status"] == "model-panel-approved" for record in frozen_records)
    assert all(record["reviewer_role"] == "three-model-panel" for record in frozen_records)
    assert hash_path.read_text(encoding="utf-8") == (
        f"{tool.sha256_bytes(corpus_payload)}  {corpus_path.name}\n"
    )
    manifest = tool.json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest == {
        "approved": 160,
        "candidate_outputs_included": False,
        "canonical_corpus_sha256": tool.sha256_bytes(corpus_payload),
        "case_count": 160,
        "pont_001_data_included": False,
        "proposal_sha256": tool.sha256_bytes(tool.proposal_bytes(records)),
        "schema_version": "hermes-pt4-offset-model-panel-freeze/v1",
        "unanimous": True,
        "vote_sha256": {
            provider: tool.sha256_bytes(path.read_bytes()) for provider, path in vote_paths.items()
        },
    }
    assert summary == {
        **manifest,
        "manifest_sha256": tool.sha256_bytes(manifest_path.read_bytes()),
    }


def test_freeze_refuses_to_overwrite_existing_output(tmp_path: Path) -> None:
    tool = load_tool()
    output_dir = tmp_path / "canonical"
    output_dir.mkdir()
    marker = output_dir / "keep.txt"
    marker.write_text("preserve", encoding="utf-8")

    with pytest.raises(tool.CorpusError, match="already exists"):
        tool.freeze_model_panel({}, tool.build_records(), output_dir)

    assert marker.read_text(encoding="utf-8") == "preserve"


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
