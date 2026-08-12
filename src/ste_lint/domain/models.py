"""Immutable domain models with no I/O or outer-layer dependencies."""

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
            raise ValueError("span start must be non-negative")
        if self.end_offset <= self.start_offset:
            raise ValueError("span must be non-empty")


@dataclass(frozen=True, slots=True)
class TextRegion:
    span: TextSpan
    kind: RegionKind
    reason: str

    def __post_init__(self) -> None:
        if not self.reason:
            raise ValueError("region reason must not be empty")


@dataclass(frozen=True, slots=True)
class Token:
    span: TextSpan
    text: str
    kind: RegionKind

    def __post_init__(self) -> None:
        if not self.text:
            raise ValueError("token text must not be empty")


@dataclass(frozen=True, slots=True)
class Sentence:
    parts: tuple[TextSpan, ...]
    is_complete: bool

    def __post_init__(self) -> None:
        if not self.parts:
            raise ValueError("sentence must contain at least one span")
        previous_end = -1
        for part in self.parts:
            if part.start_offset < previous_end:
                raise ValueError("sentence spans must be ordered and non-overlapping")
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
            raise ValueError("document URI must not be empty")
        self._validate_partition(tuple(region.span for region in self.regions), "regions")
        self._validate_partition(tuple(token.span for token in self.tokens), "tokens")
        for token in self.tokens:
            if self.text[token.span.start_offset : token.span.end_offset] != token.text:
                raise ValueError("token text must match the source text")
        for sentence in self.sentences:
            for part in sentence.parts:
                if part.end_offset > len(self.text):
                    raise ValueError("sentence span must be within the document text")
                if not self._span_is_lintable(part):
                    raise ValueError("sentence spans must contain only lintable text")

    def _validate_partition(self, spans: tuple[TextSpan, ...], name: str) -> None:
        if not spans:
            return
        expected_start = 0
        for span in spans:
            if span.start_offset != expected_start:
                raise ValueError(f"{name} must partition the document text")
            expected_start = span.end_offset
        if expected_start != len(self.text):
            raise ValueError(f"{name} must partition the document text")

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
            raise IndexError("offset is outside the document")
        for region in self.regions:
            if region.span.start_offset <= offset < region.span.end_offset:
                return region.kind
        raise ValueError("document regions do not cover the requested offset")

    def location(self, span: TextSpan) -> SourceLocation:
        if span.end_offset > len(self.text):
            raise ValueError("span must be within the document text")
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
            raise ValueError("location URI must not be empty")
        if self.start_offset < 0:
            raise ValueError("start_offset must be non-negative")
        if self.end_offset <= self.start_offset:
            raise ValueError("source span must be non-empty")
        if min(self.start_line, self.start_column, self.end_line, self.end_column) < 1:
            raise ValueError("line and column values are 1-based")
        if (self.end_line, self.end_column) < (self.start_line, self.start_column):
            raise ValueError("end position must not precede start position")


@dataclass(frozen=True, slots=True)
class SourceReference:
    standard: str
    issue: str
    locator: str

    def __post_init__(self) -> None:
        if not self.standard or not self.issue or not self.locator:
            raise ValueError("source reference fields must not be empty")


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
            raise ValueError("rule identity, title, and summary must not be empty")
        if self.kind is RuleKind.SEMANTIC and self.default_severity is Severity.ERROR:
            raise ValueError("semantic rules cannot default to error severity")
        if self.kind is RuleKind.HUMAN_REVIEW and self.implementation_status == "stable":
            raise ValueError("human-review coverage cannot be an executable stable rule")
        if self.safe_autofix and self.implementation_status != "stable":
            raise ValueError("safe autofix requires a stable rule")


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
            raise ValueError("diagnostic identity, message, and explanation must not be empty")

    def validate_for(self, document: Document) -> None:
        if self.location.uri != document.uri:
            raise ValueError("diagnostic URI must match the document URI")
        if self.location.end_offset > len(document.text):
            raise ValueError("diagnostic span must be within the document text")


@dataclass(frozen=True, slots=True)
class RuleContext:
    document: Document
    configuration: Mapping[str, object] = field(default_factory=dict)
    capabilities: Mapping[str, object] = field(default_factory=dict)


class Rule(Protocol):
    metadata: RuleMetadata

    def check(self, context: RuleContext) -> Iterable[Diagnostic]: ...
