import pytest

from ste_lint.domain import RuleContext
from ste_lint.parsing import parse_text
from ste_lint.rules.nlp_support import NlpDecision
from ste_lint.rules.note_imperative import NoteImperativeRule
from tests.rules.nlp_fakes import FakeNlpBackend, make_analysis


def run_rule(
    text: str,
    specifications: tuple[tuple[str, str, str, str, int], ...],
    *,
    text_type: str = "procedural-note",
) -> tuple[NlpDecision, int]:
    document = parse_text("manual.txt", text)
    context = RuleContext(
        document,
        {"text_type": text_type},
        {"nlp": FakeNlpBackend(make_analysis(text, specifications))},
    )
    rule = NoteImperativeRule()
    evaluation = rule.evaluate_sentence(context, document.sentences[0])
    return evaluation.decision, len(rule.check(context))


@pytest.mark.parametrize(
    ("text", "specifications"),
    [
        (
            "Remove the access cover.",
            (
                ("Remove", "VERB", "VB", "ROOT", 0),
                ("the", "DET", "DT", "det", 3),
                ("access", "NOUN", "NN", "compound", 3),
                ("cover", "NOUN", "NN", "dobj", 0),
                (".", "PUNCT", ".", "punct", 0),
            ),
        ),
        (
            "Do not touch the hot surface.",
            (
                ("Do", "AUX", "VB", "aux", 2),
                ("not", "PART", "RB", "neg", 2),
                ("touch", "VERB", "VB", "ROOT", 2),
                ("the", "DET", "DT", "det", 5),
                ("hot", "ADJ", "JJ", "amod", 5),
                ("surface", "NOUN", "NN", "dobj", 2),
                (".", "PUNCT", ".", "punct", 2),
            ),
        ),
        (
            "If the indicator flashes, stop the test.",
            (
                ("If", "SCONJ", "IN", "mark", 3),
                ("the", "DET", "DT", "det", 2),
                ("indicator", "NOUN", "NN", "nsubj", 3),
                ("flashes", "VERB", "VBZ", "advcl", 5),
                (",", "PUNCT", ",", "punct", 3),
                ("stop", "VERB", "VB", "ROOT", 5),
                ("the", "DET", "DT", "det", 7),
                ("test", "NOUN", "NN", "dobj", 5),
                (".", "PUNCT", ".", "punct", 5),
            ),
        ),
    ],
)
def test_unambiguous_note_commands_are_reported(
    text: str, specifications: tuple[tuple[str, str, str, str, int], ...]
) -> None:
    assert run_rule(text, specifications) == (NlpDecision.EMIT, 1)


def test_explicit_subject_is_not_reported() -> None:
    specifications = (
        ("You", "PRON", "PRP", "nsubj", 2),
        ("can", "AUX", "MD", "aux", 2),
        ("use", "VERB", "VB", "ROOT", 2),
        ("an", "DET", "DT", "det", 5),
        ("equivalent", "ADJ", "JJ", "amod", 5),
        ("tool", "NOUN", "NN", "dobj", 2),
        (".", "PUNCT", ".", "punct", 2),
    )

    assert run_rule("You can use an equivalent tool.", specifications) == (
        NlpDecision.CLEAR,
        0,
    )


def test_nominal_fragment_abstains() -> None:
    specifications = (
        ("Access", "NOUN", "NN", "compound", 2),
        ("cover", "NOUN", "NN", "compound", 2),
        ("removal", "NOUN", "NN", "ROOT", 2),
        (".", "PUNCT", ".", "punct", 2),
    )

    assert run_rule("Access cover removal.", specifications) == (NlpDecision.ABSTAIN, 0)


def test_same_command_outside_procedural_note_is_out_of_scope() -> None:
    specifications = (
        ("Remove", "VERB", "VB", "ROOT", 0),
        ("the", "DET", "DT", "det", 2),
        ("cover", "NOUN", "NN", "dobj", 0),
        (".", "PUNCT", ".", "punct", 0),
    )

    assert run_rule("Remove the cover.", specifications, text_type="procedural") == (
        NlpDecision.CLEAR,
        0,
    )


def test_third_person_root_is_not_treated_as_a_command() -> None:
    specifications = (
        ("Removes", "VERB", "VBZ", "ROOT", 0),
        ("the", "DET", "DT", "det", 2),
        ("cover", "NOUN", "NN", "dobj", 0),
        (".", "PUNCT", ".", "punct", 0),
    )

    assert run_rule("Removes the cover.", specifications) == (NlpDecision.CLEAR, 0)


def test_finding_offsets_are_rebased_from_later_sentence_to_document() -> None:
    command = "Remove the cover."
    text = f"The indicator is green. {command}"
    specifications = (
        ("Remove", "VERB", "VB", "ROOT", 0),
        ("the", "DET", "DT", "det", 2),
        ("cover", "NOUN", "NN", "dobj", 0),
        (".", "PUNCT", ".", "punct", 0),
    )
    document = parse_text("manual.txt", text)
    context = RuleContext(
        document,
        {"text_type": "procedural-note"},
        {"nlp": FakeNlpBackend(make_analysis(command, specifications))},
    )

    evaluation = NoteImperativeRule().evaluate_sentence(context, document.sentences[1])

    assert evaluation.decision is NlpDecision.EMIT
    assert evaluation.findings[0].start_offset == text.index("Remove")
