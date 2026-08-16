"""Relatório estável das capacidades executáveis."""

from __future__ import annotations

from collections.abc import Iterable

from curupira_lint.domain import Rule, RuleMetadata


def format_rule_list(rules: Iterable[Rule]) -> str:
    ordered = sorted(rules, key=lambda rule: str(rule.metadata.rule_id))
    return "".join(
        (
            f"{rule.metadata.rule_id}\t{rule.metadata.implementation_status}\t"
            f"{rule.metadata.kind.value}\t{rule.metadata.title}\n"
        )
        for rule in ordered
    )


def format_rule_explanation(metadata: RuleMetadata) -> str:
    return (
        f"rule_id: {metadata.rule_id}\n"
        f"título: {metadata.title}\n"
        f"status: {metadata.implementation_status}\n"
        f"classe: {metadata.kind.value}\n"
        f"fonte: {metadata.source.standard} {metadata.source.issue}, {metadata.source.locator}\n"
        f"resumo: {metadata.summary}\n"
    )
