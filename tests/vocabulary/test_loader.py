import hashlib
import json

import pytest

import ste_lint.vocabulary.loader as loader_module
from ste_lint.vocabulary import (
    VocabularyError,
    import_source,
    parse_resource,
    serialize_resource,
)


def source_bytes(entries: list[dict[str, object]]) -> bytes:
    return json.dumps(
        {
            "format": "ste-lint-vocabulary-source",
            "schema_version": 1,
            "standard": "ASD-STE100",
            "issue": "9",
            "entries": entries,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode()


def entry(
    term: str,
    part_of_speech: str = "synthetic-noun",
    meaning_id: str = "synthetic-1",
    *,
    case_sensitive: bool = False,
) -> dict[str, object]:
    return {
        "term": term,
        "part_of_speech": part_of_speech,
        "meaning_id": meaning_id,
        "case_sensitive": case_sensitive,
    }


def test_import_builds_traceable_canonical_resource() -> None:
    raw = source_bytes([entry("flux valve"), entry("ZX-4", case_sensitive=True)])

    resource = import_source(raw)
    serialized = serialize_resource(resource)
    reparsed = parse_resource(serialized)

    assert reparsed == resource
    assert resource.standard == "ASD-STE100"
    assert resource.issue == "9"
    assert resource.provenance.source_format == "ste-lint-vocabulary-source"
    assert resource.provenance.source_schema_version == 1
    assert resource.provenance.source_sha256 == hashlib.sha256(raw).hexdigest()
    assert len(resource.provenance.content_sha256) == 64
    assert b"flux valve" in serialized


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        (b'{"format":"ste-lint-vocabulary-source","format":"duplicate"}', "duplicate"),
        (source_bytes([entry("e\u0301lan")]), "NFC"),
        (source_bytes([entry(" WiFi")]), "whitespace"),
        (source_bytes([entry("term")]).replace(b'"9"', b'"8"'), "issue"),
        (source_bytes([entry("term")]).replace(b'"entries"', b'"unknown"'), "unknown"),
    ],
)
def test_source_rejects_invalid_contract(raw: bytes, message: str) -> None:
    with pytest.raises(VocabularyError, match=message):
        import_source(raw)


def test_source_rejects_casefold_collision_for_same_identity() -> None:
    raw = source_bytes(
        [
            entry("WiFi", case_sensitive=True),
            entry("wifi", case_sensitive=False),
        ]
    )

    with pytest.raises(VocabularyError, match="duplicate"):
        import_source(raw)


def test_source_preserves_intentional_part_of_speech_ambiguity() -> None:
    raw = source_bytes(
        [
            entry("seal", "synthetic-noun", "noun-1"),
            entry("seal", "synthetic-verb", "verb-1"),
        ]
    )

    resource = import_source(raw)

    assert len(resource.entries) == 2


def test_canonical_resource_detects_content_tampering() -> None:
    resource = import_source(source_bytes([entry("flux valve")]))
    tampered = serialize_resource(resource).replace(b"flux valve", b"flux pump")

    with pytest.raises(VocabularyError, match="content_sha256"):
        parse_resource(tampered)


def test_source_rejects_non_finite_json_and_exact_duplicates() -> None:
    with pytest.raises(VocabularyError, match="constant"):
        import_source(b'{"format":NaN}')

    duplicate = entry("flux valve")
    with pytest.raises(VocabularyError, match="duplicate"):
        import_source(source_bytes([duplicate, duplicate]))


def test_source_enforces_byte_and_entry_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(VocabularyError, match="16 MiB"):
        import_source(b" " * (loader_module.MAX_RESOURCE_BYTES + 1))

    monkeypatch.setattr(loader_module, "MAX_ENTRIES", 1)
    with pytest.raises(VocabularyError, match="item limit"):
        import_source(source_bytes([entry("first"), entry("second")]))
