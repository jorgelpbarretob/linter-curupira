#!/usr/bin/env python3
"""Adapt spaCy documents to the frozen PT4 bake-off schema."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import socket
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import patch

SCHEMA_VERSION = "hermes-pt4-linguistic-analysis/v1"
INPUT_SCHEMA_VERSION = "hermes-pt4-inference-input/v1"
SPACY_VERSION = "3.8.15"
MODEL_NAME = "pt_core_news_sm"
MODEL_VERSION = "3.8.0"
PIPE_NAMES = ("tok2vec", "morphologizer", "parser", "lemmatizer", "attribute_ruler")


class AdapterError(RuntimeError):
    """Raised when spaCy output cannot satisfy the frozen PT4 contract."""


def _blocked_network(*args: Any, **kwargs: Any) -> Any:
    del args, kwargs
    raise AdapterError("network access denied during PT4 adapter execution")


@contextmanager
def deny_network() -> Any:
    """Fail closed on DNS or socket connection attempts and restore stdlib state."""
    with (
        patch.object(socket, "getaddrinfo", _blocked_network),
        patch.object(socket, "gethostbyname", _blocked_network),
        patch.object(socket, "gethostbyname_ex", _blocked_network),
        patch.object(socket, "gethostbyaddr", _blocked_network),
        patch.object(socket, "getnameinfo", _blocked_network),
        patch.object(socket, "create_connection", _blocked_network),
        patch.object(socket.socket, "connect", _blocked_network),
        patch.object(socket.socket, "connect_ex", _blocked_network),
        patch.object(socket, "socket", _blocked_network),
    ):
        yield


def read_jsonl(payload: str) -> list[dict[str, Any]]:
    try:
        lines = (raw_line.removesuffix("\r") for raw_line in payload.split("\n"))
        records = [json.loads(line) for line in lines if line]
    except json.JSONDecodeError as error:
        raise AdapterError("input is not valid JSONL") from error
    if any(not isinstance(record, dict) for record in records):
        raise AdapterError("JSONL records must be objects")
    return records


def canonical_jsonl(records: list[dict[str, Any]]) -> bytes:
    return b"".join(
        (
            json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            .replace("\u0085", "\\u0085")
            .replace("\u2028", "\\u2028")
            .replace("\u2029", "\\u2029")
            + "\n"
        ).encode()
        for record in records
    )


def _write_new(path: Path, payload: bytes) -> None:
    if path.exists():
        raise AdapterError(f"output already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent, prefix=f".{path.name}-", delete=False
        ) as temporary:
            temporary.write(payload)
            temporary.flush()
            temporary_path = Path(temporary.name)
        temporary_path.replace(path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def prepare_inputs(gold_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Project only model-blind fields from frozen gold records."""
    inputs: list[dict[str, Any]] = []
    for record in gold_records:
        required_fields = {
            "schema_version",
            "case_id",
            "document_id",
            "text",
            "abstention_reason",
        }
        if not required_fields.issubset(record):
            raise AdapterError(f"{record.get('case_id')} gold record is missing required fields")
        if record.get("schema_version") != SCHEMA_VERSION:
            raise AdapterError(f"{record.get('case_id')} gold schema mismatch")
        input_record = {
            "schema_version": INPUT_SCHEMA_VERSION,
            "case_id": record["case_id"],
            "document_id": record["document_id"],
            "text": record["text"],
            "abstention_reason": record["abstention_reason"],
        }
        _validate_input_record(input_record)
        inputs.append(input_record)
    return inputs


def _abstention_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "case_id": record["case_id"],
        "document_id": record["document_id"],
        "text": record["text"],
        "surface_tokens": [],
        "words": [],
        "sentences": [],
        "abstention_reason": record["abstention_reason"],
    }


