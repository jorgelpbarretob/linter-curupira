from dataclasses import FrozenInstanceError

import pytest

from ste_lint.domain import (
    Diagnostic,
    Document,
    RuleId,
    RuleKind,
    RuleMetadata,
    Severity,
    SourceLocation,
    SourceReference,
)


def source() -> SourceReference:
    return SourceReference(standard="ASD-STE100", issue="9", locator="Part 1, Rule 8.1")


def location() -> SourceLocation:
    return SourceLocation(
        uri="manual.md",
        start_offset=4,
        end_offset=5,
        start_line=1,
        start_column=5,
        end_line=1,
        end_column=6,
    )


def test_location_rejects_empty_span() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        SourceLocation(
            uri="manual.md",
            start_offset=4,
            end_offset=4,
            start_line=1,
            start_column=5,
            end_line=1,
            end_column=5,
        )


def test_location_rejects_zero_based_line() -> None:
    with pytest.raises(ValueError, match="1-based"):
        SourceLocation(
            uri="manual.md",
            start_offset=0,
            end_offset=1,
            start_line=0,
            start_column=1,
            end_line=1,
            end_column=2,
        )


def test_semantic_rule_cannot_default_to_error() -> None:
    with pytest.raises(ValueError, match="semantic"):
        RuleMetadata(
            rule_id=RuleId("STE-I9-TEST-001"),
            title="Semantic candidate",
            source=source(),
            kind=RuleKind.SEMANTIC,
            default_severity=Severity.ERROR,
            summary="A synthetic test rule.",
            implementation_status="preview",
        )


def test_diagnostic_is_immutable() -> None:
    diagnostic = Diagnostic(
        rule_id=RuleId("STE-I9-TEST-001"),
        source=source(),
        severity=Severity.WARNING,
        location=location(),
        message="Synthetic message.",
        explanation="Synthetic explanation.",
    )

    with pytest.raises(FrozenInstanceError):
        diagnostic.message = "Changed"  # type: ignore[misc]


def test_diagnostic_rejects_span_outside_document() -> None:
    diagnostic = Diagnostic(
        rule_id=RuleId("STE-I9-TEST-001"),
        source=source(),
        severity=Severity.WARNING,
        location=location(),
        message="Synthetic message.",
        explanation="Synthetic explanation.",
    )

    with pytest.raises(ValueError, match="document text"):
        diagnostic.validate_for(Document(uri="manual.md", text="four"))
