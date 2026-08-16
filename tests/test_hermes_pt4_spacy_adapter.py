from __future__ import annotations

import importlib.util
import json
import socket
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

import pytest

TOOL_PATH = Path(__file__).parents[1] / "tools" / "hermes" / "pt4_spacy_adapter.py"


def load_tool() -> ModuleType:
    sys.path.insert(0, str(TOOL_PATH.parent))
    spec = importlib.util.spec_from_file_location("hermes_pt4_spacy_adapter", TOOL_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeMorph:
    def __init__(self, **features: str) -> None:
        self._features = features

    def to_dict(self) -> dict[str, str]:
        return self._features


@dataclass
class FakeToken:
    i: int
    text: str
    idx: int
    lemma_: str
    pos_: str
    tag_: str
    dep_: str
    morph: FakeMorph
    is_space: bool = False
    head: FakeToken | None = None


@dataclass(frozen=True)
class FakeSentence:
    tokens: tuple[FakeToken, ...]

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(self.tokens)


@dataclass(frozen=True)
class FakeDoc:
    text: str
    tokens: tuple[FakeToken, ...]
    sentences: tuple[FakeSentence, ...]

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(self.tokens)

    @property
    def sents(self) -> tuple[FakeSentence, ...]:
        return self.sentences


def test_adapt_doc_emits_the_frozen_schema_with_exact_unicode_offsets() -> None:
    tool = load_tool()
    text = "Válvula aberta."
    valve = FakeToken(0, "Válvula", 0, "válvula", "NOUN", "N", "nsubj", FakeMorph())
    open_ = FakeToken(
        1,
        "aberta",
        8,
        "abrir",
        "VERB",
        "V",
        "ROOT",
        FakeMorph(Gender="Fem", Number="Sing"),
    )
    period = FakeToken(2, ".", 14, ".", "PUNCT", ".", "punct", FakeMorph())
    valve.head = open_
    open_.head = open_
    period.head = open_
    doc = FakeDoc(text, (valve, open_, period), (FakeSentence((valve, open_, period)),))

    record = tool.adapt_doc("fixture-1", "doc-1", text, doc)

    assert record == {
        "schema_version": "hermes-pt4-linguistic-analysis/v1",
        "case_id": "fixture-1",
        "document_id": "doc-1",
        "text": text,
        "surface_tokens": [
            {"text": "Válvula", "start": 0, "end": 7},
            {"text": "aberta", "start": 8, "end": 14},
            {"text": ".", "start": 14, "end": 15},
        ],
        "words": [
            {
                "form": "Válvula",
                "surface_token_index": 0,
                "lemma": "válvula",
                "upos": "NOUN",
                "xpos": "N",
                "features": [],
                "dependency": "nsubj",
                "head_word_index": 1,
                "sentence_index": 0,
            },
            {
                "form": "aberta",
                "surface_token_index": 1,
                "lemma": "abrir",
                "upos": "VERB",
                "xpos": "V",
                "features": [["Gender", "Fem"], ["Number", "Sing"]],
                "dependency": "root",
                "head_word_index": None,
                "sentence_index": 0,
            },
            {
                "form": ".",
                "surface_token_index": 2,
                "lemma": ".",
                "upos": "PUNCT",
                "xpos": ".",
                "features": [],
                "dependency": "punct",
                "head_word_index": 1,
                "sentence_index": 0,
            },
        ],
        "sentences": [
            {
                "start": 0,
                "end": 15,
                "first_surface_token": 0,
                "past_last_surface_token": 3,
                "first_word": 0,
                "past_last_word": 3,
            }
        ],
        "abstention_reason": None,
    }


def test_adapt_doc_rejects_backend_text_normalization() -> None:
    tool = load_tool()
    token = FakeToken(0, "ação", 0, "ação", "NOUN", "N", "ROOT", FakeMorph())
    token.head = token
    doc = FakeDoc("ação", (token,), (FakeSentence((token,)),))

    with pytest.raises(tool.AdapterError, match="text differs"):
        tool.adapt_doc("fixture-normalized", None, "ac\u0327a\u0303o", doc)


def test_adapt_doc_rejects_a_token_without_an_exact_surface_slice() -> None:
    tool = load_tool()
    token = FakeToken(0, "válvula", 1, "válvula", "NOUN", "N", "ROOT", FakeMorph())
    token.head = token
    doc = FakeDoc("válvula", (token,), (FakeSentence((token,)),))

    with pytest.raises(tool.AdapterError, match="exact surface slice"):
        tool.adapt_doc("fixture-bad-offset", None, doc.text, doc)


def test_adapt_doc_rejects_a_dependency_that_crosses_sentences() -> None:
    tool = load_tool()
    first = FakeToken(0, "A", 0, "a", "NOUN", "N", "ROOT", FakeMorph())
    crossing = FakeToken(1, "X", 2, "x", "NOUN", "N", "dep", FakeMorph())
    first_period = FakeToken(2, ".", 3, ".", "PUNCT", ".", "punct", FakeMorph())
    second = FakeToken(3, "B", 5, "b", "NOUN", "N", "ROOT", FakeMorph())
    second_period = FakeToken(4, ".", 6, ".", "PUNCT", ".", "punct", FakeMorph())
    first.head = first
    crossing.head = second
    first_period.head = first
    second.head = second
    second_period.head = second
    doc = FakeDoc(
        "A X. B.",
        (first, crossing, first_period, second, second_period),
        (
            FakeSentence((first, crossing, first_period)),
            FakeSentence((second, second_period)),
        ),
    )

    with pytest.raises(tool.AdapterError, match="crosses sentence"):
        tool.adapt_doc("fixture-cross-head", None, doc.text, doc)


def test_adapt_doc_rejects_an_emitted_token_outside_all_sentences() -> None:
    tool = load_tool()
    root = FakeToken(0, "A", 0, "a", "NOUN", "N", "ROOT", FakeMorph())
    period = FakeToken(1, ".", 1, ".", "PUNCT", ".", "punct", FakeMorph())
    root.head = root
    period.head = root
    doc = FakeDoc("A.", (root, period), (FakeSentence((root,)),))

    with pytest.raises(tool.AdapterError, match="exactly one sentence"):
        tool.adapt_doc("fixture-unpartitioned", None, doc.text, doc)


def test_adapt_doc_requires_exactly_one_dependency_root_per_sentence() -> None:
    tool = load_tool()
    first = FakeToken(0, "A", 0, "a", "NOUN", "N", "ROOT", FakeMorph())
    second = FakeToken(1, "B", 2, "b", "NOUN", "N", "ROOT", FakeMorph())
    first.head = first
    second.head = second
    doc = FakeDoc("A B", (first, second), (FakeSentence((first, second)),))

    with pytest.raises(tool.AdapterError, match="exactly one dependency root"):
        tool.adapt_doc("fixture-two-roots", None, doc.text, doc)


def test_adapt_doc_rejects_an_empty_analysis_without_contractual_abstention() -> None:
    tool = load_tool()
    doc = FakeDoc("", (), ())

    with pytest.raises(tool.AdapterError, match="no surface tokens"):
        tool.adapt_doc("fixture-empty", None, "", doc)


def test_analyze_records_preserves_contractual_abstention_without_calling_spacy() -> None:
    tool = load_tool()
    root = FakeToken(0, "A", 0, "a", "NOUN", "N", "ROOT", FakeMorph())
    root.head = root
    calls: list[str] = []

    def pipeline(text: str) -> FakeDoc:
        calls.append(text)
        return FakeDoc(text, (root,), (FakeSentence((root,)),))

    records = tool.analyze_records(
        [
            {
                "schema_version": "hermes-pt4-inference-input/v1",
                "case_id": "analyzed",
                "document_id": "doc-1",
                "text": "A",
                "abstention_reason": None,
            },
            {
                "schema_version": "hermes-pt4-inference-input/v1",
                "case_id": "abstained",
                "document_id": None,
                "text": "`código` e texto",
                "abstention_reason": "partial-structural-markup",
            },
        ],
        pipeline,
    )

    assert calls == ["A"]
    assert records[0]["surface_tokens"] == [{"text": "A", "start": 0, "end": 1}]
    assert records[1] == {
        "schema_version": "hermes-pt4-linguistic-analysis/v1",
        "case_id": "abstained",
        "document_id": None,
        "text": "`código` e texto",
        "surface_tokens": [],
        "words": [],
        "sentences": [],
        "abstention_reason": "partial-structural-markup",
    }


def test_prepare_inputs_removes_all_gold_linguistic_annotations() -> None:
    tool = load_tool()
    inputs = tool.prepare_inputs(
        [
            {
                "schema_version": "hermes-pt4-linguistic-analysis/v1",
                "case_id": "fixture-1",
                "document_id": "doc-1",
                "text": "A.",
                "surface_tokens": [{"text": "A", "start": 0, "end": 1}],
                "words": [{"lemma": "a"}],
                "sentences": [{"start": 0, "end": 2}],
                "abstention_reason": None,
            }
        ]
    )

    assert inputs == [
        {
            "schema_version": "hermes-pt4-inference-input/v1",
            "case_id": "fixture-1",
            "document_id": "doc-1",
            "text": "A.",
            "abstention_reason": None,
        }
    ]


def test_analyze_records_rejects_input_that_contains_gold_fields() -> None:
    tool = load_tool()
    record = {
        "schema_version": "hermes-pt4-inference-input/v1",
        "case_id": "leaky",
        "document_id": None,
        "text": "A.",
        "abstention_reason": "structural-markup",
        "words": [{"lemma": "a"}],
    }

    with pytest.raises(tool.AdapterError, match="fields do not match"):
        tool.analyze_records([record], lambda text: None)


def test_prepare_input_cli_writes_canonical_model_blind_jsonl(tmp_path: Path) -> None:
    source = tmp_path / "gold.jsonl"
    output = tmp_path / "input.jsonl"
    source.write_text(
        json.dumps(
            {
                "schema_version": "hermes-pt4-linguistic-analysis/v1",
                "case_id": "fixture-1",
                "document_id": None,
                "text": "A.",
                "surface_tokens": [{"text": "A", "start": 0, "end": 1}],
                "words": [],
                "sentences": [],
                "abstention_reason": "structural-markup",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [sys.executable, str(TOOL_PATH), "prepare-input", str(source), str(output)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert output.read_bytes() == (
        b'{"abstention_reason":"structural-markup","case_id":"fixture-1",'
        b'"document_id":null,"schema_version":"hermes-pt4-inference-input/v1",'
        b'"text":"A."}\n'
    )


def test_prepare_input_cli_fails_closed_on_invalid_utf8(tmp_path: Path) -> None:
    source = tmp_path / "invalid.jsonl"
    output = tmp_path / "input.jsonl"
    source.write_bytes(b"\xff\n")

    completed = subprocess.run(
        [sys.executable, str(TOOL_PATH), "prepare-input", str(source), str(output)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert completed.stderr.startswith("error: ")
    assert "Traceback" not in completed.stderr
    assert not output.exists()


def test_run_offline_blocks_dns_during_model_inference() -> None:
    tool = load_tool()
    record = {
        "schema_version": "hermes-pt4-inference-input/v1",
        "case_id": "network-attempt",
        "document_id": None,
        "text": "A.",
        "abstention_reason": None,
    }

    def load_pipeline():  # type: ignore[no-untyped-def]
        def pipeline(text: str):  # type: ignore[no-untyped-def]
            socket.getaddrinfo("example.invalid", 443)
            raise AssertionError(text)

        return pipeline

    with pytest.raises(tool.AdapterError, match="network access denied"):
        tool.run_offline([record], load_pipeline)


def test_load_validated_pipeline_uses_only_the_frozen_spacy_configuration() -> None:
    tool = load_tool()
    calls: list[tuple[str, tuple[str, ...]]] = []

    class Pipeline:
        pipe_names = ["tok2vec", "morphologizer", "parser", "lemmatizer", "attribute_ruler"]

    class SpacyModule:
        __version__ = "3.8.15"

        @staticmethod
        def load(model: str, *, exclude: list[str]) -> Pipeline:
            calls.append((model, tuple(exclude)))
            return Pipeline()

    pipeline = tool.load_validated_pipeline(SpacyModule(), "3.8.0")

    assert isinstance(pipeline, Pipeline)
    assert calls == [("pt_core_news_sm", ("ner",))]


def test_analyze_cli_runs_the_injected_pipeline_and_writes_candidate_jsonl(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tool = load_tool()
    source = tmp_path / "input.jsonl"
    output = tmp_path / "candidate.jsonl"
    source.write_text(
        json.dumps(
            {
                "schema_version": "hermes-pt4-inference-input/v1",
                "case_id": "fixture-1",
                "document_id": None,
                "text": "A",
                "abstention_reason": None,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    root = FakeToken(0, "A", 0, "a", "NOUN", "N", "ROOT", FakeMorph())
    root.head = root

    def pipeline(text: str) -> FakeDoc:
        return FakeDoc(text, (root,), (FakeSentence((root,)),))

    monkeypatch.setattr(tool, "load_installed_pipeline", lambda: pipeline, raising=False)
    monkeypatch.setattr(sys, "argv", [str(TOOL_PATH), "analyze", str(source), str(output)])

    assert tool.main() == 0
    candidate = json.loads(output.read_text(encoding="utf-8"))
    assert candidate["schema_version"] == "hermes-pt4-linguistic-analysis/v1"
    assert candidate["surface_tokens"] == [{"text": "A", "start": 0, "end": 1}]
