"""Shared conservative mechanics for optional NLP rules."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ste_lint.domain import RuleContext, Sentence, TextSpan
from ste_lint.nlp import NlpAnalysis, NlpBackend


class NlpDecision(StrEnum):
    CLEAR = "clear"
    EMIT = "emit"
    ABSTAIN = "abstain"


@dataclass(frozen=True, slots=True)
class NlpEvaluation:
    decision: NlpDecision
    findings: tuple[TextSpan, ...] = ()

    def __post_init__(self) -> None:
        if (self.decision is NlpDecision.EMIT) != bool(self.findings):
            raise ValueError("only an emitting NLP evaluation can contain findings")


def analyze_contiguous_sentence(
    context: RuleContext, sentence: Sentence
) -> tuple[NlpAnalysis, int] | None:
    """Analyze only the exact complete source span accepted by ADR-014."""

    if not sentence.is_complete or len(sentence.parts) != 1:
        return None
    capability = context.capabilities.get("nlp")
    if not isinstance(capability, NlpBackend):
        return None
    source_span = sentence.parts[0]
    text = context.document.text[source_span.start_offset : source_span.end_offset]
    analysis = capability.analyze(text)
    if analysis.text != text:
        raise ValueError("NLP backend returned analysis for different source text")
    return analysis, source_span.start_offset