def _validate_input_record(record: dict[str, Any]) -> None:
    fields = {"schema_version", "case_id", "document_id", "text", "abstention_reason"}
    if set(record) != fields:
        raise AdapterError(f"{record.get('case_id')} inference input fields do not match v1")
    if record["schema_version"] != INPUT_SCHEMA_VERSION:
        raise AdapterError(f"{record.get('case_id')} inference input schema mismatch")
    if not isinstance(record["case_id"], str) or not record["case_id"]:
        raise AdapterError("inference input case_id must be a non-empty string")
    if record["document_id"] is not None and not isinstance(record["document_id"], str):
        raise AdapterError(f"{record['case_id']} document_id is invalid")
    if not isinstance(record["text"], str):
        raise AdapterError(f"{record['case_id']} text is invalid")
    reason = record["abstention_reason"]
    if reason is not None and (not isinstance(reason, str) or not reason):
        raise AdapterError(f"{record['case_id']} abstention reason is invalid")


def analyze_records(records: list[dict[str, Any]], pipeline: Any) -> list[dict[str, Any]]:
    """Analyze minimal model-blind inputs, preserving contractual abstentions."""
    results: list[dict[str, Any]] = []
    for record in records:
        _validate_input_record(record)
        if record["abstention_reason"] is not None:
            results.append(_abstention_record(record))
            continue
        results.append(
            adapt_doc(
                record["case_id"],
                record["document_id"],
                record["text"],
                pipeline(record["text"]),
            )
        )
    return results


def run_offline(records: list[dict[str, Any]], load_pipeline: Any) -> list[dict[str, Any]]:
    """Load and run a candidate while DNS and socket connections are denied."""
    with deny_network():
        pipeline = load_pipeline()
        return analyze_records(records, pipeline)


def load_validated_pipeline(spacy_module: Any, model_version: str) -> Any:
    """Load exactly the Gate 0 candidate and reject configuration drift."""
    if spacy_module.__version__ != SPACY_VERSION:
        raise AdapterError(
            f"spaCy version mismatch: expected {SPACY_VERSION}, got {spacy_module.__version__}"
        )
    if model_version != MODEL_VERSION:
        raise AdapterError(f"model version mismatch: expected {MODEL_VERSION}, got {model_version}")
    pipeline = spacy_module.load(MODEL_NAME, exclude=["ner"])
    if tuple(pipeline.pipe_names) != PIPE_NAMES:
        raise AdapterError("spaCy pipeline components differ from the frozen configuration")
    return pipeline


def load_installed_pipeline() -> Any:
    """Import spaCy lazily and validate the installed Gate 0 candidate."""
    try:
        spacy_module = importlib.import_module("spacy")
        model_version = importlib.metadata.version(MODEL_NAME)
    except (ImportError, importlib.metadata.PackageNotFoundError) as error:
        raise AdapterError("frozen spaCy candidate is not installed") from error
    return load_validated_pipeline(spacy_module, model_version)


