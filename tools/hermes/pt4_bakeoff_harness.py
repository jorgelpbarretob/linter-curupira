#!/usr/bin/env python3
"""Project and score PT4 linguistic bake-off artifacts without running a backend."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "hermes-pt4-linguistic-analysis/v1"


class HarnessError(RuntimeError):
    """Raised when a gold or candidate artifact violates the PT4 contract."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_jsonl(records: list[dict[str, Any]]) -> bytes:
    """Serialize records as deterministic UTF-8 JSONL."""
    return b"".join(
        (
            json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode()
        for record in records
    )


def canonical_json(value: dict[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()


def read_analysis_jsonl(payload: str) -> list[dict[str, Any]]:
    try:
        records = [json.loads(line) for line in payload.splitlines() if line]
    except json.JSONDecodeError as error:
        raise HarnessError("analysis artifact is not valid JSONL") from error
    if any(not isinstance(record, dict) for record in records):
        raise HarnessError("analysis JSONL records must be objects")
    return records


@dataclass(frozen=True, slots=True)
class ConlluRow:
    identifier: str
    form: str
    lemma: str
    upos: str
    xpos: str
    features: str
    head: str
    dependency: str
    misc: str


def _rows(lines: list[str]) -> list[ConlluRow]:
    rows: list[ConlluRow] = []
    for line in lines:
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != 10:
            raise HarnessError("CoNLL-U row must contain exactly ten fields")
        if not fields[1]:
            raise HarnessError("CoNLL-U FORM must not be empty")
        rows.append(
            ConlluRow(
                identifier=fields[0],
                form=fields[1],
                lemma=fields[2],
                upos=fields[3],
                xpos=fields[4],
                features=fields[5],
                head=fields[6],
                dependency=fields[7],
                misc=fields[9],
            )
        )
    return rows


def _comment(lines: list[str], prefix: str) -> str | None:
    values = [line.removeprefix(prefix) for line in lines if line.startswith(prefix)]
    if len(values) > 1:
        raise HarnessError(f"duplicate CoNLL-U comment: {prefix.strip()}")
    return values[0] if values else None


def _space_after_no(misc: str) -> bool:
    return "SpaceAfter=No" in misc.split("|")


def _features(value: str) -> list[list[str]]:
    if value == "_":
        return []
    parsed: list[list[str]] = []
    for item in value.split("|"):
        if "=" not in item:
            raise HarnessError(f"invalid FEATS item: {item}")
        name, feature_value = item.split("=", maxsplit=1)
        if not name or not feature_value:
            raise HarnessError(f"invalid FEATS item: {item}")
        parsed.append([name, feature_value])
    return sorted(parsed)


def _project_sentence(lines: list[str], document_id: str | None) -> dict[str, Any]:
    text = _comment(lines, "# text = ")
    case_id = _comment(lines, "# sent_id = ")
    if text is None or case_id is None:
        raise HarnessError("each sentence requires text and sent_id comments")
    rows = _rows(lines)
    for row in rows:
        if re.fullmatch(r"[1-9]\d*", row.identifier) or re.fullmatch(
            r"[1-9]\d*-[1-9]\d*", row.identifier
        ):
            continue
        if re.fullmatch(r"[1-9]\d*\.[1-9]\d*", row.identifier):
            raise HarnessError(f"{case_id} contains unsupported empty nodes")
        raise HarnessError(f"{case_id} has an invalid CoNLL-U ID: {row.identifier}")
    integer_rows = [row for row in rows if re.fullmatch(r"[1-9]\d*", row.identifier)]
    if not integer_rows:
        raise HarnessError(f"{case_id} has no syntactic words")

    mwt_by_word: dict[int, ConlluRow] = {}
    for row in rows:
        if "-" not in row.identifier:
            continue
        first_text, last_text = row.identifier.split("-", maxsplit=1)
        first, last = int(first_text), int(last_text)
        if first >= last:
            raise HarnessError(f"{case_id} has an invalid multiword-token range")
        for word_id in range(first, last + 1):
            if word_id in mwt_by_word:
                raise HarnessError(f"{case_id} has overlapping multiword tokens")
            mwt_by_word[word_id] = row

    words_by_id = {int(row.identifier): row for row in integer_rows}
    if set(words_by_id) != set(range(1, len(integer_rows) + 1)):
        raise HarnessError(f"{case_id} word IDs are not contiguous from one")
    for word_id in mwt_by_word:
        if word_id not in words_by_id:
            raise HarnessError(f"{case_id} multiword token covers a missing word")
    roots = [row for row in integer_rows if row.head == "0"]
    if len(roots) != 1 or roots[0].dependency != "root":
        raise HarnessError(f"{case_id} must have exactly one dependency root")
    if any(row.head != "0" and row.dependency == "root" for row in integer_rows):
        raise HarnessError(f"{case_id} has a non-root word labeled as root")

    surface_specs: list[tuple[ConlluRow, tuple[int, ...], bool]] = []
    seen_mwt: set[str] = set()
    for row in rows:
        if "-" in row.identifier:
            if row.identifier in seen_mwt:
                raise HarnessError(f"{case_id} repeats a multiword token")
            seen_mwt.add(row.identifier)
            covered = tuple(
                word_id
                for word_id, mwt in sorted(mwt_by_word.items())
                if mwt.identifier == row.identifier
            )
            surface_specs.append((row, covered, _space_after_no(row.misc)))
        elif re.fullmatch(r"[1-9]\d*", row.identifier) and int(row.identifier) not in mwt_by_word:
            surface_specs.append((row, (int(row.identifier),), _space_after_no(row.misc)))

    surface_tokens: list[dict[str, Any]] = []
    surface_by_word: dict[int, int] = {}
    cursor = 0
    previous_no_space = False
    for row, covered, no_space in surface_specs:
        start = text.find(row.form, cursor)
        if start < 0:
            raise HarnessError(f"{case_id} cannot align surface form {row.form!r}")
        gap = text[cursor:start]
        if (gap and not gap.isspace()) or (previous_no_space and gap):
            raise HarnessError(f"{case_id} has invalid text between surface tokens")
        end = start + len(row.form)
        surface_index = len(surface_tokens)
        surface_tokens.append({"text": row.form, "start": start, "end": end})
        for word_id in covered:
            surface_by_word[word_id] = surface_index
        cursor = end
        previous_no_space = no_space
    if text[cursor:] and not text[cursor:].isspace():
        raise HarnessError(f"{case_id} has unaligned trailing text")

    words: list[dict[str, Any]] = []
    for word_id, row in sorted(words_by_id.items()):
        try:
            head = int(row.head)
        except ValueError as error:
            raise HarnessError(f"{case_id} word {word_id} has invalid HEAD") from error
        if head and head not in words_by_id:
            raise HarnessError(f"{case_id} word {word_id} has a head outside its sentence")
        words.append(
            {
                "form": row.form,
                "surface_token_index": surface_by_word[word_id],
                "lemma": row.lemma,
                "upos": row.upos,
                "xpos": None if row.xpos == "_" else row.xpos,
                "features": _features(row.features),
                "dependency": row.dependency,
                "head_word_index": None if head == 0 else head - 1,
                "sentence_index": 0,
            }
        )

    first = surface_tokens[0]
    last = surface_tokens[-1]
    return {
        "schema_version": SCHEMA_VERSION,
        "case_id": case_id,
        "document_id": document_id,
        "text": text,
        "surface_tokens": surface_tokens,
        "words": words,
        "sentences": [
            {
                "start": first["start"],
                "end": last["end"],
                "first_surface_token": 0,
                "past_last_surface_token": len(surface_tokens),
                "first_word": 0,
                "past_last_word": len(words),
            }
        ],
        "abstention_reason": None,
    }


def project_conllu(conllu: str) -> list[dict[str, Any]]:
    """Project CoNLL-U sentences to the frozen surface/word offset contract."""
    blocks = [block.splitlines() for block in conllu.split("\n\n") if block.strip()]
    records: list[dict[str, Any]] = []
    document_id: str | None = None
    for lines in blocks:
        declared_document = _comment(lines, "# newdoc id = ")
        if declared_document is not None:
            document_id = declared_document
        records.append(_project_sentence(lines, document_id))
    if len({record["case_id"] for record in records}) != len(records):
        raise HarnessError("CoNLL-U contains duplicate sent_id values")
    return records


def project_offset_jsonl(jsonl: str) -> list[dict[str, Any]]:
    """Project the frozen authorial offset corpus to the common harness schema."""
    try:
        source_records = [json.loads(line) for line in jsonl.splitlines() if line]
    except json.JSONDecodeError as error:
        raise HarnessError("offset corpus is not valid JSONL") from error
    records: list[dict[str, Any]] = []
    for source in source_records:
        case_id = source.get("case_id")
        if source.get("schema_version") != "hermes-pt4-offset-corpus/v2":
            raise HarnessError(f"{case_id} offset schema version mismatch")
        if source.get("review_status") != "model-panel-approved":
            raise HarnessError(f"{case_id} offset case is not panel-approved")
        surface_tokens = [
            {"text": token["text"], "start": token["start"], "end": token["end"]}
            for token in source["surface_tokens"]
        ]
        sentence_by_surface: dict[int, int] = {}
        expected_surface = 0
        for sentence_index, sentence in enumerate(source["sentences"]):
            first_surface = sentence["first_surface_token"]
            past_last_surface = sentence["past_last_surface_token"]
            if first_surface != expected_surface or not first_surface < past_last_surface <= len(
                surface_tokens
            ):
                raise HarnessError(f"{case_id} sentence token range is not contiguous")
            first_token = surface_tokens[first_surface]
            last_token = surface_tokens[past_last_surface - 1]
            if sentence["start"] != first_token["start"] or sentence["end"] != last_token["end"]:
                raise HarnessError(f"{case_id} sentence envelope is not minimal")
            for surface_index in range(first_surface, past_last_surface):
                sentence_by_surface[surface_index] = sentence_index
            expected_surface = past_last_surface
        if expected_surface != len(surface_tokens):
            raise HarnessError(f"{case_id} sentence token range is not contiguous")
        words: list[dict[str, Any]] = []
        for word in source["syntactic_words"]:
            surface_index = word["surface_token_index"]
            if surface_index not in sentence_by_surface:
                raise HarnessError(f"{case_id} offset word is outside every sentence")
            words.append(
                {
                    "form": word["form"],
                    "surface_token_index": surface_index,
                    "lemma": None,
                    "upos": None,
                    "xpos": None,
                    "features": None,
                    "dependency": None,
                    "head_word_index": None,
                    "sentence_index": sentence_by_surface[surface_index],
                }
            )
        sentences: list[dict[str, Any]] = []
        for sentence_index, source_sentence in enumerate(source["sentences"]):
            sentence_word_indices = [
                index
                for index, word in enumerate(words)
                if word["sentence_index"] == sentence_index
            ]
            if not sentence_word_indices:
                raise HarnessError(f"{case_id} offset sentence has no syntactic words")
            first_word = sentence_word_indices[0]
            past_last_word = sentence_word_indices[-1] + 1
            if sentence_word_indices != list(range(first_word, past_last_word)):
                raise HarnessError(f"{case_id} sentence word range is not contiguous")
            sentences.append(
                {
                    "start": source_sentence["start"],
                    "end": source_sentence["end"],
                    "first_surface_token": source_sentence["first_surface_token"],
                    "past_last_surface_token": source_sentence["past_last_surface_token"],
                    "first_word": first_word,
                    "past_last_word": past_last_word,
                }
            )
        abstention_reason = None
        if source["abstention_spans"]:
            abstention_reason = (
                "structural-markup"
                if not source["analysis_segments"]
                else "partial-structural-markup"
            )
        record = {
            "schema_version": SCHEMA_VERSION,
            "case_id": case_id,
            "document_id": "pt4-offset-development-v1",
            "text": source["text"],
            "surface_tokens": surface_tokens,
            "words": words,
            "sentences": sentences,
            "abstention_reason": abstention_reason,
        }
        if _candidate_offset_errors(record):
            raise HarnessError(f"{case_id} has invalid token or sentence offsets")
        records.append(record)
    if len({record["case_id"] for record in records}) != len(records):
        raise HarnessError("offset corpus contains duplicate case IDs")
    return records


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _optional_ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _f1(precision: float, recall: float) -> float:
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def _token_key(token: dict[str, Any]) -> tuple[int, int, str]:
    return token["start"], token["end"], token["text"]


def _sentence_key(sentence: dict[str, Any]) -> tuple[int, int]:
    return sentence["start"], sentence["end"]


def _validate_candidate_shape(record: dict[str, Any]) -> None:
    record_fields = {
        "schema_version",
        "case_id",
        "document_id",
        "text",
        "surface_tokens",
        "words",
        "sentences",
        "abstention_reason",
    }
    if set(record) != record_fields:
        raise HarnessError(f"{record.get('case_id')} candidate fields do not match v1")
    case_id = record["case_id"]
    if not isinstance(case_id, str) or not isinstance(record["text"], str):
        raise HarnessError(f"{case_id} candidate scalar fields do not match v1")
    if any(
        not isinstance(record[field], list) for field in ("surface_tokens", "words", "sentences")
    ):
        raise HarnessError(f"{case_id} candidate collections do not match v1")
    token_fields = {"text", "start", "end"}
    if any(
        not isinstance(token, dict)
        or set(token) != token_fields
        or not isinstance(token["text"], str)
        or not isinstance(token["start"], int)
        or isinstance(token["start"], bool)
        or not isinstance(token["end"], int)
        or isinstance(token["end"], bool)
        for token in record["surface_tokens"]
    ):
        raise HarnessError(f"{case_id} candidate token fields do not match v1")
    word_fields = {
        "form",
        "surface_token_index",
        "lemma",
        "upos",
        "xpos",
        "features",
        "dependency",
        "head_word_index",
        "sentence_index",
    }
    optional_strings = ("lemma", "upos", "xpos", "dependency")
    if any(
        not isinstance(word, dict)
        or set(word) != word_fields
        or not isinstance(word["form"], str)
        or not isinstance(word["surface_token_index"], int)
        or isinstance(word["surface_token_index"], bool)
        or not isinstance(word["sentence_index"], int)
        or isinstance(word["sentence_index"], bool)
        or (
            word["head_word_index"] is not None
            and (
                not isinstance(word["head_word_index"], int)
                or isinstance(word["head_word_index"], bool)
            )
        )
        or any(
            word[field] is not None and not isinstance(word[field], str)
            for field in optional_strings
        )
        for word in record["words"]
    ):
        raise HarnessError(f"{case_id} candidate word fields do not match v1")
    for word in record["words"]:
        features = word["features"]
        if features is None:
            continue
        if not isinstance(features, list) or any(
            not isinstance(feature, list)
            or len(feature) != 2
            or any(not isinstance(item, str) for item in feature)
            for feature in features
        ):
            raise HarnessError(f"{case_id} candidate feature fields do not match v1")
    sentence_fields = {
        "start",
        "end",
        "first_surface_token",
        "past_last_surface_token",
        "first_word",
        "past_last_word",
    }
    if any(
        not isinstance(sentence, dict)
        or set(sentence) != sentence_fields
        or any(
            not isinstance(sentence[field], int) or isinstance(sentence[field], bool)
            for field in sentence_fields
        )
        for sentence in record["sentences"]
    ):
        raise HarnessError(f"{case_id} candidate sentence fields do not match v1")
    abstention_reason = record["abstention_reason"]
    if abstention_reason is not None and not isinstance(abstention_reason, str):
        raise HarnessError(f"{case_id} candidate abstention reason is invalid")


def _candidate_offset_errors(record: dict[str, Any]) -> int:
    text = record["text"]
    tokens = record["surface_tokens"]
    errors = 0
    previous_end = -1
    for token in tokens:
        start, end = token.get("start"), token.get("end")
        if not isinstance(start, int) or not isinstance(end, int):
            errors += 1
            continue
        if not 0 <= start < end <= len(text) or text[start:end] != token.get("text"):
            errors += 1
        if start < previous_end:
            errors += 1
        previous_end = max(previous_end, end)
    words = record["words"]
    expected_surface = 0
    expected_word = 0
    for sentence_index, sentence in enumerate(record["sentences"]):
        first = sentence.get("first_surface_token")
        past_last = sentence.get("past_last_surface_token")
        if not isinstance(first, int) or not isinstance(past_last, int):
            errors += 1
            continue
        if not 0 <= first < past_last <= len(tokens):
            errors += 1
            continue
        if first != expected_surface:
            errors += 1
        expected_surface = past_last
        if sentence.get("start") != tokens[first].get("start") or sentence.get("end") != tokens[
            past_last - 1
        ].get("end"):
            errors += 1
        first_word = sentence.get("first_word")
        past_last_word = sentence.get("past_last_word")
        if (
            not isinstance(first_word, int)
            or not isinstance(past_last_word, int)
            or not 0 <= first_word < past_last_word <= len(words)
        ):
            errors += 1
            continue
        if first_word != expected_word:
            errors += 1
        expected_word = past_last_word
        for word_index in range(first_word, past_last_word):
            word = words[word_index]
            if word.get("sentence_index") != sentence_index:
                errors += 1
            surface_index = word.get("surface_token_index")
            if not isinstance(surface_index, int) or not first <= surface_index < past_last:
                errors += 1
            head = word.get("head_word_index")
            if head is not None and (
                not isinstance(head, int) or not first_word <= head < past_last_word
            ):
                errors += 1
    if expected_surface != len(tokens):
        errors += 1
    if expected_word != len(words):
        errors += 1
    for word in words:
        surface = word.get("surface_token_index")
        head = word.get("head_word_index")
        sentence = word.get("sentence_index")
        if not isinstance(surface, int) or not 0 <= surface < len(tokens):
            errors += 1
        if head is not None and (not isinstance(head, int) or not 0 <= head < len(words)):
            errors += 1
        if not isinstance(sentence, int) or not 0 <= sentence < len(record["sentences"]):
            errors += 1
    return errors


def score_corpora(
    gold_records: list[dict[str, Any]], candidate_records: list[dict[str, Any]]
) -> dict[str, Any]:
    """Score candidate records by exact surface spans and aligned syntactic words."""
    gold_ids = [record["case_id"] for record in gold_records]
    candidate_ids = [record.get("case_id") for record in candidate_records]
    if candidate_ids != gold_ids:
        raise HarnessError("candidate case IDs must match gold in canonical order")

    gold_token_count = 0
    candidate_token_count = 0
    matched_token_count = 0
    gold_sentence_count = 0
    candidate_sentence_count = 0
    matched_sentence_count = 0
    aligned_word_count = 0
    unaligned_gold_words = 0
    unaligned_candidate_words = 0
    lemma_correct = 0
    lemma_count = 0
    upos_correct = 0
    upos_count = 0
    uas_correct = 0
    uas_count = 0
    las_correct = 0
    las_count = 0
    feature_word_count = 0
    feature_true_positive = 0
    feature_false_positive = 0
    feature_false_negative = 0
    offset_errors = 0
    candidate_abstentions: dict[str, int] = {}

    for gold, candidate in zip(gold_records, candidate_records, strict=True):
        _validate_candidate_shape(candidate)
        if candidate.get("schema_version") != SCHEMA_VERSION:
            raise HarnessError(f"{gold['case_id']} candidate schema version mismatch")
        if candidate.get("text") != gold["text"]:
            raise HarnessError(f"{gold['case_id']} candidate text differs from gold")
        offset_errors += _candidate_offset_errors(candidate)
        abstention_reason = candidate["abstention_reason"]
        if abstention_reason is not None:
            candidate_abstentions[abstention_reason] = (
                candidate_abstentions.get(abstention_reason, 0) + 1
            )

        gold_tokens = gold["surface_tokens"]
        candidate_tokens = candidate["surface_tokens"]
        gold_token_count += len(gold_tokens)
        candidate_token_count += len(candidate_tokens)
        gold_by_key = {_token_key(token): index for index, token in enumerate(gold_tokens)}
        candidate_by_key = {
            _token_key(token): index for index, token in enumerate(candidate_tokens)
        }
        matched_keys = gold_by_key.keys() & candidate_by_key.keys()
        matched_token_count += len(matched_keys)

        gold_sentences = gold["sentences"]
        candidate_sentences = candidate["sentences"]
        gold_sentence_count += len(gold_sentences)
        candidate_sentence_count += len(candidate_sentences)
        matched_sentence_count += len(
            {_sentence_key(sentence) for sentence in gold_sentences}
            & {_sentence_key(sentence) for sentence in candidate_sentences}
        )

        gold_words_by_surface: dict[int, list[tuple[int, dict[str, Any]]]] = {}
        candidate_words_by_surface: dict[int, list[tuple[int, dict[str, Any]]]] = {}
        for index, word in enumerate(gold["words"]):
            gold_words_by_surface.setdefault(word["surface_token_index"], []).append((index, word))
        for index, word in enumerate(candidate["words"]):
            candidate_words_by_surface.setdefault(word["surface_token_index"], []).append(
                (index, word)
            )

        aligned: list[tuple[int, dict[str, Any], int, dict[str, Any]]] = []
        for key in matched_keys:
            gold_surface = gold_by_key[key]
            candidate_surface = candidate_by_key[key]
            gold_surface_words = gold_words_by_surface.get(gold_surface, [])
            candidate_surface_words = candidate_words_by_surface.get(candidate_surface, [])
            paired_count = min(len(gold_surface_words), len(candidate_surface_words))
            for (gold_index, gold_word), (candidate_index, candidate_word) in zip(
                gold_surface_words[:paired_count],
                candidate_surface_words[:paired_count],
                strict=True,
            ):
                aligned.append((gold_index, gold_word, candidate_index, candidate_word))
        aligned.sort(key=lambda item: item[0])
        aligned_gold_indices = {item[0] for item in aligned}
        aligned_candidate_indices = {item[2] for item in aligned}
        missing_gold = [
            word for index, word in enumerate(gold["words"]) if index not in aligned_gold_indices
        ]
        extra_candidate = [
            word
            for index, word in enumerate(candidate["words"])
            if index not in aligned_candidate_indices
        ]
        unaligned_gold_words += len(missing_gold)
        unaligned_candidate_words += len(extra_candidate)
        for gold_word in missing_gold:
            if gold_word["lemma"] is not None:
                lemma_count += 1
            if gold_word["upos"] is not None:
                upos_count += 1
            if gold_word["features"] is not None:
                feature_word_count += 1
                feature_false_negative += len(gold_word["features"])
            if gold_word["dependency"] is not None:
                uas_count += 1
                las_count += 1
        lemma_applicable = any(word["lemma"] is not None for word in gold["words"])
        upos_applicable = any(word["upos"] is not None for word in gold["words"])
        features_applicable = any(word["features"] is not None for word in gold["words"])
        dependencies_applicable = any(word["dependency"] is not None for word in gold["words"])
        for candidate_word in extra_candidate:
            if lemma_applicable:
                lemma_count += 1
            if upos_applicable:
                upos_count += 1
            if features_applicable:
                feature_word_count += 1
                feature_false_positive += len(candidate_word["features"] or [])
            if dependencies_applicable:
                uas_count += 1
                las_count += 1
        gold_to_candidate = {
            gold_index: candidate_index for gold_index, _, candidate_index, _ in aligned
        }

        for gold_index, gold_word, candidate_index, candidate_word in aligned:
            del gold_index, candidate_index
            aligned_word_count += 1
            if gold_word["lemma"] is not None:
                lemma_count += 1
                lemma_correct += candidate_word["lemma"] == gold_word["lemma"]
            if gold_word["upos"] is not None:
                upos_count += 1
                upos_correct += candidate_word["upos"] == gold_word["upos"]
            if gold_word["features"] is not None:
                feature_word_count += 1
                gold_features = {tuple(feature) for feature in gold_word["features"]}
                candidate_features = {
                    tuple(feature) for feature in (candidate_word["features"] or [])
                }
                feature_true_positive += len(gold_features & candidate_features)
                feature_false_positive += len(candidate_features - gold_features)
                feature_false_negative += len(gold_features - candidate_features)
            gold_head = gold_word["head_word_index"]
            candidate_head = candidate_word["head_word_index"]
            if gold_word["dependency"] is not None:
                uas_count += 1
                las_count += 1
                head_correct = (gold_head is None and candidate_head is None) or (
                    gold_head is not None
                    and gold_head in gold_to_candidate
                    and gold_to_candidate[gold_head] == candidate_head
                )
                uas_correct += head_correct
                las_correct += (
                    head_correct and candidate_word["dependency"] == gold_word["dependency"]
                )

    token_precision = _ratio(matched_token_count, candidate_token_count)
    token_recall = _ratio(matched_token_count, gold_token_count)
    sentence_precision = _ratio(matched_sentence_count, candidate_sentence_count)
    sentence_recall = _ratio(matched_sentence_count, gold_sentence_count)
    feature_denominator = (
        2 * feature_true_positive + feature_false_positive + feature_false_negative
    )
    feats_f1 = (
        _ratio(2 * feature_true_positive, feature_denominator)
        if feature_denominator
        else (1.0 if feature_word_count else None)
    )
    return {
        "schema_version": "hermes-pt4-bakeoff-metrics/v1",
        "case_count": len(gold_records),
        "gold_surface_tokens": gold_token_count,
        "candidate_surface_tokens": candidate_token_count,
        "aligned_words": aligned_word_count,
        "unaligned_gold_words": unaligned_gold_words,
        "unaligned_candidate_words": unaligned_candidate_words,
        "offset_errors": offset_errors,
        "candidate_abstentions": {
            "case_count": sum(candidate_abstentions.values()),
            "by_reason": dict(sorted(candidate_abstentions.items())),
        },
        "metrics": {
            "token_precision": token_precision,
            "token_recall": token_recall,
            "token_f1": _f1(token_precision, token_recall),
            "sentence_precision": sentence_precision,
            "sentence_recall": sentence_recall,
            "sentence_f1": _f1(sentence_precision, sentence_recall),
            "lemma_accuracy": _optional_ratio(lemma_correct, lemma_count),
            "upos_accuracy": _optional_ratio(upos_correct, upos_count),
            "feats_micro_f1": feats_f1,
            "uas": _optional_ratio(uas_correct, uas_count),
            "las": _optional_ratio(las_correct, las_count),
        },
    }


def _at_least(value: object, floor: float) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and value >= floor


def evaluate_quality_gates(petrogold: dict[str, Any], offsets: dict[str, Any]) -> dict[str, Any]:
    """Apply preregistered quality floors without authorizing inference or selection."""
    petro_metrics = petrogold["metrics"]
    offset_metrics = offsets["metrics"]
    checks = {
        "offset_errors": petrogold["offset_errors"] == 0 and offsets["offset_errors"] == 0,
        "token_f1": _at_least(petro_metrics["token_f1"], 0.99)
        and _at_least(offset_metrics["token_f1"], 0.99),
        "sentence_f1": _at_least(petro_metrics["sentence_f1"], 0.95)
        and _at_least(offset_metrics["sentence_f1"], 0.95),
        "upos_accuracy": _at_least(petro_metrics["upos_accuracy"], 0.92),
        "lemma_accuracy": _at_least(petro_metrics["lemma_accuracy"], 0.90),
        "feats_micro_f1": _at_least(petro_metrics["feats_micro_f1"], 0.85),
        "uas": _at_least(petro_metrics["uas"], 0.80),
        "las": _at_least(petro_metrics["las"], 0.75),
    }
    quality_passed = all(checks.values())
    return {
        "schema_version": "hermes-pt4-quality-gate/v1",
        "status": "quality-pass-operational-pending" if quality_passed else "quality-fail",
        "quality_passed": quality_passed,
        "checks": checks,
        "operational_gates_evaluated": False,
        "inference_authorized": False,
    }


def _write_new(path: Path, payload: bytes) -> None:
    if path.exists():
        raise HarnessError(f"output already exists: {path}")
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    project = subparsers.add_parser("project-conllu", help="project frozen CoNLL-U gold")
    project.add_argument("source", type=Path)
    project.add_argument("output", type=Path)
    offset = subparsers.add_parser("project-offset", help="project frozen offset gold")
    offset.add_argument("source", type=Path)
    offset.add_argument("output", type=Path)
    score = subparsers.add_parser("score", help="score a precomputed candidate artifact")
    score.add_argument("gold", type=Path)
    score.add_argument("candidate", type=Path)
    score.add_argument("output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "score":
            gold_records = read_analysis_jsonl(args.gold.read_text(encoding="utf-8"))
            candidate_records = read_analysis_jsonl(args.candidate.read_text(encoding="utf-8"))
            result = score_corpora(gold_records, candidate_records)
            payload = canonical_json(result)
            case_count = result["case_count"]
        else:
            source = args.source.read_text(encoding="utf-8")
            records = (
                project_conllu(source)
                if args.command == "project-conllu"
                else project_offset_jsonl(source)
            )
            payload = canonical_jsonl(records)
            case_count = len(records)
        _write_new(args.output, payload)
    except (HarnessError, OSError, UnicodeError) as error:
        print(f"pt4-bakeoff-harness: {error}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "case_count": case_count,
                "output": str(args.output),
                "sha256": sha256_bytes(payload),
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
