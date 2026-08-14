"""Modelos de domínio imutáveis, sem I/O nem dependências externas."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal, NewType, Protocol

RuleId = NewType("RuleId", str)
ImplementationStatus = Literal["planned", "preview", "stable"]


class RuleKind(StrEnum):
    DETERMINISTIC = "deterministic"
    NLP = "nlp"
    SEMANTIC = "semantic"
    HUMAN_REVIEW = "human-review"


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class RegionKind(StrEnum):
    LINTABLE = "lintable"
    IGNORED = "ignored"


@dataclass(frozen=True, slots=True)
class TextSpan:
    start_offset: int
    end_offset: int

    def __post_init__(self) -> None:
        if self.start_offset < 0:
            raise ValueError("o início do span deve ser não negativo")
        if self.end_offset <= self.start_offset:
            raise ValueError("o span deve ser não vazio")


@dataclass(frozen=True, slots=True)
class TextRegion:
    span: TextSpan
    kind: RegionKind
    reason: str

    def __post_init__(self) -> None:
        if not self.reason:
            raise ValueError("a razão da região não pode ser vazia")


@dataclass(frozen=True, slots=True)
class Token:
    span: TextSpan
    text: str
    kind: RegionKind

    def __post_init__(self) -> None:
        if not self.text:
            raise ValueError("o texto do token não pode ser vazio")


@dataclass(frozen=True, slots=True)
class Sentence:
    parts: tuple[TextSpan, ...]
    is_complete: bool

    def __post_init__(self) -> None:
        if not self.parts:
            raise ValueError("a sentença deve conter ao menos um span")
        previous_end = -1
        for part in self.parts:
            if part.start_offset < previous_end:
                raise ValueError("spans da sentença devem ser ordenados e não sobrepostos")
            previous_end = part.end_offset

    def text(self, document: Document) -> str:
        return "".join(document.text[part.start_offset : part.end_offset] for part in self.parts)


@dataclass(frozen=True, slots=True)
class Document:
    uri: str
    text: str
    regions: tuple[TextRegion, ...] = ()
    tokens: tuple[Token, ...] = ()
    sentences: tuple[Sentence, ...] = ()

    def __post_init__(self) -> None:
        if not self.uri:
            raise ValueError("a URI do documento não pode ser vazia")
        self._validate_partition(tuple(region.span for region in self.regions), "regiões")
        self._validate_partition(tuple(token.span for token in self.tokens), "tokens")
        for token in self.tokens:
            if self.text[token.span.start_offset : token.span.end_offset] != token.text:
                raise ValueError("o token deve corresponder ao texto-fonte")
        for sentence in self.sentences:
            for part in sentence.parts:
                if part.end_offset > len(self.text):
                    raise ValueError("o span da sentença deve estar dentro do documento")
                if not self._span_is_lintable(part):
                    raise ValueError("spans da sentença devem conter apenas texto lintável")

    def _validate_partition(self, spans: tuple[TextSpan, ...], name: str) -> None:
        if not spans:
            return
        expected_start = 0
        for span in spans:
            if span.start_offset != expected_start:
                raise ValueError(f"{name} devem particionar o texto do documento")
            expected_start = span.end_offset
        if expected_start != len(self.text):
            raise ValueError(f"{name} devem particionar o texto do documento")

    def _span_is_lintable(self, span: TextSpan) -> bool:
        covered = span.start_offset
        for region in self.regions:
            if region.span.end_offset <= covered:
                continue
            if region.span.start_offset >= span.end_offset:
                break
            if region.kind is not RegionKind.LINTABLE:
                return False
            covered = min(span.end_offset, region.span.end_offset)
        return covered == span.end_offset

    @property
    def lintable_text(self) -> str:
        return "".join(
            self.text[region.span.start_offset : region.span.end_offset]
            for region in self.regions
            if region.kind is RegionKind.LINTABLE
        )

    def kind_at(self, offset: int) -> RegionKind:
        if offset < 0 or offset >= len(self.text):
            raise IndexError("offset fora do documento")
        for region in self.regions:
            if region.span.start_offset <= offset < region.span.end_offset:
                return region.kind
        raise ValueError("as regiões não cobrem o offset solicitado")

    def location(self, span: TextSpan) -> SourceLocation:
        if span.end_offset > len(self.text):
            raise ValueError("o span deve estar dentro do documento")
        start_line, start_column = self._line_and_column(span.start_offset)
        end_line, end_column = self._line_and_column(span.end_offset)
        return SourceLocation(
            uri=self.uri,
            start_offset=span.start_offset,
            end_offset=span.end_offset,
            start_line=start_line,
            start_column=start_column,
            end_line=end_line,
            end_column=end_column,
        )

    def _line_and_column(self, offset: int) -> tuple[int, int]:
        line = self.text.count("\n", 0, offset) + 1
        last_newline = self.text.rfind("\n", 0, offset)
        column = offset - last_newline
        return line, column


@dataclass(frozen=True, slots=True)
class SourceLocation:
    uri: str
    start_offset: int
    end_offset: int
    start_line: int
    start_column: int
    end_line: int
    end_column: int

    def __post_init__(self) -> None:
        if not self.uri:
            raise ValueError("a URI da localização não pode ser vazia")
        if self.start_offset < 0:
            raise ValueError("start_offset deve ser não negativo")
        if self.end_offset <= self.start_offset:
            raise ValueError("o span de origem deve ser não vazio")
        if min(self.start_line, self.start_column, self.end_line, self.end_column) < 1:
            raise ValueError("linha e coluna usam índice iniciado em 1")
        if (self.end_line, self.end_column) < (self.start_line, self.start_column):
            raise ValueError("a posição final não pode preceder a inicial")


@dataclass(frozen=True, slots=True)
class SourceReference:
    standard: str
    issue: str
    locator: str

    def __post_init__(self) -> None:
        if not self.standard or not self.issue or not self.locator:
            raise ValueError("os campos da referência não podem ser vazios")


@dataclass(frozen=True, slots=True)
class RuleMetadata:
    rule_id: RuleId
    title: str
    source: SourceReference
    kind: RuleKind
    default_severity: Severity
    summary: str
    implementation_status: ImplementationStatus
    safe_autofix: bool = False

    def __post_init__(self) -> None:
        if not self.rule_id or not self.title or not self.summary:
            raise ValueError("identidade, título e resumo da regra não podem ser vazios")
        if self.kind is RuleKind.SEMANTIC and self.default_severity is Severity.ERROR:
            raise ValueError("regra semântica não pode usar error como severidade padrão")
        if self.kind is RuleKind.HUMAN_REVIEW and self.implementation_status == "stable":
            raise ValueError("revisão humana não pode ser regra executável estável")
        if self.safe_autofix and self.implementation_status != "stable":
            raise ValueError("autofix seguro exige regra estável")


@dataclass(frozen=True, slots=True)
class Diagnostic:
    rule_id: RuleId
    source: SourceReference
    severity: Severity
    location: SourceLocation
    message: str
    explanation: str
    suggestion: str | None = None
    evidence: str | None = None

    def __post_init__(self) -> None:
        if not self.rule_id or not self.message or not self.explanation:
            raise ValueError("identidade, mensagem e explicação não podem ser vazias")

    def validate_for(self, document: Document) -> None:
        if self.location.uri != document.uri:
            raise ValueError("a URI do diagnóstico deve corresponder ao documento")
        if self.location.end_offset > len(document.text):
            raise ValueError("o span do diagnóstico deve estar dentro do documento")


@dataclass(frozen=True, slots=True)
class RuleContext:
    document: Document
    configuration: Mapping[str, object] = field(default_factory=dict)
    capabilities: Mapping[str, object] = field(default_factory=dict)


class Rule(Protocol):
    metadata: RuleMetadata

    def check(self, context: RuleContext) -> Iterable[Diagnostic]: ...
