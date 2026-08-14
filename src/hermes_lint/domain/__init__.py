"""Contratos de domínio públicos do Hermes."""

from hermes_lint.domain.models import (
    Diagnostic,
    Document,
    RegionKind,
    Rule,
    RuleContext,
    RuleId,
    RuleKind,
    RuleMetadata,
    Sentence,
    Severity,
    SourceLocation,
    SourceReference,
    TextRegion,
    TextSpan,
    Token,
)
from hermes_lint.domain.registry import (
    CatalogMismatchError,
    DuplicateRuleIdError,
    RuleRegistry,
    UnknownRuleIdError,
)

__all__ = [
    "CatalogMismatchError",
    "Diagnostic",
    "Document",
    "DuplicateRuleIdError",
    "RegionKind",
    "Rule",
    "RuleContext",
    "RuleId",
    "RuleKind",
    "RuleMetadata",
    "RuleRegistry",
    "Sentence",
    "Severity",
    "SourceLocation",
    "SourceReference",
    "TextRegion",
    "TextSpan",
    "Token",
    "UnknownRuleIdError",
]
