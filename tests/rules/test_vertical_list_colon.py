import pytest

from ste_lint.domain import RuleContext, Severity
from ste_lint.parsing import parse_document
from ste_lint.rules.vertical_list_colon import VerticalListLeadInColonRule


@pytest.mark.parametrize(
    "lead_in",
    [
        "Prepare these tools.",
        "The kit contains these items.",
        "Record these values.",
    ],
)
def test_vertical_list_rule_reports_clear_lead_in_without_colon(lead_in: str) -> None:
    text = f"{lead_in}\n- First item\n- Second item"
    document = parse_document("manual.md", text)

    diagnostics = tuple(VerticalListLeadInColonRule().check(RuleContext(document)))

    assert len(diagnostics) == 1
    assert diagnostics[0].severity is Severity.INFO
    assert diagnostics[0].location.start_offset == len(lead_in) - 1
    assert diagnostics[0].location.end_offset == len(lead_in)
    assert diagnostics[0].suggestion is None


@pytest.mark.parametrize(
    "lead_in",
    [
        "Prepare these tools:",
        "The kit contains these items:",
        "Record these values:",
    ],
)
def test_vertical_list_rule_accepts_clear_lead_in_with_colon(lead_in: str) -> None:
    text = f"{lead_in}\n- First item\n- Second item"
    document = parse_document("manual.md", text)

    assert tuple(VerticalListLeadInColonRule().check(RuleContext(document))) == ()


@pytest.mark.parametrize(
    "text",
    [
        "## Required tools\n\n- A brush\n- A cloth",
        "```text\nPrepare these tools.\n- A brush\n- A cloth\n```",
        "The inspection is complete.\n\n---\n\n- Archive the report\n- Close the record",
    ],
)
def test_vertical_list_rule_abstains_without_direct_clear_association(text: str) -> None:
    document = parse_document("manual.md", text)

    assert tuple(VerticalListLeadInColonRule().check(RuleContext(document))) == ()
