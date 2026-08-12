import json

from ste_lint.vocabulary import Vocabulary, import_source


def vocabulary() -> Vocabulary:
    raw = json.dumps(
        {
            "format": "ste-lint-vocabulary-source",
            "schema_version": 1,
            "standard": "ASD-STE100",
            "issue": "9",
            "entries": [
                {
                    "term": "seal",
                    "part_of_speech": "synthetic-noun",
                    "meaning_id": "noun-1",
                    "case_sensitive": False,
                },
                {
                    "term": "seal",
                    "part_of_speech": "synthetic-verb",
                    "meaning_id": "verb-1",
                    "case_sensitive": False,
                },
                {
                    "term": "ZX-4",
                    "part_of_speech": "synthetic-identifier",
                    "meaning_id": "identifier-1",
                    "case_sensitive": True,
                },
                {
                    "term": "élan",
                    "part_of_speech": "synthetic-noun",
                    "meaning_id": "unicode-1",
                    "case_sensitive": False,
                },
            ],
        },
        separators=(",", ":"),
    ).encode()
    return Vocabulary(import_source(raw), technical_terms=("bleed-air valve",))


def test_lookup_returns_closed_states_and_preserves_meaning() -> None:
    index = vocabulary()

    ambiguous = index.lookup("SEAL")
    matched = index.lookup("seal", part_of_speech="synthetic-verb")
    missing_case = index.lookup("zx-4")
    technical = index.lookup("BLEED-AIR VALVE")

    assert ambiguous.status == "ambiguous"
    assert len(ambiguous.matches) == 2
    assert matched.status == "matched"
    assert matched.matches[0].meaning_id == "verb-1"
    assert missing_case.status == "missing"
    assert technical.status == "technical"
    assert technical.matches == ()


def test_lookup_filters_part_of_speech_and_meaning_exactly() -> None:
    index = vocabulary()

    assert index.lookup("seal", part_of_speech="SYNTHETIC-VERB").status == "missing"
    assert index.lookup("seal", meaning_id="verb-1").status == "matched"


def test_lookup_normalizes_observed_unicode_to_nfc() -> None:
    assert vocabulary().lookup("e\u0301lan").status == "matched"


def test_ambiguous_matches_are_stable_across_source_order() -> None:
    entries = [
        {
            "term": "seal",
            "part_of_speech": "synthetic-verb",
            "meaning_id": "verb-1",
            "case_sensitive": False,
        },
        {
            "term": "seal",
            "part_of_speech": "synthetic-noun",
            "meaning_id": "noun-1",
            "case_sensitive": False,
        },
    ]

    def build(items: list[dict[str, object]]) -> Vocabulary:
        raw = json.dumps(
            {
                "format": "ste-lint-vocabulary-source",
                "schema_version": 1,
                "standard": "ASD-STE100",
                "issue": "9",
                "entries": items,
            },
            separators=(",", ":"),
        ).encode()
        return Vocabulary(import_source(raw))

    forward = build(entries).lookup("seal")
    reverse = build(list(reversed(entries))).lookup("seal")

    assert forward == reverse
