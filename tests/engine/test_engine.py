from collections.abc import Iterable
from dataclasses import dataclass, field

import pytest

from ste_lint.domain import (
    CatalogMismatchError,
    Diagnostic,
    Document,
    RuleContext,
    RuleId,
    RuleKind,
    RuleMetadata,
    RuleRegistry,
    Severity,
    SourceLocation,
    SourceReference,
)
from ste_lint.engine import InvalidDiagnosticError, LintEngine, RuleExecutionError


def metadata(rule_id: str, *, status: str = "stable") -> RuleMetadata:
    return RuleMetadata(
        rule_id=RuleId(rule_id),
        title="Synthetic project rule",
        source=SourceReference(standard="PROJECT", issue="1", locator="local-test"),
        kind=RuleKind.DETERMINISTIC,
        default_severity=Severity.WARNING,
        summary="A synthetic engine test.",
        implementation_status=status,  # type: ignore[arg-type]
    )


def diagnostic(rule: RuleMetadata, document: Document, start: int) -> Diagnostic:
    return Diagnostic(
        rule_id=rule.rule_id,
        source=rule.source,
        severity=Severity.WARNING,
        location=SourceLocation(
            uri=document.uri,
            start_offset=start,
            end_offset=start + 1,
            start_line=1,
            start_column=start + 1,
            end_line=1,
            end_column=start + 2,
        ),
        message="Synthetic message.",
        explanation="Synthetic explanation.",
    )


@dataclass
class StubRule:
    metadata: RuleMetadata
    diagnostics: tuple[Diagnostic, ...] = ()
    error: Exception | None = None
    calls: int = field(default=0, init=False)

    def check(self, context: RuleContext) -> Iterable[Diagnostic]:
        del context
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.diagnostics


def test_engine_orders_diagnostics_by_location_then_rule_id() -> None:
    document = Document(uri="manual.txt", text="abcdef")
    alpha = metadata("PROJECT-TEST-001")
    beta = metadata("PROJECT-TEST-002")
    alpha_rule = StubRule(alpha, (diagnostic(alpha, document, 4), diagnostic(alpha, document, 1)))
    beta_rule = StubRule(beta, (diagnostic(beta, document, 1),))
    registry = RuleRegistry((beta, alpha))
    registry.register(beta_rule)
    registry.register(alpha_rule)

    result = LintEngine(registry).lint(
        RuleContext(document),
        enabled_rule_ids=(beta.rule_id, alpha.rule_id),
    )

    assert [(item.location.start_offset, item.rule_id) for item in result] == [
        (1, "PROJECT-TEST-001"),
        (1, "PROJECT-TEST-002"),
        (4, "PROJECT-TEST-001"),
    ]


def test_disabled_rule_is_not_executed() -> None:
    document = Document(uri="manual.txt", text="x")
    enabled = metadata("PROJECT-TEST-001")
    disabled = metadata("PROJECT-TEST-002")
    enabled_rule = StubRule(enabled)
    disabled_rule = StubRule(disabled)
    registry = RuleRegistry((enabled, disabled))
    registry.register(enabled_rule)
    registry.register(disabled_rule)

    LintEngine(registry).lint(RuleContext(document), enabled_rule_ids=(enabled.rule_id,))

    assert enabled_rule.calls == 1
    assert disabled_rule.calls == 0


def test_rule_exception_becomes_identifiable_operational_error() -> None:
    document = Document(uri="manual.txt", text="x")
    registered = metadata("PROJECT-TEST-001")
    rule = StubRule(registered, error=RuntimeError("synthetic failure"))
    registry = RuleRegistry((registered,))
    registry.register(rule)

    with pytest.raises(RuleExecutionError, match="PROJECT-TEST-001") as error:
        LintEngine(registry).lint(RuleContext(document), enabled_rule_ids=(registered.rule_id,))

    assert isinstance(error.value.__cause__, RuntimeError)


def test_engine_rejects_diagnostic_outside_document() -> None:
    document = Document(uri="manual.txt", text="x")
    registered = metadata("PROJECT-TEST-001")
    invalid = diagnostic(registered, document, 1)
    rule = StubRule(registered, (invalid,))
    registry = RuleRegistry((registered,))
    registry.register(rule)

    with pytest.raises(InvalidDiagnosticError, match="PROJECT-TEST-001"):
        LintEngine(registry).lint(RuleContext(document), enabled_rule_ids=(registered.rule_id,))


def test_engine_rejects_diagnostic_emitted_for_another_rule() -> None:
    document = Document(uri="manual.txt", text="x")
    first = metadata("PROJECT-TEST-001")
    second = metadata("PROJECT-TEST-002")
    first_rule = StubRule(first, (diagnostic(second, document, 0),))
    registry = RuleRegistry((first, second))
    registry.register(first_rule)
    registry.register(StubRule(second))

    with pytest.raises(CatalogMismatchError, match="emitted a diagnostic for"):
        LintEngine(registry).lint(RuleContext(document), enabled_rule_ids=(first.rule_id,))
