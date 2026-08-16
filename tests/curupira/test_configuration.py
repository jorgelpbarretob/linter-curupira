import pytest

from curupira_lint.catalog import build_registry
from curupira_lint.domain import RuleId
from curupira_lint.engine import (
    ConfigurationError,
    RuleOverrides,
    parse_project_config,
    resolve_enabled_rule_ids,
)


@pytest.mark.parametrize(
    "text",
    [
        "schema_version = 2\n",
        "schema_version = true\n",
        "schema_version = 1\nunknown = true\n",
        "schema_version = 1\n[rules]\nunknown = []\n",
        "schema_version = 1\n[rules]\nenable = 'bad'\n",
    ],
)
def test_curupira_configuration_rejects_noncanonical_input(text: str) -> None:
    with pytest.raises(ConfigurationError):
        parse_project_config(text)


def test_preview_rule_is_disabled_by_default_and_can_be_enabled_explicitly() -> None:
    registry = build_registry()

    assert resolve_enabled_rule_ids(registry) == ()
    assert resolve_enabled_rule_ids(
        registry,
        project=RuleOverrides(enable=(RuleId("CURUPIRA-PT-PONT-001"),)),
    ) == (RuleId("CURUPIRA-PT-PONT-001"),)


def test_curupira_configuration_rejects_unknown_and_legacy_ids() -> None:
    registry = build_registry()

    for rule_id in (RuleId("CURUPIRA-PT-UNKNOWN-999"), RuleId("HERMES-PT-PONT-001")):
        with pytest.raises(ConfigurationError):
            resolve_enabled_rule_ids(registry, project=RuleOverrides(enable=(rule_id,)))
