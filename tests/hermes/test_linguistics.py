from __future__ import annotations

from dataclasses import dataclass

import pytest

from hermes_lint.linguistics import (
    LinguisticContractError,
    adapt_spacy_document,
)


@dataclass
class _Morph:
    values: dict[str, str]

    def to_dict(self) -> dict[str, str]:
        return self.values


class _Token:
    def __init__(
        self,
        text: str,
        index: int,
        offset: int,
        *,
        lemma: str,
        pos: str,
        dependency: str,
        is_space: bool = False,
    ) -> None:
        self.text = text
        self.i = index
        self.idx = offset
        self.lemma_ = lemma
        self.pos_ = pos
        self.tag_ = ""
        self.dep_ = dependency
        self.morph = _Morph({"Number": "Sing"} if pos == "NOUN" else {})
        self.is_space = is_space
        self.head = self


class _Doc:
    def __init__(self, text: str, tokens: list[_Token], sentences: list[list[_Token]]) -> None:
        self.text = text
        self._tokens = tokens
        self.sents = sentences

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(self._tokens)


def test_spacy_projection_preserves_exact_unicode_offsets_and_dependencies() -> None:
    text = "Ligue a bomba."
    ligue = _Token("Ligue", 0, 0, lemma="ligar", pos="VERB", dependency="ROOT")
    artigo = _Token("a", 1, 6, lemma="o", pos="DET", dependency="det")
    bomba = _Token("bomba", 2, 8, lemma="bomba", pos="NOUN", dependency="obj")
    ponto = _Token(".", 3, 13, lemma=".", pos="PUNCT", dependency="punct")
    artigo.head = bomba
    bomba.head = ligue
    ponto.head = ligue
    doc = _Doc(text, [ligue, artigo, bomba, ponto], [[ligue, artigo, bomba, ponto]])

    analysis = adapt_spacy_document(text, doc)

    assert [
        (token.text, token.start_offset, token.end_offset) for token in analysis.surface_tokens
    ] == [
        ("Ligue", 0, 5),
        ("a", 6, 7),
        ("bomba", 8, 13),
        (".", 13, 14),
    ]
    assert analysis.words[0].head_word_index is None
    assert analysis.words[2].head_word_index == 0
    assert analysis.words[2].features == (("Number", "Sing"),)
    assert analysis.sentences[0].past_last_word == 4


def test_spacy_projection_rejects_backend_text_drift() -> None:
    token = _Token("Ligue", 0, 0, lemma="ligar", pos="VERB", dependency="ROOT")

    with pytest.raises(LinguisticContractError, match="texto exato"):
        adapt_spacy_document("Ligue.", _Doc("Ligue!", [token], [[token]]))


def test_spacy_projection_rejects_invalid_sdk_heads() -> None:
    root = _Token("Ligue", 0, 0, lemma="ligar", pos="VERB", dependency="ROOT")
    object_ = _Token("bomba", 1, 6, lemma="bomba", pos="NOUN", dependency="obj")
    doc = _Doc("Ligue bomba", [root, object_], [[root, object_]])

    with pytest.raises(LinguisticContractError, match="não raiz.*auto-head"):
        adapt_spacy_document(doc.text, doc)

    object_.head = root
    root.head = object_
    with pytest.raises(LinguisticContractError, match="raiz.*auto-head"):
        adapt_spacy_document(doc.text, doc)


def test_spacy_projection_ignores_whitespace_only_sdk_sentences() -> None:
    leading = _Token("  ", 0, 0, lemma="  ", pos="SPACE", dependency="dep", is_space=True)
    root = _Token("Ligue", 1, 2, lemma="ligar", pos="VERB", dependency="ROOT")
    point = _Token(".", 2, 7, lemma=".", pos="PUNCT", dependency="punct")
    trailing = _Token("  ", 3, 8, lemma="  ", pos="SPACE", dependency="dep", is_space=True)
    point.head = root
    doc = _Doc(
        "  Ligue.  ",
        [leading, root, point, trailing],
        [[leading], [root, point], [trailing]],
    )

    analysis = adapt_spacy_document(doc.text, doc)

    assert [(token.text, token.start_offset) for token in analysis.surface_tokens] == [
        ("Ligue", 2),
        (".", 7),
    ]
    assert len(analysis.sentences) == 1


def test_spacy_projection_reports_sentence_coverage_counts() -> None:
    root = _Token("Ligue", 0, 0, lemma="ligar", pos="VERB", dependency="ROOT")

    with pytest.raises(LinguisticContractError, match="cobertos=0, emitidos=1"):
        adapt_spacy_document("Ligue", _Doc("Ligue", [root], []))


def test_spacy_projection_accepts_empty_text_as_empty_analysis() -> None:
    analysis = adapt_spacy_document("", _Doc("", [], []))

    assert analysis.text == ""
    assert analysis.surface_tokens == ()
    assert analysis.words == ()
    assert analysis.sentences == ()
