"""Deterministic registry for rule contracts and diagnostic provenance."""

from __future__ import annotations

import re
from collections.abc import Iterable

from ste_lint.domain.models import (
    Diagnostic,
    Rule,
    RuleId,
    RuleKind,
    RuleMetadata,
    Severity,
)

_STE_RULE_ID = re.compile(r"^STE-I9-[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d{3}$")
_PROJECT_RULE_ID = re.compile(r"^PROJECT-[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d{3}$")
_SEVERITY_RANK = {
    Severity.INFO: 0,
    Severity.WARNING: 1,
    Severity.ERROR: 2,
}


class DuplicateRuleIdError(ValueError):
    """Raised when two rules claim the same stable identity."""


class UnknownRuleIdError(LookupError):
    """Raised when a diagnostic refers to an unregistered rule."""


class CatalogMismatchError(ValueError):
    """Raised when runtime output diverges from registered metadata."""


class RuleRegistry:
    def __init__(self, catalog: Iterable[RuleMetadata]) -> None:
        self._catalog: dict[RuleId, RuleMetadata] = {}
        self._rules: dict[RuleId, Rule] = {}
        for metadata in catalog:
            self._validate_catalog_metadata(metadata)
            if metadata.rule_id in self._catalog:
                raise DuplicateRuleIdError(f"duplicate catalog rule_id: {metadata.rule_id}")
            self._catalog[metadata.rule_id] = metadata

    def register(self, rule: Rule) -> None:
        rule_id = rule.metadata.rule_id
        try:
            catalog_metadata = self._catalog[rule_id]
        except KeyError as error:
            raise CatalogMismatchError(
                f"rule_id {rule_id} is not present in the catalog"
            ) from error
        if rule.metadata != catalog_metadata:
            raise CatalogMismatchError(
                f"implementation metadata differs from the catalog for {rule_id}"
            )
        if catalog_metadata.implementation_status == "planned":
            raise CatalogMismatchError(f"planned rule {rule_id} cannot be executable")
        if catalog_metadata.kind is RuleKind.HUMAN_REVIEW:
            raise CatalogMismatchError(f"human-review rule {rule_id} cannot be executable")
        if rule_id in self._rules:
            raise DuplicateRuleIdError(f"duplicate rule_id: {rule_id}")
        self._rules[rule_id] = rule

    def all(self) -> tuple[Rule, ...]:
        return tuple(self._rules[rule_id] for rule_id in sorted(self._rules, key=str))

    def get(self, rule_id: RuleId) -> Rule:
        try:
            return self._rules[rule_id]
        except KeyError as error:
            raise UnknownRuleIdError(f"unknown executable rule_id: {rule_id}") from error

    def validate_startup(self) -> None:
        missing = [
            rule_id
            for rule_id, metadata in self._catalog.items()
            if metadata.implementation_status in {"preview", "stable"}
            and metadata.kind is not RuleKind.HUMAN_REVIEW
            and rule_id not in self._rules
        ]
        if missing:
            formatted = ", ".join(str(rule_id) for rule_id in sorted(missing, key=str))
            raise CatalogMismatchError(f"missing implementation for catalog rules: {formatted}")

    def validate_diagnostic(self, diagnostic: Diagnostic) -> None:
        try:
            metadata = self._rules[diagnostic.rule_id].metadata
        except KeyError as error:
            raise UnknownRuleIdError(f"unknown rule_id: {diagnostic.rule_id}") from error

        if diagnostic.source != metadata.source:
            raise CatalogMismatchError(
                f"diagnostic source differs from registered source for {diagnostic.rule_id}"
            )
        if metadata.kind is RuleKind.SEMANTIC and diagnostic.severity is not Severity.INFO:
            raise CatalogMismatchError("semantic diagnostics cannot exceed info severity")
        if metadata.implementation_status == "preview" and diagnostic.severity is not Severity.INFO:
            raise CatalogMismatchError("preview diagnostics cannot exceed info severity")
        if _SEVERITY_RANK[diagnostic.severity] > _SEVERITY_RANK[metadata.default_severity]:
            raise CatalogMismatchError(
                f"diagnostic severity exceeds the catalog default for {diagnostic.rule_id}"
            )

    @staticmethod
    def _validate_catalog_metadata(metadata: RuleMetadata) -> None:
        rule_id = str(metadata.rule_id)
        if _STE_RULE_ID.fullmatch(rule_id):
            if metadata.source.standard != "ASD-STE100" or metadata.source.issue != "9":
                raise CatalogMismatchError(
                    f"STE-I9 rule {rule_id} must reference ASD-STE100 Issue 9"
                )
            if metadata.source.locator.upper() == "TBD":
                raise CatalogMismatchError(f"STE-I9 rule {rule_id} requires a verified locator")
            return
        if _PROJECT_RULE_ID.fullmatch(rule_id):
            if metadata.source.standard != "PROJECT":
                raise CatalogMismatchError(
                    f"PROJECT rule {rule_id} must use the PROJECT source namespace"
                )
            return
        raise CatalogMismatchError(f"invalid rule_id namespace or format: {rule_id}")
