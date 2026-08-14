import json

from hermes_lint.catalog import build_registry
from hermes_lint.domain import RuleContext, RuleId
from hermes_lint.engine import LintEngine
from hermes_lint.engine.baseline import apply_baseline, build_baseline, serialize_baseline
from hermes_lint.parsing import parse_document


def test_hermes_baseline_suppresses_by_content_without_storing_text_or_rule_id() -> None:
    document = parse_document("procedimento.txt", "Feche a válvula; desligue a bomba.\n")
    diagnostics = LintEngine(build_registry()).lint(
        RuleContext(document),
        enabled_rule_ids=(RuleId("HERMES-PT-PONT-001"),),
    )

    baseline = build_baseline(document, diagnostics)
    serialized = serialize_baseline(baseline)

    assert apply_baseline(document, diagnostics, baseline) == ()
    assert json.loads(serialized)["schema_version"] == "1.0"
    assert "Feche a válvula" not in serialized
    assert "HERMES-PT-PONT-001" not in serialized
    assert "STE-I9" not in serialized
