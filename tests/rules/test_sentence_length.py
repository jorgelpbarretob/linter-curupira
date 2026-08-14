import pytest

from ste_lint.domain import RuleContext, Severity
from ste_lint.parsing import parse_document
from ste_lint.rules.sentence_length import (
    DescriptiveSentenceLengthRule,
    ProceduralSentenceLengthRule,
)


@pytest.mark.parametrize(
    ("rule", "text_type", "word", "limit"),
    [
        (ProceduralSentenceLengthRule(), "procedural", "one", 20),
        (DescriptiveSentenceLengthRule(), "descriptive", "one", 25),
    ],
)
def test_sentence_length_reports_only_above_the_boundary(
    rule: object, text_type: str, word: str, limit: int
) -> None:
    at_limit = " ".join([word] * limit) + "."
    above_limit = " ".join([word] * (limit + 1)) + "."

    at_limit_document = parse_document("manual.txt", at_limit)
    above_limit_document = parse_document("manual.txt", above_limit)
    configuration = {"text_type": text_type}

    assert tuple(rule.check(RuleContext(at_limit_document, configuration))) == ()
    diagnostics = tuple(rule.check(RuleContext(above_limit_document, configuration)))
    assert len(diagnostics) == 1
    assert diagnostics[0].severity is Severity.INFO
    assert diagnostics[0].suggestion is None
    assert diagnostics[0].location.start_offset == 0
    assert diagnostics[0].location.end_offset == len(above_limit)


@pytest.mark.parametrize(
    ("rule", "configured_type"),
    [
        (ProceduralSentenceLengthRule(), None),
        (ProceduralSentenceLengthRule(), "descriptive"),
        (ProceduralSentenceLengthRule(), "procedural-note"),
        (DescriptiveSentenceLengthRule(), None),
        (DescriptiveSentenceLengthRule(), "procedural"),
    ],
)
def test_sentence_length_abstains_without_matching_text_type(
    rule: object, configured_type: str | None
) -> None:
    document = parse_document("manual.txt", " ".join(["word"] * 30) + ".")
    configuration = {} if configured_type is None else {"text_type": configured_type}

    assert tuple(rule.check(RuleContext(document, configuration))) == ()


@pytest.mark.parametrize(
    "text",
    [
        (
            "Inspect the type-2 pump with twenty additional simple words here now "
            "please today before operation starts again safely inside."
        ),
        (
            "Inspect the pump (including the spare unit) with many additional simple "
            "words before the scheduled operation starts again today."
        ),
        (
            "Inspect the pump at 20 mm and record many additional simple values before "
            "the scheduled operation starts again today."
        ),
    ],
)
def test_sentence_length_abstains_for_ambiguous_counting_constructs(text: str) -> None:
    document = parse_document("manual.txt", text)

    assert (
        tuple(
            ProceduralSentenceLengthRule().check(RuleContext(document, {"text_type": "procedural"}))
        )
        == ()
    )


def test_sentence_length_diagnostic_starts_after_vuepress_closing_marker() -> None:
    sentence = " ".join(["word"] * 21) + "."
    text = f":::\n\n{sentence}\n"
    document = parse_document("manual.md", text)

    diagnostics = tuple(
        ProceduralSentenceLengthRule().check(RuleContext(document, {"text_type": "procedural"}))
    )

    assert len(diagnostics) == 1
    assert diagnostics[0].location.start_offset == text.index(sentence)
    assert diagnostics[0].location.start_line == 3


def test_sentence_length_diagnostic_starts_after_vuepress_opening_marker() -> None:
    sentence = " ".join(["word"] * 21) + "."
    text = f":::warning\n{sentence}\n:::\n"
    document = parse_document("manual.md", text)

    diagnostics = tuple(
        ProceduralSentenceLengthRule().check(RuleContext(document, {"text_type": "procedural"}))
    )

    assert len(diagnostics) == 1
    assert diagnostics[0].location.start_offset == text.index(sentence)
    assert diagnostics[0].location.start_line == 2
