import json

from ste_lint.domain import (
    Diagnostic,
    RuleId,
    Severity,
    SourceLocation,
    SourceReference,
)
from ste_lint.reporting import format_json, format_text


def diagnostic(
    rule_id: str = "PROJECT-TEST-001", *, start: int = 0, suggestion: str | None = None
) -> Diagnostic:
    return Diagnostic(
        rule_id=RuleId(rule_id),
        source=SourceReference(standard="PROJECT", issue="1", locator="local-test"),
        severity=Severity.WARNING,
        location=SourceLocation(
            uri="manual.txt",
            start_offset=start,
            end_offset=start + 1,
            start_line=1,
            start_column=start + 1,
            end_line=1,
            end_column=start + 2,
        ),
        message="Synthetic message.",
        explanation="Synthetic café explanation.",
        suggestion=suggestion,
    )


def test_json_is_versioned_complete_and_deterministic() -> None:
    later = diagnostic("PROJECT-TEST-002", start=3, suggestion="Synthetic suggestion.")
    earlier = diagnostic()

    first = format_json((later, earlier))
    second = format_json((earlier, later))

    assert first == second
    assert first.endswith("\n")
    assert "café" in first
    payload = json.loads(first)
    assert payload["schema_version"] == "1.0"
    assert [item["rule_id"] for item in payload["diagnostics"]] == [
        "PROJECT-TEST-001",
        "PROJECT-TEST-002",
    ]
    assert payload["diagnostics"][0] == {
        "rule_id": "PROJECT-TEST-001",
        "source": {"standard": "PROJECT", "issue": "1", "locator": "local-test"},
        "severity": "warning",
        "location": {
            "uri": "manual.txt",
            "start_offset": 0,
            "end_offset": 1,
            "start_line": 1,
            "start_column": 1,
            "end_line": 1,
            "end_column": 2,
        },
        "message": "Synthetic message.",
        "explanation": "Synthetic café explanation.",
        "suggestion": None,
        "evidence": None,
    }


def test_text_contains_required_diagnostic_fields() -> None:
    output = format_text((diagnostic(suggestion="Synthetic suggestion."),), enabled_rule_count=1)

    assert "manual.txt:1:1" in output
    assert "[0, 1)" in output
    assert "warning PROJECT-TEST-001" in output
    assert "source: PROJECT issue 1, local-test" in output
    assert "message: Synthetic message." in output
    assert "explanation: Synthetic café explanation." in output
    assert "suggestion: Synthetic suggestion." in output


def test_text_distinguishes_no_enabled_rules_from_no_detected_violations() -> None:
    assert format_text((), enabled_rule_count=0) == "No executable rules are enabled.\n"
    assert format_text((), enabled_rule_count=2) == (
        "No violations were detected by the enabled rules.\n"
    )
