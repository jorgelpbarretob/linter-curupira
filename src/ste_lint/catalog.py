"""Executable catalog composition for the current release."""

from ste_lint.domain import RuleMetadata, RuleRegistry

# Phase 3 publishes the strict catalog mechanism but no executable normative rule.
# Candidate IDs remain unfrozen until their individual Phase 4 increments.
RULE_CATALOG: tuple[RuleMetadata, ...] = ()


def build_registry() -> RuleRegistry:
    registry = RuleRegistry(RULE_CATALOG)
    registry.validate_startup()
    return registry
