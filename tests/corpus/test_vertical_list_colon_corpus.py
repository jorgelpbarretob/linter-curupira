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
