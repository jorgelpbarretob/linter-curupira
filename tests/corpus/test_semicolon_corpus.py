import json
from pathlib import Path

from ste_lint.domain import RuleContext
from ste_lint.parsing import parse_document
from ste_lint.rules.semicolon import SemicolonRule


def test_semicolon_rule_matches_all_human_approved_seed_labels() -> None:
    cases = [
        json.loads(line)
        for line in Path("corpus/seed/semicolon.jsonl").read_text(encoding="utf-8").splitlines()
    ]

    assert len(cases) == 13
    assert all(case["review_status"] == "approved" for case in cases)
    for case in cases:
        suffix = "md" if case["source_format"] == "markdown" else "txt"
        document = parse_document(f"{case['case_id']}.{suffix}", case["text"])
        diagnostics = tuple(SemicolonRule().check(RuleContext(document)))
        assert len(diagnostics) == case["expected_diagnostics"], case["case_id"]
