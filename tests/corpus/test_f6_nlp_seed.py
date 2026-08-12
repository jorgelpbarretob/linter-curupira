import json
import socket
from collections import Counter
from pathlib import Path

import pytest

from ste_lint.domain import RuleContext
from ste_lint.engine import NlpConfiguration
from ste_lint.nlp import NlpSetupError
from ste_lint.nlp.spacy_backend import load_spacy_backend
from ste_lint.parsing import parse_text
from ste_lint.rules.nlp_support import NlpDecision
from ste_lint.rules.note_imperative import NoteImperativeRule
from ste_lint.rules.passive_voice import PassiveVoiceRule

CORPUS_PATH = Path(__file__).parent / "data" / "f6_nlp_seed.json"


def load_cases() -> list[dict[str, str]]:
    payload = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    return payload["cases"]  # type: ignore[no-any-return]


@pytest.fixture(scope="module")
def backend() -> object:
    try:
        return load_spacy_backend(NlpConfiguration())
    except NlpSetupError as error:
        pytest.skip(str(error))


def evaluate(case: dict[str, str], backend: object) -> NlpDecision:
    document = parse_text("synthetic.txt", case["text"])
    context = RuleContext(document, {"text_type": case["text_type"]}, {"nlp": backend})
    rule = PassiveVoiceRule() if case["rule_id"] == "STE-I9-VOICE-001" else NoteImperativeRule()
    return rule.evaluate_sentence(context, document.sentences[0]).decision


def test_pinned_model_matches_all_approved_and_expanded_labels(backend: object) -> None:
    for case in load_cases():
        decision = evaluate(case, backend)
        if case["expected"] == "emit":
            assert decision is NlpDecision.EMIT, case
        elif case["expected"] == "abstain":
            assert decision is NlpDecision.ABSTAIN, case
        else:
            assert decision is not NlpDecision.EMIT, case


def test_pinned_model_load_and_analysis_are_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    def reject_connection(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise AssertionError("NLP runtime attempted a network connection")

    monkeypatch.setattr(socket.socket, "connect", reject_connection)
    try:
        local_backend = load_spacy_backend(NlpConfiguration())
    except NlpSetupError as error:
        pytest.skip(str(error))

    analysis = local_backend.analyze("Remove the cover.")

    assert analysis.model_version == "3.8.0"


def test_seed_confusion_matrix_and_abstention_gate(backend: object) -> None:
    results: Counter[tuple[str, str]] = Counter()
    unsafe_emissions: Counter[str] = Counter()
    for case in load_cases():
        decision = evaluate(case, backend)
        if case["truth"] == "indeterminate":
            results[(case["rule_id"], "indeterminate")] += 1
            results[(case["rule_id"], "abstained")] += decision is not NlpDecision.EMIT
            unsafe_emissions[case["rule_id"]] += decision is NlpDecision.EMIT
            continue
        positive = decision is NlpDecision.EMIT
        outcomes = {
            ("violation", True): "tp",
            ("violation", False): "fn",
            ("non-violation", True): "fp",
            ("non-violation", False): "tn",
        }
        outcome = outcomes[(case["truth"], positive)]
        results[(case["rule_id"], outcome)] += 1

    assert results[("STE-I9-VOICE-001", "tp")] == 4
    assert results[("STE-I9-VOICE-001", "tn")] == 5
    assert results[("STE-I9-VOICE-001", "fp")] == 0
    assert results[("STE-I9-VOICE-001", "fn")] == 0
    assert results[("STE-I9-VOICE-001", "abstained")] == 4
    assert results[("STE-I9-NOTE-001", "tp")] == 6
    assert results[("STE-I9-NOTE-001", "tn")] == 5
    assert results[("STE-I9-NOTE-001", "fp")] == 0
    assert results[("STE-I9-NOTE-001", "fn")] == 0
    assert results[("STE-I9-NOTE-001", "abstained")] == 2
    assert unsafe_emissions == Counter()
