"""Strict, reproducible rule configuration."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass

from ste_lint.domain import RuleId, RuleRegistry, UnknownRuleIdError


class ConfigurationError(ValueError):
    """Raised when configuration cannot be validated atomically."""


@dataclass(frozen=True, slots=True)
class RuleOverrides:
    enable: tuple[RuleId, ...] = ()
    disable: tuple[RuleId, ...] = ()

    def __post_init__(self) -> None:
        if len(set(self.enable)) != len(self.enable):
            raise ConfigurationError("enabled rule IDs must not contain duplicates")
        if len(set(self.disable)) != len(self.disable):
            raise ConfigurationError("disabled rule IDs must not contain duplicates")
        conflict = set(self.enable) & set(self.disable)
        if conflict:
            formatted = ", ".join(sorted(conflict, key=str))
            raise ConfigurationError(f"rule IDs cannot be both enabled and disabled: {formatted}")


def parse_project_config(text: str) -> RuleOverrides:
    try:
        raw = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise ConfigurationError(f"invalid TOML configuration: {error}") from error

    _reject_unknown_keys(raw, {"schema_version", "rules"}, "configuration")
    schema_version = raw.get("schema_version")
    if type(schema_version) is not int or schema_version != 1:
        raise ConfigurationError("schema_version must be 1")

    raw_rules = raw.get("rules", {})
    if not isinstance(raw_rules, dict):
        raise ConfigurationError("rules must be a TOML table")
    _reject_unknown_keys(raw_rules, {"enable", "disable"}, "rules")
    return RuleOverrides(
        enable=_parse_rule_id_array(raw_rules.get("enable", []), "rules.enable"),
        disable=_parse_rule_id_array(raw_rules.get("disable", []), "rules.disable"),
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
        formatted = ", ".join(sorted(unknown))
        raise ConfigurationError(f"unknown {context} keys: {formatted}")


def _parse_rule_id_array(value: object, field: str) -> tuple[RuleId, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ConfigurationError(f"{field} must be an array of rule IDs")
    return tuple(RuleId(item) for item in value)


def _validate_known_rule_ids(registry: RuleRegistry, layer: RuleOverrides) -> None:
    for rule_id in (*layer.enable, *layer.disable):
        try:
            registry.get(rule_id)
        except UnknownRuleIdError as error:
            raise ConfigurationError(f"unknown rule_id in configuration: {rule_id}") from error
