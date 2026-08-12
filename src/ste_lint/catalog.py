"""Executable catalog composition for the current release."""

from ste_lint.domain import RuleMetadata, RuleRegistry
from ste_lint.rules import (
    DescriptiveParagraphLengthRule,
    DescriptiveSentenceLengthRule,
    NoteImperativeRule,
    PassiveVoiceRule,
    ProceduralSentenceLengthRule,
    SemicolonRule,
    VerticalListLeadInColonRule,
)

_RULES = (
    SemicolonRule(),
    ProceduralSentenceLengthRule(),
    DescriptiveSentenceLengthRule(),
    DescriptiveParagraphLengthRule(),
    VerticalListLeadInColonRule(),
    PassiveVoiceRule(),
    NoteImperativeRule(),
)
RULE_CATALOG: tuple[RuleMetadata, ...] = tuple(rule.metadata for rule in _RULES)


def build_registry() -> RuleRegistry:
    registry = RuleRegistry(RULE_CATALOG)
    for rule in _RULES:
        registry.register(rule)
    registry.validate_startup()
    return registry
