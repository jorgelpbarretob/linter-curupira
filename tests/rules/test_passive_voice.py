import pytest

from ste_lint.domain import RuleContext
from ste_lint.parsing import parse_text
from ste_lint.rules.nlp_support import NlpDecision
from ste_lint.rules.passive_voice import PassiveVoiceRule
from tests.rules.nlp_fakes import FakeNlpBackend, make_analysis


def run_rule(
    text: str,
    specifications: tuple[tuple[str, str, str, str, int], ...],
    *,
    text_type: str,
) -> tuple[NlpDecision, int]:
    document = parse_text("manual.txt", text)
    context = RuleContext(
        document,
        {"text_type": text_type},
        {"nlp": FakeNlpBackend(make_analysis(text, specifications))},
    )
    rule = PassiveVoiceRule()
    evaluation = rule.evaluate_sentence(context, document.sentences[0])
    return evaluation.decision, len(rule.check(context))


PASSIVE_WITH_AGENT = (
    ("The", "DET", "DT", "det", 2),
    ("access", "NOUN", "NN", "compound", 2),
    ("panel", "NOUN", "NN", "nsubjpass", 4),
    ("is", "AUX", "VBZ", "auxpass", 4),
    ("removed", "VERB", "VBN", "ROOT", 4),
    ("by", "ADP", "IN", "agent", 4),
    ("the", "DET", "DT", "det", 7),
    ("technician", "NOUN", "NN", "pobj", 5),
    (".", "PUNCT", ".", "punct", 4),
)

PASSIVE_WITH_MODAL = (
    ("The", "DET", "DT", "det", 1),
    ("pressure", "NOUN", "NN", "nsubjpass", 4),
    ("must", "AUX", "MD", "aux", 4),
    ("be", "AUX", "VB", "auxpass", 4),
    ("adjusted", "VERB", "VBN", "ROOT", 4),
    ("before", "ADP", "IN", "prep", 4),
    ("the", "DET", "DT", "det", 7),
    ("test", "NOUN", "NN", "pobj", 5),
    (".", "PUNCT", ".", "punct", 4),
)

BARE_PASSIVE = (
    ("The", "DET", "DT", "det", 1),
    ("valve", "NOUN", "NN", "nsubjpass", 3),
    ("is", "AUX", "VBZ", "auxpass", 3),
    ("closed", "VERB", "VBN", "ROOT", 3),
    (".", "PUNCT", ".", "punct", 3),
)


@pytest.mark.parametrize("text_type", ["procedural", "descriptive", "procedural-note"])
def test_explicit_agent_is_reported_for_all_supported_text_types(text_type: str) -> None:
    decision, diagnostic_count = run_rule(
        "The access panel is removed by the technician.",
        PASSIVE_WITH_AGENT,
        text_type=text_type,
    )

    assert decision is NlpDecision.EMIT
    assert diagnostic_count == 1


def test_modal_passive_is_reported_only_in_procedural_text() -> None:
    assert run_rule(
        "The pressure must be adjusted before the test.",
        PASSIVE_WITH_MODAL,
        text_type="procedural",
    ) == (NlpDecision.EMIT, 1)
    assert run_rule(
        "The pressure must be adjusted before the test.",
        PASSIVE_WITH_MODAL,
        text_type="descriptive",
    ) == (NlpDecision.ABSTAIN, 0)


def test_ambiguous_bare_passive_abstains() -> None:
    assert run_rule("The valve is closed.", BARE_PASSIVE, text_type="procedural") == (
        NlpDecision.ABSTAIN,
        0,
    )


def test_participial_adjective_is_not_a_passive_candidate() -> None:
    specifications = tuple(
        (value[0], "ADJ", value[2], value[3], value[4]) if value[0] == "closed" else value
        for value in BARE_PASSIVE
    )

    assert run_rule("The valve is closed.", specifications, text_type="descriptive") == (
        NlpDecision.CLEAR,
        0,
    )


def test_incomplete_sentence_abstains_without_calling_backend() -> None:
    document = parse_text("manual.txt", "The valve is closed")
    context = RuleContext(document, {"text_type": "procedural"}, {})

    evaluation = PassiveVoiceRule().evaluate_sentence(context, document.sentences[0])

    assert evaluation.decision is NlpDecision.ABSTAIN


def test_finding_offsets_are_rebased_from_later_sentence_to_document() -> None:
    passive = "The access panel is removed by the technician."
    text = f"Open the valve. {passive}"
    document = parse_text("manual.txt", text)
    context = RuleContext(
        document,
        {"text_type": "procedural"},
        {"nlp": FakeNlpBackend(make_analysis(passive, PASSIVE_WITH_AGENT))},
    )

    evaluation = PassiveVoiceRule().evaluate_sentence(context, document.sentences[1])

    assert evaluation.decision is NlpDecision.EMIT
    assert evaluation.findings[0].start_offset == text.index("removed")
    assert evaluation.findings[0].end_offset == text.index("removed") + len("removed")
