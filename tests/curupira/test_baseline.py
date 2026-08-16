import json

from curupira_lint.catalog import build_registry
from curupira_lint.domain import RuleContext, RuleId
from curupira_lint.engine import LintEngine
from curupira_lint.engine.baseline import apply_baseline, build_baseline, serialize_baseline
from curupira_lint.parsing import parse_document
from hermes_lint.catalog import build_registry as build_hermes_registry
from hermes_lint.domain import RuleContext as HermesRuleContext
from hermes_lint.domain import RuleId as HermesRuleId
from hermes_lint.engine import LintEngine as HermesLintEngine
from hermes_lint.engine.baseline import build_baseline as build_hermes_baseline
from hermes_lint.parsing import parse_document as parse_hermes_document


def test_curupira_baseline_suppresses_by_content_without_storing_text_or_rule_id() -> None:
    document = parse_document("procedimento.txt", "Feche a válvula; desligue a bomba.\n")
    diagnostics = LintEngine(build_registry()).lint(
        RuleContext(document),
        enabled_rule_ids=(RuleId("CURUPIRA-PT-PONT-001"),),
    )

    baseline = build_baseline(document, diagnostics)
    serialized = serialize_baseline(baseline)

    assert apply_baseline(document, diagnostics, baseline) == ()
    assert json.loads(serialized)["schema_version"] == "1.0"
    assert "Feche a válvula" not in serialized
    assert "CURUPIRA-PT-PONT-001" not in serialized
    assert "STE-I9" not in serialized


def test_historical_hermes_baseline_does_not_suppress_curupira_diagnostic() -> None:
    text = "Feche a válvula; desligue a bomba.\n"
    hermes_document = parse_hermes_document("procedimento.txt", text)
    hermes_diagnostics = HermesLintEngine(build_hermes_registry()).lint(
        HermesRuleContext(hermes_document),
        enabled_rule_ids=(HermesRuleId("HERMES-PT-PONT-001"),),
    )
    historical_baseline = build_hermes_baseline(hermes_document, hermes_diagnostics)

    document = parse_document("procedimento.txt", text)
    diagnostics = LintEngine(build_registry()).lint(
        RuleContext(document),
        enabled_rule_ids=(RuleId("CURUPIRA-PT-PONT-001"),),
    )

    assert apply_baseline(document, diagnostics, historical_baseline) == diagnostics
