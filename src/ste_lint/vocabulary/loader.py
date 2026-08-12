"""Strict JSON vocabulary loading with traceable canonical hashes."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from typing import cast

from ste_lint.vocabulary.models import (
    VocabularyEntry,
    VocabularyProvenance,
    VocabularyResource,
)

MAX_RESOURCE_BYTES = 16 * 1024 * 1024
MAX_ENTRIES = 100_000
SOURCE_FORMAT = "ste-lint-vocabulary-source"
RESOURCE_FORMAT = "ste-lint-vocabulary"
SCHEMA_VERSION = 1
STANDARD = "ASD-STE100"
ISSUE = "9"


class VocabularyError(ValueError):
    """Raised when a vocabulary resource violates its public contract."""


def import_source(raw: bytes) -> VocabularyResource:
    root = _parse_json(raw)
    _require_keys(root, {"format", "schema_version", "standard", "issue", "entries"})
    _require_identity(root, expected_format=SOURCE_FORMAT)
    entries = _parse_entries(root["entries"])
    source_hash = hashlib.sha256(raw).hexdigest()
    return VocabularyResource(
        standard=STANDARD,
        issue=ISSUE,
        entries=entries,
        provenance=VocabularyProvenance(
            source_format=SOURCE_FORMAT,
            source_schema_version=SCHEMA_VERSION,
            source_sha256=source_hash,
            content_sha256=_content_sha256(entries),
        ),
    )


def parse_resource(raw: bytes) -> VocabularyResource:
    root = _parse_json(raw)
    _require_keys(
        root,
        {"format", "schema_version", "standard", "issue", "entries", "provenance"},
    )
    _require_identity(root, expected_format=RESOURCE_FORMAT)
    entries = _parse_entries(root["entries"])
    provenance = _parse_provenance(root["provenance"])
    expected_content_hash = _content_sha256(entries)
    if provenance.content_sha256 != expected_content_hash:
        raise VocabularyError("invalid provenance.content_sha256")
    return VocabularyResource(STANDARD, ISSUE, entries, provenance)


def serialize_resource(resource: VocabularyResource) -> bytes:
    root = {
        "format": RESOURCE_FORMAT,
        "schema_version": SCHEMA_VERSION,
        "standard": resource.standard,
        "issue": resource.issue,
        "entries": [_entry_object(entry) for entry in resource.entries],
        "provenance": {
            "source_format": resource.provenance.source_format,
            "source_schema_version": resource.provenance.source_schema_version,
            "source_sha256": resource.provenance.source_sha256,
            "content_sha256": resource.provenance.content_sha256,
        },
    }
    return json.dumps(
        root,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _parse_json(raw: bytes) -> dict[str, object]:
    if len(raw) > MAX_RESOURCE_BYTES:
        raise VocabularyError("vocabulary resource exceeds the 16 MiB limit")
    try:
        decoded = raw.decode("utf-8")
        value = json.loads(
            decoded,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise VocabularyError(f"invalid vocabulary JSON: {error}") from error
    if not isinstance(value, dict):
        raise VocabularyError("vocabulary root must be an object")
    return cast(dict[str, object], value)


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise VocabularyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> object:
    raise VocabularyError(f"invalid JSON constant: {value}")


def _require_keys(value: dict[str, object], expected: set[str]) -> None:
    unknown = set(value) - expected
    missing = expected - set(value)
    if unknown:
        raise VocabularyError(f"unknown vocabulary keys: {', '.join(sorted(unknown))}")
    if missing:
        raise VocabularyError(f"missing vocabulary keys: {', '.join(sorted(missing))}")


def _require_identity(root: dict[str, object], *, expected_format: str) -> None:
    if root["format"] != expected_format:
        raise VocabularyError(f"format must be {expected_format}")
    if type(root["schema_version"]) is not int or root["schema_version"] != SCHEMA_VERSION:
        raise VocabularyError("schema_version must be 1")
    if root["standard"] != STANDARD:
        raise VocabularyError(f"standard must be {STANDARD}")
    if root["issue"] != ISSUE:
        raise VocabularyError(f"issue must be the string {ISSUE}")


def _parse_entries(value: object) -> tuple[VocabularyEntry, ...]:
    if not isinstance(value, list):
        raise VocabularyError("entries must be an array")
    if len(value) > MAX_ENTRIES:
        raise VocabularyError("entries exceeds the 100000 item limit")
    entries: list[VocabularyEntry] = []
    collision_buckets: dict[tuple[str, str, str], list[VocabularyEntry]] = {}
    for item in value:
        entry = _parse_entry(item)
        key = (entry.part_of_speech, entry.meaning_id, entry.term.casefold())
        bucket = collision_buckets.setdefault(key, [])
        if any(
            existing.term == entry.term or not existing.case_sensitive or not entry.case_sensitive
            for existing in bucket
        ):
            raise VocabularyError("duplicate vocabulary entry after case normalization")
        bucket.append(entry)
        entries.append(entry)
    return tuple(entries)


def _parse_entry(value: object) -> VocabularyEntry:
    if not isinstance(value, dict):
        raise VocabularyError("each vocabulary entry must be an object")
    item = cast(dict[str, object], value)
    _require_keys(item, {"term", "part_of_speech", "meaning_id", "case_sensitive"})
    term = _validated_string(item["term"], "term", 256)
    part_of_speech = _validated_string(item["part_of_speech"], "part_of_speech", 128)
    meaning_id = _validated_string(item["meaning_id"], "meaning_id", 128)
    case_sensitive = item["case_sensitive"]
    if type(case_sensitive) is not bool:
        raise VocabularyError("case_sensitive must be a boolean")
    return VocabularyEntry(term, part_of_speech, meaning_id, case_sensitive)


def _validated_string(value: object, field: str, maximum: int) -> str:
    if not isinstance(value, str) or not value:
        raise VocabularyError(f"{field} must be a non-empty string")
    if value != value.strip():
        raise VocabularyError(f"{field} must not contain external whitespace")
    if len(value) > maximum:
        raise VocabularyError(f"{field} exceeds the {maximum} code point limit")
    if unicodedata.normalize("NFC", value) != value:
        raise VocabularyError(f"{field} must use Unicode NFC normalization")
    return value


def _parse_provenance(value: object) -> VocabularyProvenance:
    if not isinstance(value, dict):
        raise VocabularyError("provenance must be an object")
    item = cast(dict[str, object], value)
    _require_keys(
        item,
        {"source_format", "source_schema_version", "source_sha256", "content_sha256"},
    )
    if item["source_format"] != SOURCE_FORMAT:
        raise VocabularyError(f"provenance.source_format must be {SOURCE_FORMAT}")
    if type(item["source_schema_version"]) is not int or item["source_schema_version"] != 1:
        raise VocabularyError("provenance.source_schema_version must be 1")
    source_hash = _validated_sha256(item["source_sha256"], "source_sha256")
    content_hash = _validated_sha256(item["content_sha256"], "content_sha256")
    return VocabularyProvenance(SOURCE_FORMAT, 1, source_hash, content_hash)


def _validated_sha256(value: object, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise VocabularyError(f"provenance.{field} must be lowercase SHA-256")
    if any(character not in "0123456789abcdef" for character in value):
        raise VocabularyError(f"provenance.{field} must be lowercase SHA-256")
    return value


def _content_sha256(entries: tuple[VocabularyEntry, ...]) -> str:
    sorted_entries = sorted(
        entries,
        key=lambda entry: (
            entry.term,
            entry.part_of_speech,
            entry.meaning_id,
            entry.case_sensitive,
        ),
    )
    payload = {
        "standard": STANDARD,
        "issue": ISSUE,
        "entries": [_entry_object(entry) for entry in sorted_entries],
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _entry_object(entry: VocabularyEntry) -> dict[str, object]:
    return {
        "term": entry.term,
        "part_of_speech": entry.part_of_speech,
        "meaning_id": entry.meaning_id,
        "case_sensitive": entry.case_sensitive,
    }
