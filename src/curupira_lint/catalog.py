"""Composição do catálogo executável Curupira."""

from curupira_lint.domain import RuleMetadata, RuleRegistry
from curupira_lint.rules import Pont001Rule

_RULES = (Pont001Rule(),)
RULE_CATALOG: tuple[RuleMetadata, ...] = tuple(rule.metadata for rule in _RULES)


def build_registry() -> RuleRegistry:
    registry = RuleRegistry(RULE_CATALOG)
    for rule in _RULES:
        registry.register(rule)
    registry.validate_startup()
    return registry
