from hermes_lint.catalog import build_registry
from hermes_lint.domain import RuleContext, RuleId, Severity
from hermes_lint.engine import LintEngine
from hermes_lint.parsing import parse_document


def test_pont_001_reports_the_exact_semicolon_span_through_the_engine() -> None:
    text = "Feche a válvula; desligue a bomba."
    document = parse_document("procedimento.txt", text)

    diagnostics = LintEngine(build_registry()).lint(
        RuleContext(document),
        enabled_rule_ids=(RuleId("HERMES-PT-PONT-001"),),
    )

    assert len(diagnostics) == 1
    diagnostic = diagnostics[0]
    assert diagnostic.rule_id == "HERMES-PT-PONT-001"
    assert diagnostic.source.standard == "Hermes"
    assert diagnostic.source.issue == "0.1"
    assert diagnostic.source.locator == "Seção 5, HERMES-PT-PONT-001"
    assert diagnostic.severity is Severity.INFO
    assert diagnostic.location.start_offset == text.index(";")
    assert diagnostic.location.end_offset == text.index(";") + 1
    assert diagnostic.suggestion is None


def test_pont_001_keeps_code_and_math_delimiters_from_hiding_visible_prose() -> None:
    text = "Use `$` como símbolo; depois calcule $a;b$."
    document = parse_document("procedimento.md", text)

    diagnostics = LintEngine(build_registry()).lint(
        RuleContext(document),
        enabled_rule_ids=(RuleId("HERMES-PT-PONT-001"),),
    )

    visible_semicolon = text.index(";", text.index("símbolo"))
    assert [diagnostic.location.start_offset for diagnostic in diagnostics] == [visible_semicolon]
