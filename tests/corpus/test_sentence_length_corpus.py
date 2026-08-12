import json
from pathlib import Path

import pytest

from ste_lint.domain import Rule, RuleContext
from ste_lint.parsing import parse_document
from ste_lint.rules.sentence_length import (
    DescriptiveSentenceLengthRule,
    ProceduralSentenceLengthRule,
)


@pytest.mark.parametrize(
    ("filename", "rule"),
    [
        ("procedural-sentence-length.jsonl", ProceduralSentenceLengthRule()),
        ("descriptive-sentence-length.jsonl", DescriptiveSentenceLengthRule()),
    ],
)
def test_sentence_length_rules_match_human_approved_seed_labels(filename: str, rule: Rule) -> None:
    cases = [
        json.loads(line)
        for line in Path("corpus/seed", filename).read_text(encoding="utf-8").splitlines()
    ]

    assert len(cases) == 13
    assert all(case["review_status"] == "approved" for case in cases)
    for case in cases:
        suffix = "md" if case["source_format"] == "markdown" else "txt"
        document = parse_document(f"{case['case_id']}.{suffix}", case["text"])
        context = RuleContext(document, {"text_type": case["text_type"]})
        diagnostics = tuple(rule.check(context))
        assert len(diagnostics) == case["expected_diagnostics"], case["case_id"]
