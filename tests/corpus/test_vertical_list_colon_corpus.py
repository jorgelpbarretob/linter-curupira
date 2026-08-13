import hashlib
import json
from pathlib import Path

from ste_lint.domain import RuleContext
from ste_lint.parsing import parse_document
from ste_lint.rules.vertical_list_colon import VerticalListLeadInColonRule


def test_vertical_list_rule_matches_human_approved_seed_labels() -> None:
    cases = [
        json.loads(line)
        for line in Path("corpus/seed/vertical-list-lead-in-colon.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]

    assert len(cases) == 13
    assert all(case["review_status"] == "approved" for case in cases)
    for case in cases:
        suffix = "md" if case["source_format"] == "markdown" else "txt"
        document = parse_document(f"{case['case_id']}.{suffix}", case["text"])
        diagnostics = tuple(VerticalListLeadInColonRule().check(RuleContext(document)))
        assert len(diagnostics) == case["expected_diagnostics"], case["case_id"]
        for diagnostic in diagnostics:
            start = diagnostic.location.start_offset
            end = diagnostic.location.end_offset
            assert document.text[start:end] == ".", case["case_id"]


def test_vertical_list_rule_matches_approved_f7_readiness_labels() -> None:
    cases = [
        json.loads(line)
        for line in Path("corpus/f7/vertical-list-provider-readiness.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]

    assert len(cases) == 16
    assert all(case["review_status"] == "approved" for case in cases)
    for case in cases:
        suffix = "md" if case["source_format"] == "markdown" else "txt"
        document = parse_document(f"{case['case_id']}.{suffix}", case["text"])
        diagnostics = tuple(VerticalListLeadInColonRule().check(RuleContext(document)))
        assert len(diagnostics) == case["expected_diagnostics"], case["case_id"]
        for diagnostic in diagnostics:
            start = diagnostic.location.start_offset
            end = diagnostic.location.end_offset
            assert document.text[start:end] == ".", case["case_id"]
            assert case["expected_replacement"] == ":", case["case_id"]


def test_vertical_list_rule_matches_approved_blank_line_challenge() -> None:
    cases = [
        json.loads(line)
        for line in Path("corpus/f7/vertical-list-blank-line-challenge.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]

    assert len(cases) == 17
    assert all(case["review_status"] == "approved" for case in cases)
    for case in cases:
        document = parse_document(f"{case['case_id']}.md", case["text"])
        diagnostics = tuple(VerticalListLeadInColonRule().check(RuleContext(document)))
        assert len(diagnostics) == case["expected_diagnostics"], case["case_id"]
        for diagnostic in diagnostics:
            start = diagnostic.location.start_offset
            end = diagnostic.location.end_offset
            assert document.text[start:end] == ".", case["case_id"]
            assert case["expected_replacement"] == ":", case["case_id"]


def test_vertical_list_rule_matches_approved_evidence_challenge() -> None:
    cases = [
        json.loads(line)
        for line in Path("corpus/f7/vertical-list-evidence-challenge.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]

    assert len(cases) == 47
    assert all(case["review_status"] == "approved" for case in cases)
    for case in cases:
        suffix = "md" if case["source_format"] == "markdown" else "txt"
        document = parse_document(f"{case['case_id']}.{suffix}", case["text"])
        diagnostics = tuple(VerticalListLeadInColonRule().check(RuleContext(document)))
        assert len(diagnostics) == case["expected_diagnostics"], case["case_id"]
        for diagnostic in diagnostics:
            start = diagnostic.location.start_offset
            end = diagnostic.location.end_offset
            assert document.text[start:end] == ".", case["case_id"]
            assert case["expected_replacement"] == ":", case["case_id"]


def test_consumed_v1_holdout_is_a_recall_regression() -> None:
    path = Path("corpus/f7/vertical-list-holdout.jsonl")
    frozen_hash = "30d30b0ab2377983f33329a032286ed6f31cfab7b92cd168fc335a66d34b1cc7"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == frozen_hash
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    assert len(cases) == 60
    assert all(case["review_status"] == "approved" for case in cases)
    mismatches: list[str] = []
    for case in cases:
        document = parse_document(f"{case['case_id']}.md", case["text"])
        diagnostics = tuple(VerticalListLeadInColonRule().check(RuleContext(document)))
        if len(diagnostics) != case["expected_diagnostics"]:
            mismatches.append(case["case_id"])
        for diagnostic in diagnostics:
            start = diagnostic.location.start_offset
            end = diagnostic.location.end_offset
            assert document.text[start:end] == ".", case["case_id"]
            assert case["expected_replacement"] == ":", case["case_id"]
    assert mismatches == ["f7-list-ho-github-p08"]


def test_frozen_holdout_controls_have_no_false_positives() -> None:
    path = Path("corpus/f7/vertical-list-holdout.jsonl")
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    controls = [case for case in cases if case["truth"] == "non_violation"]
    assert len(controls) == 30
    for case in controls:
        document = parse_document(f"{case['case_id']}.md", case["text"])
        diagnostics = tuple(VerticalListLeadInColonRule().check(RuleContext(document)))
        assert diagnostics == (), case["case_id"]


def test_consumed_v2_holdout_is_a_regression() -> None:
    path = Path("corpus/f7/vertical-list-holdout-v2.jsonl")
    frozen_hash = "b91d6c6c1bd7f5955332e86e80504c1890e3437531ce352781084ab74cd07ca2"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == frozen_hash
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    assert len(cases) == 60
    assert all(case["review_status"] == "approved" for case in cases)
    for case in cases:
        document = parse_document(f"{case['case_id']}.md", case["text"])
        diagnostics = tuple(VerticalListLeadInColonRule().check(RuleContext(document)))
        assert len(diagnostics) == case["expected_diagnostics"], case["case_id"]
        for diagnostic in diagnostics:
            start = diagnostic.location.start_offset
            end = diagnostic.location.end_offset
            assert document.text[start:end] == ".", case["case_id"]
            assert case["expected_replacement"] == ":", case["case_id"]
