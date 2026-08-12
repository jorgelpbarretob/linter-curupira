"""Immutable vocabulary models and deterministic lookup results."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Literal

LookupStatus = Literal["technical", "matched", "ambiguous", "missing"]


@dataclass(frozen=True, slots=True)
class VocabularyEntry:
    term: str
    part_of_speech: str
    meaning_id: str
    case_sensitive: bool


@dataclass(frozen=True, slots=True)
class VocabularyProvenance:
    source_format: str
    source_schema_version: int
    source_sha256: str
    content_sha256: str


@dataclass(frozen=True, slots=True)
class VocabularyResource:
    standard: str
    issue: str
    entries: tuple[VocabularyEntry, ...]
    provenance: VocabularyProvenance


@dataclass(frozen=True, slots=True)
class LookupResult:
    status: LookupStatus
    matches: tuple[VocabularyEntry, ...] = ()


class Vocabulary:
    """Case-aware lookup over one resource and a technical-terms overlay."""

    def __init__(
        self,
        resource: VocabularyResource,
        *,
        technical_terms: tuple[str, ...] = (),
    ) -> None:
        self._entries = tuple(
            sorted(
                resource.entries,
                key=lambda entry: (
                    entry.term,
                    entry.part_of_speech,
                    entry.meaning_id,
                    entry.case_sensitive,
                ),
            )
        )
        self._technical_terms = frozenset(
            unicodedata.normalize("NFC", term).casefold() for term in technical_terms
        )

    def lookup(
        self,
        term: str,
        *,
        part_of_speech: str | None = None,
        meaning_id: str | None = None,
    ) -> LookupResult:
        observed = unicodedata.normalize("NFC", term)
        if observed.casefold() in self._technical_terms:
            return LookupResult("technical")

        matches = tuple(
            entry
            for entry in self._entries
            if _term_matches(entry, observed)
            and (part_of_speech is None or entry.part_of_speech == part_of_speech)
            and (meaning_id is None or entry.meaning_id == meaning_id)
        )
        if not matches:
            return LookupResult("missing")
        if len(matches) == 1:
            return LookupResult("matched", matches)
        return LookupResult("ambiguous", matches)


def _term_matches(entry: VocabularyEntry, observed: str) -> bool:
    if entry.case_sensitive:
        return entry.term == observed
    return entry.term.casefold() == observed.casefold()
