"""Preview detection of command roots in text declared as a procedural note."""

from __future__ import annotations

from ste_lint.domain import (
    Diagnostic,
    RuleContext,
    RuleId,
    RuleKind,
    RuleMetadata,
    Sentence,
    Severity,
    SourceReference,
    TextSpan,
)
from ste_lint.rules.nlp_support import (
    NlpDecision,
    NlpEvaluation,
    analyze_contiguous_sentence,
)

_SUBJECT_DEPENDENCIES = {"nsubj", "nsubjpass", "expl"}


class NoteImperativeRule:
    metadata = RuleMetadata(
        rule_id=RuleId("STE-I9-NOTE-001"),
        title="Imperative in a procedural note",
        source=SourceReference(
            standard="ASD-STE100",
            issue="9",
            locator="Part 1, Section 5, Rule 5.5",
        ),
        kind=RuleKind.NLP,
        default_severity=Severity.INFO,
        summary="Reports unambiguous command roots in text declared as a procedural note.",
        implementation_status="preview",
    )

    def evaluate_sentence(self, context: RuleContext, sentence: Sentence) -> NlpEvaluation:
        if context.configuration.get("text_type") != "procedural-note":
            return NlpEvaluation(NlpDecision.CLEAR)
        analyzed = analyze_contiguous_sentence(context, sentence)
        if analyzed is None:
            return NlpEvaluation(NlpDecision.ABSTAIN)
        analysis, base_offset = analyzed
        roots = tuple(
            (index, token)
            for index, token in enumerate(analysis.tokens)
            if token.dependency == "ROOT"
        )
        if len(roots) != 1:
            return NlpEvaluation(NlpDecision.ABSTAIN)
        root_index, root = roots[0]
        has_subject = any(
            token.head_index == root_index and token.dependency in _SUBJECT_DEPENDENCIES
            for token in analysis.tokens
        )
        if root.pos == "VERB" and root.tag in {"VB", "VBP"} and not has_subject:
            return NlpEvaluation(
                NlpDecision.EMIT,
                (
                    TextSpan(
                        base_offset + root.start_offset,
                        base_offset + root.end_offset,
                    ),
                ),
            )
        if root.pos == "VERB" and root.tag == "VBP" and has_subject:
            return NlpEvaluation(NlpDecision.ABSTAIN)
        if not any(token.pos in {"VERB", "AUX"} for token in analysis.tokens):
            return NlpEvaluation(NlpDecision.ABSTAIN)
        return NlpEvaluation(NlpDecision.CLEAR)

    def check(self, context: RuleContext) -> tuple[Diagnostic, ...]:
        diagnostics: list[Diagnostic] = []
        for sentence in context.document.sentences:
            evaluation = self.evaluate_sentence(context, sentence)
            for span in evaluation.findings:
                diagnostics.append(
                    Diagnostic(
                        rule_id=self.metadata.rule_id,
                        source=self.metadata.source,
                        severity=self.metadata.default_severity,
                        location=context.document.location(span),
                        message="Command in text declared as a procedural note.",
                        explanation=(
                            "This preview rule found an unambiguous imperative root in text "
                            "declared as a procedural note."
                        ),
                        evidence=context.document.text[span.start_offset : span.end_offset],
                    )
                )
        return tuple(diagnostics)
