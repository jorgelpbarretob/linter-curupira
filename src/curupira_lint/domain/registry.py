"""Registry determinístico do catálogo autoral Curupira."""

from __future__ import annotations

import re
from collections.abc import Iterable

from curupira_lint.domain.models import Diagnostic, Rule, RuleId, RuleKind, RuleMetadata, Severity

_CURUPIRA_RULE_ID = re.compile(r"^CURUPIRA-PT-[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d{3}$")
_LEGACY_RULE_IDS = {
    RuleId("HERMES-PT-PONT-001"): RuleId("CURUPIRA-PT-PONT-001"),
}
_SEVERITY_RANK = {Severity.INFO: 0, Severity.WARNING: 1, Severity.ERROR: 2}


class DuplicateRuleIdError(ValueError):
    """Indica duas regras com a mesma identidade estável."""


class UnknownRuleIdError(LookupError):
    """Indica referência a uma regra executável desconhecida."""


class CatalogMismatchError(ValueError):
    """Indica divergência entre catálogo, implementação e diagnóstico."""


class RuleRegistry:
    def __init__(self, catalog: Iterable[RuleMetadata]) -> None:
        self._catalog: dict[RuleId, RuleMetadata] = {}
        self._rules: dict[RuleId, Rule] = {}
        for metadata in catalog:
            self._validate_catalog_metadata(metadata)
            if metadata.rule_id in self._catalog:
                raise DuplicateRuleIdError(f"ID duplicado no catálogo: {metadata.rule_id}")
            self._catalog[metadata.rule_id] = metadata

    def register(self, rule: Rule) -> None:
        rule_id = rule.metadata.rule_id
        try:
            catalog_metadata = self._catalog[rule_id]
        except KeyError as error:
            raise CatalogMismatchError(f"ID {rule_id} ausente do catálogo") from error
        if rule.metadata != catalog_metadata:
            raise CatalogMismatchError(f"metadados divergentes para {rule_id}")
        if catalog_metadata.implementation_status == "planned":
            raise CatalogMismatchError(f"regra planejada {rule_id} não pode ser executável")
        if catalog_metadata.kind is RuleKind.HUMAN_REVIEW:
            raise CatalogMismatchError(f"regra de revisão humana {rule_id} não pode ser executável")
        if rule_id in self._rules:
            raise DuplicateRuleIdError(f"ID duplicado: {rule_id}")
        self._rules[rule_id] = rule

    def all(self) -> tuple[Rule, ...]:
        return tuple(self._rules[rule_id] for rule_id in sorted(self._rules, key=str))

    def get(self, rule_id: RuleId) -> Rule:
        if replacement := _LEGACY_RULE_IDS.get(rule_id):
            raise UnknownRuleIdError(f"{rule_id} foi renomeado para {replacement}")
        try:
            return self._rules[rule_id]
        except KeyError as error:
            raise UnknownRuleIdError(f"ID de regra executável desconhecido: {rule_id}") from error

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
            raise CatalogMismatchError(f"implementação ausente: {formatted}")

    def validate_diagnostic(self, diagnostic: Diagnostic) -> None:
        try:
            metadata = self._rules[diagnostic.rule_id].metadata
        except KeyError as error:
            raise UnknownRuleIdError(f"ID de regra desconhecido: {diagnostic.rule_id}") from error
        if diagnostic.source != metadata.source:
            raise CatalogMismatchError(f"fonte divergente para {diagnostic.rule_id}")
        if metadata.kind is RuleKind.SEMANTIC and diagnostic.severity is not Severity.INFO:
            raise CatalogMismatchError("diagnóstico semântico não pode exceder severidade info")
        if metadata.implementation_status == "preview" and diagnostic.severity is not Severity.INFO:
            raise CatalogMismatchError("diagnóstico preview não pode exceder severidade info")
        if _SEVERITY_RANK[diagnostic.severity] > _SEVERITY_RANK[metadata.default_severity]:
            raise CatalogMismatchError("severidade excede o padrão do catálogo")

    @staticmethod
    def _validate_catalog_metadata(metadata: RuleMetadata) -> None:
        rule_id = str(metadata.rule_id)
        if _CURUPIRA_RULE_ID.fullmatch(rule_id) is None:
            raise CatalogMismatchError(f"namespace ou formato de ID inválido: {rule_id}")
        if metadata.source.standard != "Curupira" or metadata.source.issue != "0.1":
            raise CatalogMismatchError(f"regra Curupira {rule_id} exige fonte Curupira 0.1")
        if metadata.source.locator.upper() == "TBD":
            raise CatalogMismatchError(f"regra Curupira {rule_id} exige locator autoral")
