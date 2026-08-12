from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

import pytest

from ste_lint.domain import (
    Diagnostic,
    RuleContext,
    RuleId,
    RuleKind,
    RuleMetadata,
    RuleRegistry,
    Severity,
    SourceReference,
)
from ste_lint.engine import (
    ConfigurationError,
    NlpConfiguration,
    ProjectConfiguration,
    RuleOverrides,
    parse_project_config,
    resolve_enabled_rule_ids,
)


def metadata(rule_id: str, *, status: Literal["preview", "stable"] = "stable") -> RuleMetadata:
    return RuleMetadata(
        rule_id=RuleId(rule_id),
        title="Synthetic project rule",
        source=SourceReference(standard="PROJECT", issue="1", locator="local-test"),
        kind=RuleKind.DETERMINISTIC,
        default_severity=Severity.WARNING,
        summary="A synthetic configuration test.",
        implementation_status=status,
    )


@dataclass(frozen=True)
class StubRule:
    metadata: RuleMetadata

    def check(self, context: RuleContext) -> Iterable[Diagnostic]:
        del context
        return ()


def registry_with(*entries: RuleMetadata) -> RuleRegistry:
    registry = RuleRegistry(entries)
    for entry in entries:
        registry.register(StubRule(entry))
    registry.validate_startup()
    return registry


def test_project_config_parses_strict_toml_contract() -> None:
    configuration = parse_project_config(
        "schema_version = 1\n"
        'text_type = "procedural"\n'
        "[rules]\n"
        'enable = ["PROJECT-TEST-001"]\n'
        "disable = []\n"
        "[glossary]\n"
        'terms = ["bleed-air valve", "ZX-4 controller"]\n'
        "[vocabulary]\n"
        'path = ".ste-lint/vocabulary.json"\n'
        "[nlp]\n"
        'backend = "spacy"\n'
        'model_package = "en_core_web_sm"\n'
        'model_version = "3.8.0"\n'
    )

    assert configuration == ProjectConfiguration(
        rules=RuleOverrides(enable=(RuleId("PROJECT-TEST-001"),)),
        text_type="procedural",
        technical_terms=("bleed-air valve", "ZX-4 controller"),
        vocabulary_path=".ste-lint/vocabulary.json",
        nlp=NlpConfiguration(),
    )


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("schema_version = 2\n", "schema_version"),
        ("schema_version = true\n", "schema_version"),
        ("schema_version = 1\nunknown = true\n", "unknown configuration keys"),
        ("schema_version = 1\n[rules]\nother = []\n", "unknown rules keys"),
        ("schema_version = 1\n[rules]\nenable = 'bad'\n", "array of rule IDs"),
        ('schema_version = 1\ntext_type = "automatic"\n', "text_type"),
        ("schema_version = 1\n[glossary]\nterms = 'bad'\n", "array of terms"),
        ("schema_version = 1\n[vocabulary]\npath = ''\n", "vocabulary.path"),
        ("schema_version = 1\n[vocabulary]\nunknown = 'bad'\n", "unknown vocabulary"),
        ("schema_version = 1\n[nlp]\nunknown = 'bad'\n", "unknown nlp"),
        (
            "schema_version = 1\n[nlp]\n"
            'backend = "other"\nmodel_package = "en_core_web_sm"\nmodel_version = "3.8.0"\n',
            "nlp.backend",
        ),
        (
            "schema_version = 1\n[nlp]\n"
            'backend = "spacy"\nmodel_package = "en_core_web_sm"\nmodel_version = "latest"\n',
            "nlp.model_version",
        ),
        (
            'schema_version = 1\n[nlp]\nbackend = "spacy"\n',
            "requires backend, model_package, and model_version",
        ),
        (
            'schema_version = 1\n[glossary]\nterms = ["Bleed-air valve", "bleed-air valve"]\n',
            "duplicate",
        ),
        (
            "schema_version = 1\n[rules]\n"
            'enable = ["PROJECT-TEST-001"]\n'
            'disable = ["PROJECT-TEST-001"]\n',
            "both enabled and disabled",
        ),
    ],
)
def test_project_config_rejects_invalid_or_ambiguous_input(text: str, message: str) -> None:
    with pytest.raises(ConfigurationError, match=message):
        parse_project_config(text)


def test_stable_rules_are_enabled_and_preview_rules_are_disabled_by_default() -> None:
    stable = metadata("PROJECT-TEST-001")
    preview = metadata("PROJECT-TEST-002", status="preview")

    enabled = resolve_enabled_rule_ids(registry_with(stable, preview))

    assert enabled == (stable.rule_id,)


def test_cli_overrides_project_file_rule_selection() -> None:
    stable = metadata("PROJECT-TEST-001")
    preview = metadata("PROJECT-TEST-002", status="preview")
    project = RuleOverrides(enable=(preview.rule_id,), disable=(stable.rule_id,))
    cli = RuleOverrides(enable=(stable.rule_id,), disable=(preview.rule_id,))

    enabled = resolve_enabled_rule_ids(registry_with(stable, preview), project=project, cli=cli)

    assert enabled == (stable.rule_id,)


def test_unknown_rule_id_fails_before_execution() -> None:
    stable = metadata("PROJECT-TEST-001")

    with pytest.raises(ConfigurationError, match="unknown rule_id"):
        resolve_enabled_rule_ids(
            registry_with(stable),
            cli=RuleOverrides(enable=(RuleId("PROJECT-UNKNOWN-999"),)),
        )
