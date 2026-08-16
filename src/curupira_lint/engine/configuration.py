"""Configuração estrita e precedência explícita de seleção de regras."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass

from curupira_lint.domain import RuleId, RuleRegistry, UnknownRuleIdError

_LEGACY_RULE_IDS = {
    RuleId("HERMES-PT-PONT-001"): RuleId("CURUPIRA-PT-PONT-001"),
}


class ConfigurationError(ValueError):
    """Indica configuração inválida ou ambígua."""


@dataclass(frozen=True, slots=True)
class RuleOverrides:
    enable: tuple[RuleId, ...] = ()
    disable: tuple[RuleId, ...] = ()

    def __post_init__(self) -> None:
        if len(set(self.enable)) != len(self.enable):
            raise ConfigurationError("IDs habilitados não podem conter duplicatas")
        if len(set(self.disable)) != len(self.disable):
            raise ConfigurationError("IDs desabilitados não podem conter duplicatas")
        conflict = set(self.enable) & set(self.disable)
        if conflict:
            formatted = ", ".join(sorted(conflict, key=str))
            raise ConfigurationError(f"IDs não podem ser habilitados e desabilitados: {formatted}")


@dataclass(frozen=True, slots=True)
class ProjectConfiguration:
    rules: RuleOverrides = RuleOverrides()


def parse_project_config(text: str) -> ProjectConfiguration:
    try:
        raw = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise ConfigurationError(f"TOML inválido: {error}") from error
    _reject_unknown_keys(raw, {"schema_version", "rules"}, "configuração")
    schema_version = raw.get("schema_version")
    if type(schema_version) is not int or schema_version != 1:
        raise ConfigurationError("schema_version deve ser 1")
    raw_rules = raw.get("rules", {})
    if not isinstance(raw_rules, dict):
        raise ConfigurationError("rules deve ser uma tabela TOML")
    _reject_unknown_keys(raw_rules, {"enable", "disable"}, "rules")
    return ProjectConfiguration(
        rules=RuleOverrides(
            enable=_parse_rule_ids(raw_rules.get("enable", []), "rules.enable"),
            disable=_parse_rule_ids(raw_rules.get("disable", []), "rules.disable"),
        )
    )


def resolve_enabled_rule_ids(
    registry: RuleRegistry,
    *,
    project: RuleOverrides | None = None,
    cli: RuleOverrides | None = None,
) -> tuple[RuleId, ...]:
    registry.validate_startup()
    state = {
        rule.metadata.rule_id: rule.metadata.implementation_status == "stable"
        for rule in registry.all()
    }
    for layer in (project or RuleOverrides(), cli or RuleOverrides()):
        _validate_known_rule_ids(registry, layer)
        for rule_id in layer.enable:
            state[rule_id] = True
        for rule_id in layer.disable:
            state[rule_id] = False
    return tuple(
        rule_id
        for rule_id, is_enabled in sorted(state.items(), key=lambda item: str(item[0]))
        if is_enabled
    )


def _reject_unknown_keys(value: dict[str, object], allowed: set[str], context: str) -> None:
    unknown = set(value) - allowed
    if unknown:
        raise ConfigurationError(f"chaves desconhecidas em {context}: {', '.join(sorted(unknown))}")


def _parse_rule_ids(value: object, field: str) -> tuple[RuleId, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ConfigurationError(f"{field} deve ser um array de IDs")
    return tuple(RuleId(item) for item in value)


def _validate_known_rule_ids(registry: RuleRegistry, layer: RuleOverrides) -> None:
    for rule_id in (*layer.enable, *layer.disable):
        if replacement := _LEGACY_RULE_IDS.get(rule_id):
            raise ConfigurationError(f"{rule_id} foi renomeado para {replacement}")
        try:
            registry.get(rule_id)
        except UnknownRuleIdError as error:
            raise ConfigurationError(f"ID desconhecido na configuração: {rule_id}") from error
