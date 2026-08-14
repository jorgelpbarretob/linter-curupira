"""Composição do catálogo executável Hermes."""

from hermes_lint.domain import RuleMetadata, RuleRegistry
from hermes_lint.rules import Pont001Rule

_RULES = (Pont001Rule(),)
RULE_CATALOG: tuple[RuleMetadata, ...] = tuple(rule.metadata for rule in _RULES)


def build_registry() -> RuleRegistry:
    registry = RuleRegistry(RULE_CATALOG)
    for rule in _RULES:
        registry.register(rule)
    registry.validate_startup()
    return registry
