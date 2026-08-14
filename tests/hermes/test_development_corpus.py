import json
from pathlib import Path

from hermes_lint.catalog import build_registry
from hermes_lint.domain import RuleContext, RuleId
from hermes_lint.engine import LintEngine
from hermes_lint.parsing import parse_document


def test_pont_001_matches_every_adjudicated_development_case() -> None:
    corpus = Path("corpus/hermes/pont-001-development-v1.jsonl")
    registry = build_registry()
    engine = LintEngine(registry)
    failures: list[tuple[str, int, int]] = []

    for line in corpus.read_text(encoding="utf-8").splitlines():
        case = json.loads(line)
        expected = case["expected_diagnostics"]
        if expected is None:
            continue
        suffix = "md" if case["source_format"] == "markdown" else "txt"
        document = parse_document(f"{case['case_id']}.{suffix}", case["text"])
        diagnostics = engine.lint(
            RuleContext(document),
            enabled_rule_ids=(RuleId("HERMES-PT-PONT-001"),),
        )
        if len(diagnostics) != expected:
            failures.append((case["case_id"], expected, len(diagnostics)))

    assert failures == []
