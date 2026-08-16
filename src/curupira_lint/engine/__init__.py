"""Execução determinística e seleção das regras Curupira."""

from curupira_lint.engine.baseline import (
    Baseline,
    BaselineError,
    apply_baseline,
    build_baseline,
    parse_baseline,
    serialize_baseline,
)
from curupira_lint.engine.configuration import (
    ConfigurationError,
    ProjectConfiguration,
    RuleOverrides,
    parse_project_config,
    resolve_enabled_rule_ids,
)
from curupira_lint.engine.runner import InvalidDiagnosticError, LintEngine, RuleExecutionError

__all__ = [
    "Baseline",
    "BaselineError",
    "ConfigurationError",
    "InvalidDiagnosticError",
    "LintEngine",
    "ProjectConfiguration",
    "RuleExecutionError",
    "RuleOverrides",
    "apply_baseline",
    "build_baseline",
    "parse_baseline",
    "parse_project_config",
    "resolve_enabled_rule_ids",
    "serialize_baseline",
]
