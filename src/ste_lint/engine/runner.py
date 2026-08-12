"""Rule engine with strict diagnostic validation."""

from __future__ import annotations

from ste_lint.domain import (
    CatalogMismatchError,
    Diagnostic,
    RuleContext,
    RuleId,
    RuleRegistry,
)


class RuleExecutionError(RuntimeError):
    """Raised when a rule implementation fails during execution."""


class InvalidDiagnosticError(ValueError):
    """Raised when a rule emits a diagnostic outside the document contract."""


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
                raise RuleExecutionError(f"rule {rule_id} failed during execution") from error

            for diagnostic in emitted:
                if diagnostic.rule_id != rule_id:
                    raise CatalogMismatchError(
                        f"rule {rule_id} emitted a diagnostic for {diagnostic.rule_id}"
                    )
                self._registry.validate_diagnostic(diagnostic)
                try:
                    diagnostic.validate_for(context.document)
                except ValueError as error:
                    raise InvalidDiagnosticError(
                        f"rule {rule_id} emitted an invalid document span"
                    ) from error
                diagnostics.append(diagnostic)

        return tuple(sorted(diagnostics, key=_diagnostic_sort_key))


def _diagnostic_sort_key(diagnostic: Diagnostic) -> tuple[str, int, int, str]:
    return (
        diagnostic.location.uri,
        diagnostic.location.start_offset,
        diagnostic.location.end_offset,
        str(diagnostic.rule_id),
    )
