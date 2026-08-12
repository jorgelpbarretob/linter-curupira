import pytest

from ste_lint.domain import RuleContext, RuleKind, Severity
from ste_lint.parsing import parse_document
from ste_lint.rules.semicolon import SemicolonRule


@pytest.mark.parametrize(
    "text",
    [
        "Inspect the valve; replace the seal.",
        "The pump is ready; the controller is active.",
        "Open the cover; then disconnect the cable.",
    ],
)
def test_semicolon_rule_reports_lintable_semicolon(text: str) -> None:
    document = parse_document("manual.txt", text)

    diagnostics = tuple(SemicolonRule().check(RuleContext(document)))

    assert len(diagnostics) == 1
    diagnostic = diagnostics[0]
    assert diagnostic.rule_id == "STE-I9-PUNCT-001"
    assert diagnostic.source.issue == "9"
    assert diagnostic.source.locator == "Part 1, Section 8, Rule 8.1"
    assert diagnostic.severity is Severity.INFO
    assert diagnostic.location.start_offset == text.index(";")
    assert diagnostic.location.end_offset == text.index(";") + 1
    assert diagnostic.suggestion is None


@pytest.mark.parametrize(
    "text",
    [
        "Inspect the valve. Replace the seal.",
        "The pump is ready, and the controller is active.",
        "Use these tools:\n- A brush\n- A clean cloth.",
    ],
)
def test_semicolon_rule_does_not_report_text_without_semicolon(text: str) -> None:
    document = parse_document("manual.txt", text)

    assert tuple(SemicolonRule().check(RuleContext(document))) == ()


@pytest.mark.parametrize(
    "text",
    [
        "Set `mode=safe;retry=2` in the file.",
        "Open [the page](https://example.invalid/check;a=1).",
        "The nominal clearance is 5&nbsp;mm.",
    ],
)
def test_semicolon_rule_ignores_markdown_code_destinations_and_entities(text: str) -> None:
    document = parse_document("manual.md", text)

    assert tuple(SemicolonRule().check(RuleContext(document))) == ()


def test_semicolon_metadata_is_deterministic_preview_without_autofix() -> None:
    metadata = SemicolonRule.metadata

    assert metadata.kind is RuleKind.DETERMINISTIC
    assert metadata.implementation_status == "preview"
    assert metadata.default_severity is Severity.INFO
    assert metadata.safe_autofix is False
