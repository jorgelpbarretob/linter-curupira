"""Vendor-neutral contracts for optional NLP capabilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class NlpToken:
    """One parser token with offsets relative to the analyzed text."""

    text: str
    start_offset: int
    end_offset: int
    lemma: str
    pos: str
    tag: str
    dependency: str
    head_index: int

    def __post_init__(self) -> None:
        if not self.text:
            raise ValueError("NLP token text must not be empty")
        if self.start_offset < 0 or self.end_offset <= self.start_offset:
            raise ValueError("NLP token offsets must describe a non-empty span")
        if not all((self.lemma, self.pos, self.tag, self.dependency)):
            raise ValueError("NLP token parser attributes must not be empty")
        if self.head_index < 0:
            raise ValueError("NLP token head index must be non-negative")


@dataclass(frozen=True, slots=True)
class NlpAnalysis:
    """Validated parser output with reproducible backend identity."""

    text: str
    tokens: tuple[NlpToken, ...]
    backend: str
    backend_version: str
    model: str
    model_version: str

    def __post_init__(self) -> None:
        if not all((self.backend, self.backend_version, self.model, self.model_version)):
            raise ValueError("NLP backend and model identity must not be empty")
        previous_end = -1
        for token in self.tokens:
            if token.start_offset < previous_end:
                raise ValueError("NLP tokens must be ordered and non-overlapping")
            if token.end_offset > len(self.text):
                raise ValueError("NLP token must be within the analyzed text")
            if self.text[token.start_offset : token.end_offset] != token.text:
                raise ValueError("NLP token must match the source text")
            if token.head_index >= len(self.tokens):
                raise ValueError("NLP token head index must identify an analysis token")
            previous_end = token.end_offset


@runtime_checkable
class NlpBackend(Protocol):
    """Capability supplied to NLP rules without exposing an SDK type."""

    def analyze(self, text: str) -> NlpAnalysis: ...