def adapt_doc(case_id: str, document_id: str | None, text: str, doc: Any) -> dict[str, Any]:
    """Project one already-analyzed spaCy document without leaking SDK objects."""
    if doc.text != text:
        raise AdapterError(f"{case_id} backend text differs from the exact input")
    tokens = [token for token in doc if not token.is_space]
    if not tokens:
        raise AdapterError(f"{case_id} backend produced no surface tokens")
    previous_end = 0
    for token in tokens:
        end = token.idx + len(token.text)
        if not 0 <= token.idx < end <= len(text) or text[token.idx : end] != token.text:
            raise AdapterError(f"{case_id} token does not have an exact surface slice")
        if token.idx < previous_end:
            raise AdapterError(f"{case_id} surface tokens overlap or are out of order")
        previous_end = end
    token_by_sdk_index = {token.i: index for index, token in enumerate(tokens)}
    sentence_by_sdk_index: dict[int, int] = {}
    sentence_membership: dict[int, int] = {}
    sentences: list[dict[str, int]] = []
    first_word = 0
    expected_surface = 0
    for sentence in doc.sents:
        sentence_tokens = [token for token in sentence if not token.is_space]
        if not sentence_tokens:
            continue
        sentence_index = len(sentences)
        first_surface = token_by_sdk_index[sentence_tokens[0].i]
        past_last_surface = token_by_sdk_index[sentence_tokens[-1].i] + 1
        if first_surface != expected_surface or past_last_surface - first_surface != len(
            sentence_tokens
        ):
            raise AdapterError(f"{case_id} sentence tokens are not a contiguous partition")
        for token in sentence_tokens:
            sentence_by_sdk_index[token.i] = sentence_index
            sentence_membership[token.i] = sentence_membership.get(token.i, 0) + 1
        sentences.append(
            {
                "start": sentence_tokens[0].idx,
                "end": sentence_tokens[-1].idx + len(sentence_tokens[-1].text),
                "first_surface_token": first_surface,
                "past_last_surface_token": past_last_surface,
                "first_word": first_word,
                "past_last_word": first_word + len(sentence_tokens),
            }
        )
        first_word += len(sentence_tokens)
        expected_surface = past_last_surface

    if expected_surface != len(tokens) or any(
        sentence_membership.get(token.i) != 1 for token in tokens
    ):
        raise AdapterError(f"{case_id} each emitted token must belong to exactly one sentence")
    for sentence_index in range(len(sentences)):
        roots = [
            token
            for token in tokens
            if sentence_by_sdk_index[token.i] == sentence_index and token.dep_ == "ROOT"
        ]
        if len(roots) != 1:
            raise AdapterError(f"{case_id} sentence must have exactly one dependency root")
        if roots[0].head.i != roots[0].i:
            raise AdapterError(f"{case_id} dependency root must be self-headed")

    surface_tokens = [
        {"text": token.text, "start": token.idx, "end": token.idx + len(token.text)}
        for token in tokens
    ]
    words = []
    for token in tokens:
        is_root = token.dep_ == "ROOT"
        if not is_root:
            if token.head.i == token.i:
                raise AdapterError(f"{case_id} non-root word must not be self-headed")
            if token.head.i not in token_by_sdk_index:
                raise AdapterError(f"{case_id} dependency head is not an emitted word")
            if sentence_by_sdk_index[token.head.i] != sentence_by_sdk_index[token.i]:
                raise AdapterError(f"{case_id} dependency head crosses sentence")
        words.append(
            {
                "form": token.text,
                "surface_token_index": token_by_sdk_index[token.i],
                "lemma": token.lemma_,
                "upos": token.pos_,
                "xpos": token.tag_ or None,
                "features": sorted([name, value] for name, value in token.morph.to_dict().items()),
                "dependency": "root" if is_root else token.dep_,
                "head_word_index": None if is_root else token_by_sdk_index[token.head.i],
                "sentence_index": sentence_by_sdk_index[token.i],
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "case_id": case_id,
        "document_id": document_id,
        "text": text,
        "surface_tokens": surface_tokens,
        "words": words,
        "sentences": sentences,
        "abstention_reason": None,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser(
        "prepare-input", help="remove gold annotations from a frozen projection"
    )
    prepare.add_argument("source", type=Path)
    prepare.add_argument("output", type=Path)
    analyze = subparsers.add_parser("analyze", help="run the frozen spaCy candidate offline")
    analyze.add_argument("source", type=Path)
    analyze.add_argument("output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        records = read_jsonl(args.source.read_text(encoding="utf-8"))
        if args.command == "prepare-input":
            _write_new(args.output, canonical_jsonl(prepare_inputs(records)))
        elif args.command == "analyze":
            _write_new(
                args.output,
                canonical_jsonl(run_offline(records, load_installed_pipeline)),
            )
        else:  # pragma: no cover - argparse enforces the command set
            raise AdapterError(f"unsupported command: {args.command}")
    except (AdapterError, OSError, UnicodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
