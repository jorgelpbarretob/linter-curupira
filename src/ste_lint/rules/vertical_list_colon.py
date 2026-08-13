"""Narrow detector for clear Markdown list lead-ins without a colon."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePath

from ste_lint.domain import (
    Diagnostic,
    Document,
    RegionKind,
    RuleContext,
    RuleId,
    RuleKind,
    RuleMetadata,
    Severity,
    SourceReference,
    TextSpan,
)

_LIST_MARKER = re.compile(r"^[ ]{0,3}(?:[-+*]|\d+[.)])[ \t]+")
_CLEAR_ASSOCIATION = re.compile(
    r"\bthese[ \t]+[^\W\d_]+(?:-[^\W\d_]+)*s\.$",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class _Line:
    start: int
    content_end: int
    end: int


class VerticalListLeadInColonRule:
    metadata = RuleMetadata(
        rule_id=RuleId("STE-I9-LIST-001"),
        title="Vertical-list lead-in colon",
        source=SourceReference(
            standard="ASD-STE100",
            issue="9",
            locator="Part 1, Section 4, Rule 4.3",
        ),
        kind=RuleKind.DETERMINISTIC,
        default_severity=Severity.INFO,
        summary="Reports a narrow class of clear list lead-ins that end with a period.",
        implementation_status="preview",
    )

    def check(self, context: RuleContext) -> tuple[Diagnostic, ...]:
        if PurePath(context.document.uri).suffix.lower() not in {".md", ".markdown"}:
            return ()

        document = context.document
        lines = _lines(document.text)
        diagnostics: list[Diagnostic] = []
        index = 1
        while index < len(lines):
            if not _is_lintable_list_item(document, lines[index]):
                index += 1
                continue
            run_end = index + 1
            while run_end < len(lines) and _is_lintable_list_item(document, lines[run_end]):
                run_end += 1
            if run_end - index >= 2:
                diagnostic = _diagnostic_for_lead_in(document, lines[index - 1], self.metadata)
                if diagnostic is not None:
                    diagnostics.append(diagnostic)
            index = run_end
        return tuple(diagnostics)


def _lines(text: str) -> tuple[_Line, ...]:
    result: list[_Line] = []
    offset = 0
    for raw_line in text.splitlines(keepends=True):
        content_end = offset + len(raw_line.rstrip("\r\n"))
        result.append(_Line(offset, content_end, offset + len(raw_line)))
        offset += len(raw_line)
    if not result and text:
        result.append(_Line(0, len(text), len(text)))
    return tuple(result)


def _is_lintable_list_item(document: Document, line: _Line) -> bool:
    content = document.text[line.start : line.content_end]
    marker = _LIST_MARKER.match(content)
    if marker is None:
        return False
    prose_offset = line.start + marker.end()
    return prose_offset < line.content_end and document.kind_at(prose_offset) is RegionKind.LINTABLE


def _diagnostic_for_lead_in(
    document: Document, line: _Line, metadata: RuleMetadata
) -> Diagnostic | None:
    content = document.text[line.start : line.content_end]
    stripped = content.rstrip()
    if not stripped or not _CLEAR_ASSOCIATION.search(stripped):
        return None
    if not _is_single_complete_sentence(document, line):
        return None
    if not _all_lintable(document, TextSpan(line.start, line.content_end)):
        return None
    if stripped.endswith(":"):
        return None
    if not stripped.endswith("."):
        return None

    punctuation_offset = line.start + len(stripped) - 1
    span = TextSpan(punctuation_offset, punctuation_offset + 1)
    return Diagnostic(
        rule_id=metadata.rule_id,
        source=metadata.source,
        severity=Severity.INFO,
        location=document.location(span),
        message="Clear vertical-list lead-in does not end with a colon.",
        explanation=(
            "This preview rule covers direct Markdown lists introduced by a line "
            "that ends with 'these' and one plural head word."
        ),
        evidence="direct-list-lead-in",
    )


def _is_single_complete_sentence(document: Document, line: _Line) -> bool:
    content = document.text[line.start : line.content_end]
    trimmed_start = line.start + len(content) - len(content.lstrip(" \t"))
    trimmed_end = line.start + len(content.rstrip(" \t"))
    if trimmed_start >= trimmed_end:
        return False

    overlapping = tuple(
        sentence
        for sentence in document.sentences
        if any(
            part.start_offset < trimmed_end and part.end_offset > trimmed_start
            for part in sentence.parts
        )
    )
    return (
        len(overlapping) == 1
        and overlapping[0].is_complete
        and overlapping[0].parts == (TextSpan(trimmed_start, trimmed_end),)
    )


def _all_lintable(document: Document, span: TextSpan) -> bool:
    for region in document.regions:
        overlaps = (
            region.span.start_offset < span.end_offset
            and region.span.end_offset > span.start_offset
        )
        if overlaps and region.kind is RegionKind.IGNORED:
            return False
    return True
