"""Conservative sentence-length rules for explicitly declared text types."""

from __future__ import annotations

from ste_lint.domain import (
    Diagnostic,
    Document,
    RegionKind,
    RuleContext,
    RuleId,
    RuleKind,
    RuleMetadata,
    Sentence,
    Severity,
    SourceReference,
)

_SIMPLE_PUNCTUATION = {",", ".", "!", "?", ":", ";"}


class _SentenceLengthRule:
    metadata: RuleMetadata
    text_type: str
    limit: int

    def check(self, context: RuleContext) -> tuple[Diagnostic, ...]:
        if context.configuration.get("text_type") != self.text_type:
            return ()

        diagnostics: list[Diagnostic] = []
        for sentence in context.document.sentences:
            count = _simple_word_count(context.document, sentence)
            if count is None or count <= self.limit:
                continue
            span = sentence.parts[0]
            diagnostics.append(
                Diagnostic(
                    rule_id=self.metadata.rule_id,
                    source=self.metadata.source,
                    severity=Severity.INFO,
                    location=context.document.location(span),
                    message=f"{self.text_type.title()} sentence exceeds {self.limit} words.",
                    explanation=(
                        "This preview rule counts only unambiguous alphabetic words "
                        f"and reports a count of {count}."
                    ),
                    evidence=f"word_count={count}; limit={self.limit}",
                )
            )
        return tuple(diagnostics)


class ProceduralSentenceLengthRule(_SentenceLengthRule):
    text_type = "procedural"
    limit = 20
    metadata = RuleMetadata(
        rule_id=RuleId("STE-I9-SENT-001"),
        title="Procedural sentence length",
        source=SourceReference(
            standard="ASD-STE100",
            issue="9",
            locator=("Part 1, Section 5, Rule 5.1; Part 1, Section 8, Rules 8.4-8.7"),
        ),
        kind=RuleKind.DETERMINISTIC,
        default_severity=Severity.INFO,
        summary="Reports an unambiguously countable procedural sentence above 20 words.",
        implementation_status="preview",
    )


class DescriptiveSentenceLengthRule(_SentenceLengthRule):
    text_type = "descriptive"
    limit = 25
    metadata = RuleMetadata(
        rule_id=RuleId("STE-I9-SENT-002"),
        title="Descriptive sentence length",
        source=SourceReference(
            standard="ASD-STE100",
            issue="9",
            locator=("Part 1, Section 6, Rule 6.3; Part 1, Section 8, Rules 8.4-8.7"),
        ),
        kind=RuleKind.DETERMINISTIC,
        default_severity=Severity.INFO,
        summary="Reports an unambiguously countable descriptive sentence above 25 words.",
        implementation_status="preview",
    )


def _simple_word_count(document: Document, sentence: Sentence) -> int | None:
    if not sentence.is_complete or len(sentence.parts) != 1:
        return None
    span = sentence.parts[0]
    count = 0
    for token in document.tokens:
        if token.span.end_offset <= span.start_offset:
            continue
        if token.span.start_offset >= span.end_offset:
            break
        if token.kind is not RegionKind.LINTABLE or token.text.isspace():
            continue
        if token.text.isalpha():
            count += 1
            continue
        if token.text not in _SIMPLE_PUNCTUATION:
            return None
    return count
