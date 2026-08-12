from collections.abc import Iterable
from dataclasses import dataclass, replace

import pytest

from ste_lint.domain import (
    CatalogMismatchError,
    Diagnostic,
    DuplicateRuleIdError,
    RuleContext,
    RuleId,
    RuleKind,
    RuleMetadata,
    RuleRegistry,
    Severity,
    SourceLocation,
    SourceReference,
)


@dataclass(frozen=True)
class StubRule:
    metadata: RuleMetadata

    def check(self, context: RuleContext) -> Iterable[Diagnostic]:
        del context
        return ()


def metadata(rule_id: str = "PROJECT-TEST-001") -> RuleMetadata:
    return RuleMetadata(
        rule_id=RuleId(rule_id),
        title="Synthetic project rule",
        source=SourceReference(standard="PROJECT", issue="1", locator="local-test"),
        kind=RuleKind.DETERMINISTIC,
        default_severity=Severity.WARNING,
        summary="A synthetic registry test.",
        implementation_status="preview",
    )


def test_registry_rejects_duplicate_rule_id() -> None:
    registered = metadata()
    registry = RuleRegistry((registered,))
    registry.register(StubRule(metadata()))

    with pytest.raises(DuplicateRuleIdError, match="PROJECT-TEST-001"):
        registry.register(StubRule(metadata()))


def test_registry_rejects_duplicate_id_inside_catalog() -> None:
    registered = metadata()

    with pytest.raises(DuplicateRuleIdError, match="duplicate catalog"):
        RuleRegistry((registered, registered))


def test_registry_rejects_implementation_metadata_divergence() -> None:
    registered = metadata()
    registry = RuleRegistry((registered,))

    with pytest.raises(CatalogMismatchError, match="metadata differs"):
        registry.register(StubRule(replace(registered, title="Different title")))


def test_registry_rejects_invalid_rule_id_namespace() -> None:
    invalid = replace(metadata(), rule_id=RuleId("LOCAL-TEST-001"))

    with pytest.raises(CatalogMismatchError, match="invalid rule_id"):
        RuleRegistry((invalid,))


def test_registry_returns_rules_in_rule_id_order() -> None:
    first = metadata("PROJECT-Z-001")
    second = metadata("PROJECT-A-001")
    registry = RuleRegistry((first, second))
    registry.register(StubRule(first))
    registry.register(StubRule(second))

    assert [rule.metadata.rule_id for rule in registry.all()] == [
        "PROJECT-A-001",
        "PROJECT-Z-001",
    ]


def test_registry_rejects_diagnostic_with_divergent_source() -> None:
    registered = metadata()
    registry = RuleRegistry((registered,))
    registry.register(StubRule(registered))
    diagnostic = Diagnostic(
        rule_id=registered.rule_id,
        source=SourceReference(standard="PROJECT", issue="1", locator="different"),
        severity=Severity.WARNING,
        location=SourceLocation(
            uri="manual.md",
            start_offset=0,
            end_offset=1,
            start_line=1,
            start_column=1,
            end_line=1,
            end_column=2,
        ),
        message="Synthetic message.",
        explanation="Synthetic explanation.",
    )

    with pytest.raises(CatalogMismatchError, match="source"):
        registry.validate_diagnostic(diagnostic)


def test_registry_rejects_implementation_not_present_in_catalog() -> None:
    registry = RuleRegistry(())

    with pytest.raises(CatalogMismatchError, match="not present in the catalog"):
        registry.register(StubRule(metadata()))


def test_registry_startup_rejects_missing_preview_implementation() -> None:
    registry = RuleRegistry((metadata(),))

    with pytest.raises(CatalogMismatchError, match="missing implementation"):
        registry.validate_startup()


def test_registry_rejects_preview_diagnostic_above_info() -> None:
    registered = metadata()
    registry = RuleRegistry((registered,))
    registry.register(StubRule(registered))
    diagnostic = Diagnostic(
        rule_id=registered.rule_id,
        source=registered.source,
        severity=Severity.WARNING,
        location=SourceLocation(
            uri="manual.md",
            start_offset=0,
            end_offset=1,
            start_line=1,
            start_column=1,
            end_line=1,
            end_column=2,
        ),
        message="Synthetic message.",
        explanation="Synthetic explanation.",
    )

    with pytest.raises(CatalogMismatchError, match="preview"):
        registry.validate_diagnostic(diagnostic)


def test_registry_rejects_semantic_warning_even_when_stable() -> None:
    registered = RuleMetadata(
        rule_id=RuleId("PROJECT-TEST-001"),
        title="Synthetic semantic rule",
        source=SourceReference(standard="PROJECT", issue="1", locator="local-test"),
        kind=RuleKind.SEMANTIC,
        default_severity=Severity.WARNING,
        summary="A synthetic registry test.",
        implementation_status="stable",
    )
    registry = RuleRegistry((registered,))
    registry.register(StubRule(registered))
    diagnostic = Diagnostic(
        rule_id=registered.rule_id,
        source=registered.source,
        severity=Severity.WARNING,
        location=SourceLocation(
            uri="manual.md",
            start_offset=0,
            end_offset=1,
            start_line=1,
            start_column=1,
            end_line=1,
            end_column=2,
        ),
        message="Synthetic message.",
        explanation="Synthetic explanation.",
    )

    with pytest.raises(CatalogMismatchError, match="semantic"):
        registry.validate_diagnostic(diagnostic)
