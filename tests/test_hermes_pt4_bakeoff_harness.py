from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from types import ModuleType

import pytest

TOOL_PATH = Path(__file__).parents[1] / "tools" / "hermes" / "pt4_bakeoff_harness.py"
PETROGOLD_PATH = (
    Path(__file__).parents[1] / "corpus" / "hermes" / "pt4" / "pt_petrogold-ud-test-r2.18.conllu"
)
OFFSET_CORPUS_PATH = (
    Path(__file__).parents[1] / "corpus" / "hermes" / "pt4" / "pt4-offset-development-v1.jsonl"
)
MWT_FIXTURE = """# text = A pressão nas linhas.
# sent_id = fixture-1
# newdoc id = fixture-doc
1\tA\to\tDET\t_\tDefinite=Def\t2\tdet\t_\t_
2\tpressão\tpressão\tNOUN\t_\tGender=Fem\t5\tnsubj\t_\t_
3-4\tnas\t_\t_\t_\t_\t_\t_\t_\t_
3\tem\tem\tADP\t_\t_\t5\tcase\t_\t_
4\tas\to\tDET\t_\tNumber=Plur\t5\tdet\t_\t_
5\tlinhas\tlinha\tNOUN\t_\tNumber=Plur\t0\troot\t_\tSpaceAfter=No
6\t.\t.\tPUNCT\t_\t_\t5\tpunct\t_\t_
"""


