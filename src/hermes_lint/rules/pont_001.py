"""Detecta ponto e vírgula em prosa lintável."""

from __future__ import annotations

from hermes_lint.domain import (
    Diagnostic,
    RegionKind,
    RuleContext,
    RuleId,
    RuleKind,
    RuleMetadata,
    Severity,
    SourceReference,
)


class Pont001Rule:
    metadata = RuleMetadata(
        rule_id=RuleId("HERMES-PT-PONT-001"),
        title="Ponto e vírgula em prosa lintável",
        source=SourceReference(
            standard="Hermes",
            issue="0.1",
            locator="Seção 5, HERMES-PT-PONT-001",
        ),
        kind=RuleKind.DETERMINISTIC,
        default_severity=Severity.INFO,
        summary="Detecta ponto e vírgula em prosa técnica lintável.",
        implementation_status="preview",
    )

    def check(self, context: RuleContext) -> tuple[Diagnostic, ...]:
        document = context.document
        return tuple(
            Diagnostic(
                rule_id=self.metadata.rule_id,
                source=self.metadata.source,
                severity=Severity.INFO,
                location=document.location(token.span),
                message="Ponto e vírgula em prosa lintável.",
                explanation=(
                    "Separe as informações em unidades explícitas adequadas à relação entre elas."
                ),
                evidence=token.text,
            )
            for token in document.tokens
            if token.kind is RegionKind.LINTABLE and token.text == ";"
        )
