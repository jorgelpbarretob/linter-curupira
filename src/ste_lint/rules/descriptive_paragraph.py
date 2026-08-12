"""Conservative descriptive-paragraph length detector."""

from __future__ import annotations

import re

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

_PARAGRAPH_SEPARATOR = re.compile(r"\r?\n[ \t]*\r?\n+")


class DescriptiveParagraphLengthRule:
    metadata = RuleMetadata(
        rule_id=RuleId("STE-I9-PARA-001"),
        title="Descriptive paragraph length",
        source=SourceReference(
            standard="ASD-STE100",
            issue="9",
            locator="Part 1, Section 6, Rule 6.6",
        ),
        kind=RuleKind.DETERMINISTIC,
        default_severity=Severity.INFO,
        summary="Reports an unambiguous descriptive paragraph above six sentences.",
        implementation_status="preview",
    )

    def check(self, context: RuleContext) -> tuple[Diagnostic, ...]:
        if context.configuration.get("text_type") != "descriptive":
            return ()

        diagnostics: list[Diagnostic] = []
        for paragraph in _paragraph_spans(context.document.text):
            count = _unambiguous_sentence_count(context.document, paragraph)
            if count is None or count <= 6:
                continue
            diagnostics.append(
                Diagnostic(
                    rule_id=self.metadata.rule_id,
                    source=self.metadata.source,
                    severity=Severity.INFO,
                    location=context.document.location(paragraph),
                    message="Descriptive paragraph exceeds six sentences.",
                    explanation=(
                        "This preview rule reports only paragraphs with "
                        f"{count} unambiguously delimited prose sentences."
                    ),
                    evidence=f"sentence_count={count}; limit=6",
                )
            )
        return tuple(diagnostics)


def _paragraph_spans(text: str) -> tuple[TextSpan, ...]:
    boundaries = [0]
    boundaries.extend(match.end() for match in _PARAGRAPH_SEPARATOR.finditer(text))
    ends = [match.start() for match in _PARAGRAPH_SEPARATOR.finditer(text)]
    ends.append(len(text))

    spans: list[TextSpan] = []
    for raw_start, raw_end in zip(boundaries, ends, strict=True):
        start = raw_start
        end = raw_end
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        if end > start:
            spans.append(TextSpan(start, end))
    return tuple(spans)


def _unambiguous_sentence_count(document: Document, paragraph: TextSpan) -> int | None:
    for region in document.regions:
        overlaps = (
            region.span.start_offset < paragraph.end_offset
            and region.span.end_offset > paragraph.start_offset
        )
        if overlaps and region.kind is RegionKind.IGNORED:
            return None

    relevant = []
    for sentence in document.sentences:
        overlaps = any(
            part.start_offset < paragraph.end_offset and part.end_offset > paragraph.start_offset
            for part in sentence.parts
        )
        if not overlaps:
            continue
        if (
            not sentence.is_complete
            or len(sentence.parts) != 1
            or sentence.parts[0].start_offset < paragraph.start_offset
            or sentence.parts[0].end_offset > paragraph.end_offset
        ):
            return None
        relevant.append(sentence)
    return len(relevant)
