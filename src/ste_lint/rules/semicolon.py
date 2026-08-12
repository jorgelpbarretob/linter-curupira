"""Detect semicolons in lintable prose."""

from __future__ import annotations

from ste_lint.domain import (
    Diagnostic,
    RegionKind,
    RuleContext,
    RuleId,
    RuleKind,
    RuleMetadata,
    Severity,
    SourceReference,
)


class SemicolonRule:
    metadata = RuleMetadata(
        rule_id=RuleId("STE-I9-PUNCT-001"),
        title="Semicolon in lintable prose",
        source=SourceReference(
            standard="ASD-STE100",
            issue="9",
            locator="Part 1, Section 8, Rule 8.1",
        ),
        kind=RuleKind.DETERMINISTIC,
        default_severity=Severity.INFO,
        summary="Reports a semicolon found in lintable prose.",
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
                message="Semicolon in lintable prose.",
                explanation=("This preview rule reports semicolons that occur in visible prose."),
                evidence=token.text,
            )
            for token in document.tokens
            if token.kind is RegionKind.LINTABLE and token.text == ";"
        )
