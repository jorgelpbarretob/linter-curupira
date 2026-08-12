import pytest

from ste_lint.domain import RuleContext, Severity
from ste_lint.parsing import parse_document
from ste_lint.rules.descriptive_paragraph import DescriptiveParagraphLengthRule


def sentence(number: int) -> str:
    return f"Synthetic component {number} is available."


@pytest.mark.parametrize("count", [7, 8, 9])
def test_descriptive_paragraph_rule_reports_more_than_six_sentences(count: int) -> None:
    text = " ".join(sentence(number) for number in range(count))
    document = parse_document("manual.txt", text)

    diagnostics = tuple(
        DescriptiveParagraphLengthRule().check(RuleContext(document, {"text_type": "descriptive"}))
    )

    assert len(diagnostics) == 1
    assert diagnostics[0].severity is Severity.INFO
    assert diagnostics[0].location.start_offset == 0
    assert diagnostics[0].location.end_offset == len(text)
    assert diagnostics[0].suggestion is None


@pytest.mark.parametrize("count", [1, 5, 6])
def test_descriptive_paragraph_rule_accepts_six_or_fewer_sentences(count: int) -> None:
    text = " ".join(sentence(number) for number in range(count))
    document = parse_document("manual.txt", text)

    assert (
        tuple(
            DescriptiveParagraphLengthRule().check(
                RuleContext(document, {"text_type": "descriptive"})
            )
        )
        == ()
    )


def test_descriptive_paragraph_rule_does_not_combine_separate_paragraphs() -> None:
    first = " ".join(sentence(number) for number in range(4))
    second = " ".join(sentence(number) for number in range(4, 8))
    document = parse_document("manual.txt", f"{first}\n\n{second}")

    assert (
        tuple(
            DescriptiveParagraphLengthRule().check(
                RuleContext(document, {"text_type": "descriptive"})
            )
        )
        == ()
    )


def test_descriptive_paragraph_rule_abstains_for_procedural_text() -> None:
    text = " ".join(sentence(number) for number in range(7))
    document = parse_document("manual.txt", text)

    assert (
        tuple(
            DescriptiveParagraphLengthRule().check(
                RuleContext(document, {"text_type": "procedural"})
            )
        )
        == ()
    )


def test_descriptive_paragraph_rule_abstains_for_markdown_list() -> None:
    text = "\n".join(f"- {sentence(number)}" for number in range(7))
    document = parse_document("manual.md", text)

    assert (
        tuple(
            DescriptiveParagraphLengthRule().check(
                RuleContext(document, {"text_type": "descriptive"})
            )
        )
        == ()
    )
