"""Tipos imutáveis do domínio linguístico, independentes de SDK."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Protocol


class LinguisticContractError(ValueError):
    """Indica que um backend violou o contrato linguístico local."""


@dataclass(frozen=True, slots=True)
class SurfaceToken:
    text: str
    start_offset: int
    end_offset: int

    def __post_init__(self) -> None:
        if not self.text:
            raise LinguisticContractError("token de superfície não pode ser vazio")
        if self.start_offset < 0 or self.end_offset <= self.start_offset:
            raise LinguisticContractError("span de token inválido")


@dataclass(frozen=True, slots=True)
class SyntacticWord:
    surface_token_index: int
    lemma: str
    upos: str
    xpos: str | None
    features: tuple[tuple[str, str], ...]
    dependency: str
    head_word_index: int | None
    sentence_index: int

    def __post_init__(self) -> None:
        if self.surface_token_index < 0 or self.sentence_index < 0:
            raise LinguisticContractError("índice linguístico não pode ser negativo")
        if not self.lemma or not self.upos or not self.dependency:
            raise LinguisticContractError("lemma, UPOS e dependência são obrigatórios")
        if tuple(sorted(self.features)) != self.features:
            raise LinguisticContractError("features devem estar ordenadas")
        if self.head_word_index is not None and self.head_word_index < 0:
            raise LinguisticContractError("índice do head não pode ser negativo")


@dataclass(frozen=True, slots=True)
class LinguisticSentence:
    start_offset: int
    end_offset: int
    first_surface_token: int
    past_last_surface_token: int
    first_word: int
    past_last_word: int

    def __post_init__(self) -> None:
        if self.start_offset < 0 or self.end_offset <= self.start_offset:
            raise LinguisticContractError("span de sentença inválido")
        if not 0 <= self.first_surface_token < self.past_last_surface_token:
            raise LinguisticContractError("intervalo de tokens da sentença inválido")
        if not 0 <= self.first_word < self.past_last_word:
            raise LinguisticContractError("intervalo de palavras da sentença inválido")


@dataclass(frozen=True, slots=True)
class LinguisticAnalysis:
    text: str
    surface_tokens: tuple[SurfaceToken, ...]
    words: tuple[SyntacticWord, ...]
    sentences: tuple[LinguisticSentence, ...]
    backend: str
    backend_version: str
    model: str
    model_version: str
    model_sha256: str
    configuration_sha256: str

    def __post_init__(self) -> None:
        provenance = (
            self.backend,
            self.backend_version,
            self.model,
            self.model_version,
            self.model_sha256,
            self.configuration_sha256,
        )
        if any(not value for value in provenance):
            raise LinguisticContractError("proveniência linguística deve ser completa")
        self._validate_tokens()
        self._validate_sentences_and_words()

    def _validate_tokens(self) -> None:
        previous_end = 0
        for token in self.surface_tokens:
            if token.end_offset > len(self.text):
                raise LinguisticContractError("token ultrapassa o texto exato")
            if token.start_offset < previous_end:
                raise LinguisticContractError("tokens devem ser ordenados e não sobrepostos")
            if self.text[token.start_offset : token.end_offset] != token.text:
                raise LinguisticContractError("token não corresponde ao slice do texto exato")
            previous_end = token.end_offset

    def _validate_sentences_and_words(self) -> None:
        if not self.surface_tokens:
            if self.words or self.sentences:
                raise LinguisticContractError(
                    "análise sem tokens não pode conter palavras ou sentenças"
                )
            return
        if not self.words or not self.sentences:
            raise LinguisticContractError(
                "tokens, palavras e sentenças devem ter cobertura completa"
            )
        expected_token = 0
        expected_word = 0
        for sentence_index, sentence in enumerate(self.sentences):
            if (
                sentence.first_surface_token != expected_token
                or sentence.first_word != expected_word
            ):
                raise LinguisticContractError("sentenças devem particionar tokens e palavras")
            if sentence.past_last_surface_token > len(self.surface_tokens):
                raise LinguisticContractError("sentença referencia token inexistente")
            if sentence.past_last_word > len(self.words):
                raise LinguisticContractError("sentença referencia palavra inexistente")
            first = self.surface_tokens[sentence.first_surface_token]
            last = self.surface_tokens[sentence.past_last_surface_token - 1]
            if (sentence.start_offset, sentence.end_offset) != (
                first.start_offset,
                last.end_offset,
            ):
                raise LinguisticContractError("span da sentença deve envolver seus tokens exatos")
            roots = 0
            for word_index in range(sentence.first_word, sentence.past_last_word):
                word = self.words[word_index]
                if word.sentence_index != sentence_index:
                    raise LinguisticContractError("palavra atravessa limite de sentença")
                if (
                    not sentence.first_surface_token
                    <= word.surface_token_index
                    < sentence.past_last_surface_token
                ):
                    raise LinguisticContractError("palavra aponta para token fora da sentença")
                if word.head_word_index is None:
                    roots += 1
                elif not sentence.first_word <= word.head_word_index < sentence.past_last_word:
                    raise LinguisticContractError("head atravessa limite de sentença")
            if roots != 1:
                raise LinguisticContractError("cada sentença deve conter exatamente uma raiz")
            expected_token = sentence.past_last_surface_token
            expected_word = sentence.past_last_word
        if expected_token != len(self.surface_tokens) or expected_word != len(self.words):
            raise LinguisticContractError("sentenças não cobrem toda a análise")


class LocalLinguisticBackend(Protocol):
    def analyze(self, text: str) -> LinguisticAnalysis: ...


def analysis_to_dict(analysis: LinguisticAnalysis) -> dict[str, object]:
    """Omite ``analysis.text``; o consumidor o correlaciona pelo URI e SHA-256 externos."""
    return {
        "surface_tokens": [asdict(token) for token in analysis.surface_tokens],
        "words": [asdict(word) for word in analysis.words],
        "sentences": [asdict(sentence) for sentence in analysis.sentences],
        "provenance": {
            "backend": analysis.backend,
            "backend_version": analysis.backend_version,
            "model": analysis.model,
            "model_version": analysis.model_version,
            "model_sha256": analysis.model_sha256,
            "configuration_sha256": analysis.configuration_sha256,
        },
    }
