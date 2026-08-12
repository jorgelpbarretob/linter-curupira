"""Conservative preview detection of parser-confirmed passive voice."""

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


class PassiveVoiceRule:
    metadata = RuleMetadata(
        rule_id=RuleId("STE-I9-VOICE-001"),
        title="Parser-confirmed passive voice",
        source=SourceReference(
            standard="ASD-STE100",
            issue="9",
            locator="Part 1, Section 3, Rule 3.6",
        ),
        kind=RuleKind.NLP,
        default_severity=Severity.INFO,
        summary="Reports only high-confidence passive constructions in declared text types.",
        implementation_status="preview",
    )

    def evaluate_sentence(self, context: RuleContext, sentence: Sentence) -> NlpEvaluation:
        text_type = context.configuration.get("text_type")
        if text_type not in {"procedural", "descriptive", "procedural-note"}:
            return NlpEvaluation(NlpDecision.ABSTAIN)
        analyzed = analyze_contiguous_sentence(context, sentence)
        if analyzed is None:
            return NlpEvaluation(NlpDecision.ABSTAIN)
        analysis, base_offset = analyzed
        candidates: list[int] = []
        findings: list[TextSpan] = []
        for index, token in enumerate(analysis.tokens):
            if token.pos != "VERB" or token.tag != "VBN":
                continue
            children = tuple(child for child in analysis.tokens if child.head_index == index)
            if not any(child.dependency == "auxpass" for child in children):
                continue
            candidates.append(index)
            has_agent = any(child.dependency == "agent" for child in children)
            has_modal = any(child.dependency == "aux" and child.tag == "MD" for child in children)
            if has_agent or (text_type == "procedural" and has_modal):
                findings.append(
                    TextSpan(
                        base_offset + token.start_offset,
                        base_offset + token.end_offset,
                    )
                )
        if findings:
            return NlpEvaluation(NlpDecision.EMIT, tuple(findings))
        if candidates:
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
                        message="High-confidence passive construction.",
                        explanation=(
                            "This preview rule found a parser-confirmed passive construction "
                            "that meets its conservative reporting policy."
                        ),
                        evidence=context.document.text[span.start_offset : span.end_offset],
                    )
                )
        return tuple(diagnostics)
