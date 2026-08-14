"""Engine com validação estrita de diagnósticos."""

from __future__ import annotations

from hermes_lint.domain import CatalogMismatchError, Diagnostic, RuleContext, RuleId, RuleRegistry


class RuleExecutionError(RuntimeError):
    """Indica falha interna durante a execução de uma regra."""


class InvalidDiagnosticError(ValueError):
    """Indica diagnóstico fora do contrato do documento."""


class LintEngine:
    def __init__(self, registry: RuleRegistry) -> None:
        registry.validate_startup()
        self._registry = registry

    def lint(
        self,
        context: RuleContext,
        *,
        enabled_rule_ids: tuple[RuleId, ...],
    ) -> tuple[Diagnostic, ...]:
        diagnostics: list[Diagnostic] = []
        for rule_id in sorted(set(enabled_rule_ids), key=str):
            rule = self._registry.get(rule_id)
            try:
                emitted = tuple(rule.check(context))
            except Exception as error:
                raise RuleExecutionError(f"falha ao executar {rule_id}") from error
            for diagnostic in emitted:
                if diagnostic.rule_id != rule_id:
                    raise CatalogMismatchError(f"{rule_id} emitiu diagnóstico de outra regra")
                self._registry.validate_diagnostic(diagnostic)
                try:
                    diagnostic.validate_for(context.document)
                except ValueError as error:
                    raise InvalidDiagnosticError(f"{rule_id} emitiu span inválido") from error
                diagnostics.append(diagnostic)
        return tuple(
            sorted(
                diagnostics,
                key=lambda item: (
                    item.location.uri,
                    item.location.start_offset,
                    item.location.end_offset,
                    str(item.rule_id),
                ),
            )
        )