def load_tool() -> ModuleType:
    sys.path.insert(0, str(TOOL_PATH.parent))
    spec = importlib.util.spec_from_file_location("hermes_pt4_bakeoff_harness", TOOL_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_project_conllu_preserves_surface_mwt_words_offsets_and_heads() -> None:
    records = load_tool().project_conllu(MWT_FIXTURE)

    assert len(records) == 1
    record = records[0]
    assert record["case_id"] == "fixture-1"
    assert record["document_id"] == "fixture-doc"
    assert record["text"] == "A pressão nas linhas."
    assert record["surface_tokens"] == [
        {"text": "A", "start": 0, "end": 1},
        {"text": "pressão", "start": 2, "end": 9},
        {"text": "nas", "start": 10, "end": 13},
        {"text": "linhas", "start": 14, "end": 20},
        {"text": ".", "start": 20, "end": 21},
    ]
    assert [word["form"] for word in record["words"]] == [
        "A",
        "pressão",
        "em",
        "as",
        "linhas",
        ".",
    ]
    assert [word["surface_token_index"] for word in record["words"]] == [0, 1, 2, 2, 3, 4]
    assert [word["head_word_index"] for word in record["words"]] == [1, 4, 4, 4, None, 4]
    assert record["words"][1]["features"] == [["Gender", "Fem"]]
    assert record["sentences"] == [
        {
            "start": 0,
            "end": 21,
            "first_surface_token": 0,
            "past_last_surface_token": 5,
            "first_word": 0,
            "past_last_word": 6,
        }
    ]


def test_project_conllu_accepts_the_complete_frozen_petrogold_split() -> None:
    records = load_tool().project_conllu(PETROGOLD_PATH.read_text(encoding="utf-8"))

    assert len(records) == 1039
    assert len({record["document_id"] for record in records}) == 2
    assert sum(len(record["surface_tokens"]) for record in records) == 27453
    assert sum(len(record["words"]) for record in records) == 29623


def test_project_conllu_requires_exactly_one_dependency_root_per_sentence() -> None:
    tool = load_tool()
    without_root = MWT_FIXTURE.replace(
        "5\tlinhas\tlinha\tNOUN\t_\tNumber=Plur\t0\troot",
        "5\tlinhas\tlinha\tNOUN\t_\tNumber=Plur\t2\tdep",
    )

    with pytest.raises(tool.HarnessError, match="exactly one dependency root"):
        tool.project_conllu(without_root)


def test_project_conllu_uses_space_after_only_from_the_surface_token() -> None:
    tool = load_tool()
    word_level_marker = MWT_FIXTURE.replace(
        "4\tas\to\tDET\t_\tNumber=Plur\t5\tdet\t_\t_",
        "4\tas\to\tDET\t_\tNumber=Plur\t5\tdet\t_\tSpaceAfter=No",
    )
    surface_level_marker = MWT_FIXTURE.replace(
        "3-4\tnas\t_\t_\t_\t_\t_\t_\t_\t_",
        "3-4\tnas\t_\t_\t_\t_\t_\t_\t_\tSpaceAfter=No",
    )

    assert tool.project_conllu(word_level_marker)[0]["text"] == "A pressão nas linhas."
    with pytest.raises(tool.HarnessError, match="invalid text between surface tokens"):
        tool.project_conllu(surface_level_marker)


@pytest.mark.parametrize("invalid_id", ["01", "3a", "1-2-3"])
def test_project_conllu_rejects_malformed_row_identifiers(invalid_id: str) -> None:
    tool = load_tool()
    malformed_row = f"{invalid_id}\tmalformado\t_\t_\t_\t_\t_\t_\t_\t_\n"

    with pytest.raises(tool.HarnessError, match="invalid CoNLL-U ID"):
        tool.project_conllu(MWT_FIXTURE + malformed_row)


def test_project_conllu_rejects_empty_surface_forms() -> None:
    tool = load_tool()
    conllu = "# text =  \n# sent_id = empty-form\n1\t\t_\tX\t_\t_\t0\troot\t_\t_\n"

    with pytest.raises(tool.HarnessError, match="FORM must not be empty"):
        tool.project_conllu(conllu)


def test_project_conllu_rejects_empty_feature_names_or_values() -> None:
    tool = load_tool()
    malformed = MWT_FIXTURE.replace("Gender=Fem", "Gender=")

    with pytest.raises(tool.HarnessError, match="invalid FEATS item"):
        tool.project_conllu(malformed)


def test_project_conllu_handles_crlf_without_leaking_carriage_returns() -> None:
    record = load_tool().project_conllu(MWT_FIXTURE.replace("\n", "\r\n"))[0]

    assert record["case_id"] == "fixture-1"
    assert record["document_id"] == "fixture-doc"
    assert record["text"] == "A pressão nas linhas."


def test_score_corpora_returns_perfect_metrics_for_identical_analysis() -> None:
    tool = load_tool()
    gold = tool.project_conllu(MWT_FIXTURE)

    result = tool.score_corpora(gold, gold)

    assert result == {
        "schema_version": "hermes-pt4-bakeoff-metrics/v1",
        "case_count": 1,
        "gold_surface_tokens": 5,
        "candidate_surface_tokens": 5,
        "aligned_words": 6,
        "unaligned_gold_words": 0,
        "unaligned_candidate_words": 0,
        "offset_errors": 0,
        "candidate_abstentions": {"case_count": 0, "by_reason": {}},
        "metrics": {
            "token_precision": 1.0,
            "token_recall": 1.0,
            "token_f1": 1.0,
            "sentence_precision": 1.0,
            "sentence_recall": 1.0,
            "sentence_f1": 1.0,
            "lemma_accuracy": 1.0,
            "upos_accuracy": 1.0,
            "feats_micro_f1": 1.0,
            "uas": 1.0,
            "las": 1.0,
        },
    }


def test_score_corpora_counts_morphology_and_dependency_errors_on_aligned_words() -> None:
    tool = load_tool()
    gold = tool.project_conllu(MWT_FIXTURE)
    candidate = deepcopy(gold)
    candidate[0]["words"][0]["head_word_index"] = None
    candidate[0]["words"][1].update(
        {
            "lemma": "pressao",
            "upos": "X",
            "features": [["Gender", "Masc"]],
            "dependency": "dep",
        }
    )

    metrics = tool.score_corpora(gold, candidate)["metrics"]

    assert metrics == {
        "token_precision": 1.0,
        "token_recall": 1.0,
        "token_f1": 1.0,
        "sentence_precision": 1.0,
        "sentence_recall": 1.0,
        "sentence_f1": 1.0,
        "lemma_accuracy": 5 / 6,
        "upos_accuracy": 5 / 6,
        "feats_micro_f1": 0.75,
        "uas": 5 / 6,
        "las": 4 / 6,
    }


def test_score_corpora_aligns_words_only_through_exact_surface_spans() -> None:
    tool = load_tool()
    gold = tool.project_conllu(MWT_FIXTURE)
    candidate = deepcopy(gold)
    candidate[0]["surface_tokens"][2:3] = [
        {"text": "n", "start": 10, "end": 11},
        {"text": "as", "start": 11, "end": 13},
    ]
    for word, surface_index in zip(candidate[0]["words"], [0, 1, 2, 3, 4, 5], strict=True):
        word["surface_token_index"] = surface_index
    candidate[0]["sentences"][0]["past_last_surface_token"] = 6

    result = tool.score_corpora(gold, candidate)

    assert result["gold_surface_tokens"] == 5
    assert result["candidate_surface_tokens"] == 6
    assert result["aligned_words"] == 4
    assert result["unaligned_gold_words"] == 2
    assert result["unaligned_candidate_words"] == 2
    assert result["offset_errors"] == 0
    assert result["metrics"]["token_precision"] == 4 / 6
    assert result["metrics"]["token_recall"] == 4 / 5
    assert result["metrics"]["token_f1"] == pytest.approx(8 / 11)
    assert result["metrics"]["lemma_accuracy"] == 0.5
    assert result["metrics"]["upos_accuracy"] == 0.5
    assert result["metrics"]["feats_micro_f1"] == 0.75
    assert result["metrics"]["uas"] == 0.5
    assert result["metrics"]["las"] == 0.5


def test_score_corpora_does_not_credit_a_head_that_is_not_aligned() -> None:
    tool = load_tool()
    gold = tool.project_conllu(MWT_FIXTURE)
    candidate = deepcopy(gold)
    del candidate[0]["surface_tokens"][1]
    del candidate[0]["words"][1]
    candidate[0]["words"][0]["head_word_index"] = None
    for word, surface_index in zip(candidate[0]["words"], [0, 1, 1, 2, 3], strict=True):
        word["surface_token_index"] = surface_index
    for word in candidate[0]["words"]:
        head = word["head_word_index"]
        if head is not None and head > 1:
            word["head_word_index"] = head - 1
    candidate[0]["sentences"][0].update({"past_last_surface_token": 4, "past_last_word": 5})

    result = tool.score_corpora(gold, candidate)

    assert result["aligned_words"] == 5
    assert result["unaligned_gold_words"] == 1
    assert result["metrics"]["uas"] == 4 / 6


def test_score_corpora_penalizes_missing_word_inside_a_matched_surface_token() -> None:
    tool = load_tool()
    gold = tool.project_conllu(MWT_FIXTURE)
    candidate = deepcopy(gold)
    del candidate[0]["words"][3]
    for word in candidate[0]["words"]:
        head = word["head_word_index"]
        if head is not None and head > 3:
            word["head_word_index"] = head - 1
    candidate[0]["sentences"][0]["past_last_word"] = 5

    result = tool.score_corpora(gold, candidate)
    metrics = result["metrics"]

    assert metrics["token_f1"] == 1.0
    assert result["unaligned_gold_words"] == 1
    assert result["unaligned_candidate_words"] == 0
    assert metrics["lemma_accuracy"] == 5 / 6
    assert metrics["upos_accuracy"] == 5 / 6
    assert metrics["feats_micro_f1"] == 6 / 7
    assert metrics["uas"] == 5 / 6
    assert metrics["las"] == 5 / 6


def test_offset_corpus_scores_only_metrics_supported_by_its_gold() -> None:
    tool = load_tool()
    gold = tool.project_offset_jsonl(OFFSET_CORPUS_PATH.read_text(encoding="utf-8"))

    result = tool.score_corpora(gold, gold)

    assert len(gold) == 160
    assert result["gold_surface_tokens"] == 872
    assert result["offset_errors"] == 0
    assert result["metrics"]["token_f1"] == 1.0
    assert result["metrics"]["sentence_f1"] == 1.0
    assert result["metrics"]["lemma_accuracy"] is None
    assert result["metrics"]["upos_accuracy"] is None
    assert result["metrics"]["feats_micro_f1"] is None
    assert result["metrics"]["uas"] is None
    assert result["metrics"]["las"] is None


def test_score_corpora_reports_candidate_offset_contract_errors() -> None:
    tool = load_tool()
    gold = tool.project_conllu(MWT_FIXTURE)
    candidate = deepcopy(gold)
    candidate[0]["surface_tokens"][0]["end"] = 2

    result = tool.score_corpora(gold, candidate)

    assert result["offset_errors"] == 1
    assert result["metrics"]["token_recall"] == 4 / 5


def test_score_corpora_rejects_serialized_backend_fields() -> None:
    tool = load_tool()
    gold = tool.project_conllu(MWT_FIXTURE)
    candidate = deepcopy(gold)
    candidate[0]["spacy_doc"] = {"vendor": "sdk-object"}

    with pytest.raises(tool.HarnessError, match="candidate fields"):
        tool.score_corpora(gold, candidate)


def test_score_corpora_rejects_malformed_feature_pairs() -> None:
    tool = load_tool()
    gold = tool.project_conllu(MWT_FIXTURE)
    candidate = deepcopy(gold)
    candidate[0]["words"][0]["features"] = [["Definite"]]

    with pytest.raises(tool.HarnessError, match="candidate feature fields"):
        tool.score_corpora(gold, candidate)


@pytest.mark.parametrize("field", ["surface_tokens", "words", "sentences"])
def test_score_corpora_rejects_nonlist_candidate_collections(field: str) -> None:
    tool = load_tool()
    gold = tool.project_conllu(MWT_FIXTURE)
    candidate = deepcopy(gold)
    candidate[0][field] = None

    with pytest.raises(tool.HarnessError, match="candidate collections"):
        tool.score_corpora(gold, candidate)


def test_score_corpora_rejects_nonstring_candidate_token_text() -> None:
    tool = load_tool()
    gold = tool.project_conllu(MWT_FIXTURE)
    candidate = deepcopy(gold)
    candidate[0]["surface_tokens"][0]["text"] = None

    with pytest.raises(tool.HarnessError, match="candidate token fields"):
        tool.score_corpora(gold, candidate)


def test_score_corpora_reports_candidate_abstention_reasons() -> None:
    tool = load_tool()
    gold = tool.project_conllu(MWT_FIXTURE)
    candidate = deepcopy(gold)
    candidate[0]["abstention_reason"] = "unsupported-tokenization"

    result = tool.score_corpora(gold, candidate)

    assert result["candidate_abstentions"] == {
        "case_count": 1,
        "by_reason": {"unsupported-tokenization": 1},
    }


def test_score_corpora_reports_words_assigned_across_sentence_boundaries() -> None:
    tool = load_tool()
    records = tool.project_offset_jsonl(OFFSET_CORPUS_PATH.read_text(encoding="utf-8"))
    gold = [next(record for record in records if len(record["sentences"]) == 2)]
    candidate = deepcopy(gold)
    second_sentence = candidate[0]["sentences"][1]
    candidate[0]["words"][second_sentence["first_word"]]["sentence_index"] = 0

    result = tool.score_corpora(gold, candidate)

    assert result["offset_errors"] >= 1


def test_score_corpora_reports_gaps_in_candidate_sentence_partitions() -> None:
    tool = load_tool()
    records = tool.project_offset_jsonl(OFFSET_CORPUS_PATH.read_text(encoding="utf-8"))
    gold = [next(record for record in records if len(record["sentences"]) == 2)]
    candidate = deepcopy(gold)
    candidate[0]["sentences"][0]["past_last_surface_token"] -= 1
    candidate[0]["sentences"][0]["end"] = candidate[0]["surface_tokens"][2]["end"]
    candidate[0]["sentences"][0]["past_last_word"] -= 1

    result = tool.score_corpora(gold, candidate)

    assert result["offset_errors"] >= 1


def test_project_offset_rejects_nonminimal_sentence_envelopes() -> None:
    tool = load_tool()
    source = json.loads(OFFSET_CORPUS_PATH.read_text(encoding="utf-8").splitlines()[0])
    source["sentences"][0]["end"] += 1

    with pytest.raises(tool.HarnessError, match="sentence envelope"):
        tool.project_offset_jsonl(json.dumps(source, ensure_ascii=False))


def test_project_offset_rejects_noncontiguous_sentence_word_ranges() -> None:
    tool = load_tool()
    sources = [
        json.loads(line) for line in OFFSET_CORPUS_PATH.read_text(encoding="utf-8").splitlines()
    ]
    source = next(record for record in sources if len(record["sentences"]) == 2)
    source["syntactic_words"][1], source["syntactic_words"][4] = (
        source["syntactic_words"][4],
        source["syntactic_words"][1],
    )

    with pytest.raises(tool.HarnessError, match="word range is not contiguous"):
        tool.project_offset_jsonl(json.dumps(source, ensure_ascii=False))


def test_project_offset_rejects_overlapping_surface_spans() -> None:
    tool = load_tool()
    source = json.loads(OFFSET_CORPUS_PATH.read_text(encoding="utf-8").splitlines()[0])
    source["surface_tokens"][1]["start"] = source["surface_tokens"][0]["start"]

    with pytest.raises(tool.HarnessError, match="invalid token or sentence offsets"):
        tool.project_offset_jsonl(json.dumps(source, ensure_ascii=False))


def test_canonical_jsonl_is_stable_and_round_trips_without_sdk_types() -> None:
    tool = load_tool()
    records = tool.project_conllu(MWT_FIXTURE)

    first = tool.canonical_jsonl(records)
    second = tool.canonical_jsonl(records)

    assert first == second
    assert first.endswith(b"\n")
    assert [json.loads(line) for line in first.decode().splitlines()] == records
    assert b"spacy" not in first
    assert b"stanza" not in first


def test_cli_projects_gold_atomically_and_refuses_overwrite(tmp_path: Path) -> None:
    source = tmp_path / "fixture.conllu"
    output = tmp_path / "gold.jsonl"
    source.write_text(MWT_FIXTURE, encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(TOOL_PATH), "project-conllu", str(source), str(output)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout) == {
        "case_count": 1,
        "output": str(output),
        "sha256": load_tool().sha256_bytes(output.read_bytes()),
    }
    refused = subprocess.run(
        [sys.executable, str(TOOL_PATH), "project-conllu", str(source), str(output)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert refused.returncode != 0
    assert "already exists" in refused.stderr


def test_cli_projects_the_frozen_offset_corpus(tmp_path: Path) -> None:
    output = tmp_path / "offset-gold.jsonl"

    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL_PATH),
            "project-offset",
            str(OFFSET_CORPUS_PATH),
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(completed.stdout)
    assert summary["case_count"] == 160
    assert summary["sha256"] == load_tool().sha256_bytes(output.read_bytes())


def test_cli_scores_precomputed_candidate_without_running_a_backend(tmp_path: Path) -> None:
    tool = load_tool()
    analysis = tool.canonical_jsonl(tool.project_conllu(MWT_FIXTURE))
    gold = tmp_path / "gold.jsonl"
    candidate = tmp_path / "candidate.jsonl"
    output = tmp_path / "metrics.json"
    gold.write_bytes(analysis)
    candidate.write_bytes(analysis)

    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL_PATH),
            "score",
            str(gold),
            str(candidate),
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout)["sha256"] == tool.sha256_bytes(output.read_bytes())
    assert json.loads(output.read_text(encoding="utf-8"))["metrics"]["las"] == 1.0


def test_quality_gate_requires_both_corpora_and_every_preregistered_floor() -> None:
    tool = load_tool()
    petrogold = tool.project_conllu(MWT_FIXTURE)
    offsets = tool.project_offset_jsonl(OFFSET_CORPUS_PATH.read_text(encoding="utf-8"))
    petrogold_metrics = tool.score_corpora(petrogold, petrogold)
    offset_metrics = tool.score_corpora(offsets, offsets)

    accepted = tool.evaluate_quality_gates(petrogold_metrics, offset_metrics)
    offset_metrics["offset_errors"] = 1
    rejected = tool.evaluate_quality_gates(petrogold_metrics, offset_metrics)

    assert accepted["status"] == "quality-pass-operational-pending"
    assert accepted["quality_passed"] is True
    assert all(accepted["checks"].values())
    assert accepted["inference_authorized"] is False
    assert rejected["quality_passed"] is False
    assert rejected["checks"]["offset_errors"] is False
