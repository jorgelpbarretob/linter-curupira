"""Strict, reproducible rule configuration."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from typing import Literal

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


TextType = Literal["procedural", "descriptive", "procedural-note"]


@dataclass(frozen=True, slots=True)
class NlpConfiguration:
    backend: Literal["spacy"] = "spacy"
    model_package: Literal["en_core_web_sm"] = "en_core_web_sm"
    model_version: Literal["3.8.0"] = "3.8.0"


@dataclass(frozen=True, slots=True)
class ProjectConfiguration:
    rules: RuleOverrides = RuleOverrides()
    text_type: TextType | None = None
    technical_terms: tuple[str, ...] = ()
    vocabulary_path: str | None = None
    nlp: NlpConfiguration | None = None


def parse_project_config(text: str) -> ProjectConfiguration:
    try:
        raw = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise ConfigurationError(f"invalid TOML configuration: {error}") from error

    _reject_unknown_keys(
        raw,
        {"schema_version", "text_type", "rules", "glossary", "vocabulary", "nlp"},
        "configuration",
    )
    schema_version = raw.get("schema_version")
    if type(schema_version) is not int or schema_version != 1:
        raise ConfigurationError("schema_version must be 1")

    raw_rules = raw.get("rules", {})
    if not isinstance(raw_rules, dict):
        raise ConfigurationError("rules must be a TOML table")
    _reject_unknown_keys(raw_rules, {"enable", "disable"}, "rules")
    rules = RuleOverrides(
        enable=_parse_rule_id_array(raw_rules.get("enable", []), "rules.enable"),
        disable=_parse_rule_id_array(raw_rules.get("disable", []), "rules.disable"),
    )

    raw_glossary = raw.get("glossary", {})
    if not isinstance(raw_glossary, dict):
        raise ConfigurationError("glossary must be a TOML table")
    _reject_unknown_keys(raw_glossary, {"terms"}, "glossary")

    raw_vocabulary = raw.get("vocabulary", {})
    if not isinstance(raw_vocabulary, dict):
        raise ConfigurationError("vocabulary must be a TOML table")
    _reject_unknown_keys(raw_vocabulary, {"path"}, "vocabulary")
    nlp = _parse_nlp_configuration(raw.get("nlp"))
    return ProjectConfiguration(
        rules=rules,
        text_type=_parse_text_type(raw.get("text_type")),
        technical_terms=_parse_technical_terms(raw_glossary.get("terms", [])),
        vocabulary_path=_parse_vocabulary_path(raw_vocabulary.get("path")),
        nlp=nlp,
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


def _parse_text_type(value: object) -> TextType | None:
    if value is None:
        return None
    if value not in {"procedural", "descriptive", "procedural-note"}:
        raise ConfigurationError("text_type must be procedural, descriptive, or procedural-note")
    return value  # type: ignore[return-value]


def _parse_technical_terms(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item or item != item.strip() for item in value
    ):
        raise ConfigurationError("glossary.terms must be an array of terms")
    normalized = [item.casefold() for item in value]
    if len(set(normalized)) != len(normalized):
        raise ConfigurationError("glossary.terms must not contain duplicate terms")
    return tuple(value)


def _parse_vocabulary_path(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value or value != value.strip():
        raise ConfigurationError("vocabulary.path must be a non-empty path")
    return value


def _parse_nlp_configuration(value: object) -> NlpConfiguration | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ConfigurationError("nlp must be a TOML table")
    _reject_unknown_keys(value, {"backend", "model_package", "model_version"}, "nlp")
    required = {"backend", "model_package", "model_version"}
    if set(value) != required:
        raise ConfigurationError("nlp requires backend, model_package, and model_version")
    if value["backend"] != "spacy":
        raise ConfigurationError("nlp.backend must be spacy")
    if value["model_package"] != "en_core_web_sm":
        raise ConfigurationError("nlp.model_package must be en_core_web_sm")
    if value["model_version"] != "3.8.0":
        raise ConfigurationError("nlp.model_version must be 3.8.0")
    return NlpConfiguration()


def _validate_known_rule_ids(registry: RuleRegistry, layer: RuleOverrides) -> None:
    for rule_id in (*layer.enable, *layer.disable):
        try:
            registry.get(rule_id)
        except UnknownRuleIdError as error:
            raise ConfigurationError(f"unknown rule_id in configuration: {rule_id}") from error
