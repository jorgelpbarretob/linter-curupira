"""Registra e compara execuções A/B do Curupira no Hermes Agent."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from curupira_lint.catalog import build_registry
from curupira_lint.domain import RuleContext, RuleId
from curupira_lint.engine import LintEngine
from curupira_lint.parsing import parse_document

SCHEMA_RUN = "curupira-hermes-agent-run/v1"
SCHEMA_COMPARISON = "curupira-hermes-agent-comparison/v1"


def build_run(
    *,
    condition: str,
    usage_path: Path,
    output_path: Path,
    elapsed_seconds: float,
    hermes_agent_version: str,
) -> dict[str, Any]:
    usage_source = _load_object(usage_path)
    usage = {
        key: usage_source[key]
        for key in (
            "input_tokens",
            "output_tokens",
            "total_tokens",
            "api_calls",
            "model",
            "provider",
        )
    }
    output = output_path.read_text(encoding="utf-8")
    document = parse_document(output_path.name, output)
    diagnostics = LintEngine(build_registry()).lint(
        RuleContext(document),
        enabled_rule_ids=(RuleId("CURUPIRA-PT-PONT-001"),),
    )
    return {
        "schema_version": SCHEMA_RUN,
        "condition": condition,
        "hermes_agent_version": hermes_agent_version,
        "usage": usage,
        "elapsed_seconds": elapsed_seconds,
        "residual_findings": len(diagnostics),
    }


def build_comparison(baseline_path: Path, treatment_path: Path) -> dict[str, Any]:
    baseline = _load_run(baseline_path, "baseline")
    treatment = _load_run(treatment_path, "curupira")
    deltas = {
        "total_tokens": treatment["usage"]["total_tokens"] - baseline["usage"]["total_tokens"],
        "api_calls": treatment["usage"]["api_calls"] - baseline["usage"]["api_calls"],
        "elapsed_seconds": round(treatment["elapsed_seconds"] - baseline["elapsed_seconds"], 3),
        "residual_findings": treatment["residual_findings"] - baseline["residual_findings"],
    }
    return {
        "schema_version": SCHEMA_COMPARISON,
        "baseline": baseline,
        "curupira": treatment,
        "deltas": deltas,
        "interpretation": {
            "token_reduction_observed": deltas["total_tokens"] < 0,
            "residual_finding_reduction_observed": deltas["residual_findings"] < 0,
        },
    }


def _load_run(path: Path, expected_condition: str) -> dict[str, Any]:
    run = _load_object(path)
    if run.get("schema_version") != SCHEMA_RUN:
        raise ValueError(f"schema inválido em {path}")
    if run.get("condition") != expected_condition:
        raise ValueError(f"condição esperada {expected_condition} em {path}")
    return run


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"objeto JSON esperado em {path}")
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    record = commands.add_parser("record")
    record.add_argument("--condition", choices=("baseline", "curupira"), required=True)
    record.add_argument("--usage", type=Path, required=True)
    record.add_argument("--output-document", type=Path, required=True)
    record.add_argument("--elapsed-seconds", type=float, required=True)
    record.add_argument("--hermes-agent-version", required=True)
    record.add_argument("--output", type=Path, required=True)

    compare = commands.add_parser("compare")
    compare.add_argument("--baseline", type=Path, required=True)
    compare.add_argument("--curupira", type=Path, required=True)
    compare.add_argument("--output", type=Path, required=True)

    arguments = parser.parse_args(argv)
    if arguments.command == "record":
        value = build_run(
            condition=arguments.condition,
            usage_path=arguments.usage,
            output_path=arguments.output_document,
            elapsed_seconds=arguments.elapsed_seconds,
            hermes_agent_version=arguments.hermes_agent_version,
        )
    else:
        value = build_comparison(arguments.baseline, arguments.curupira)
    _write_json(arguments.output, value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
