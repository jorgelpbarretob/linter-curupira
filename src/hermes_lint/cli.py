"""Composição da linha de comando Hermes e códigos de saída."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

from hermes_lint.catalog import build_registry
from hermes_lint.domain import (
    CatalogMismatchError,
    RuleContext,
    RuleId,
    RuleRegistry,
    UnknownRuleIdError,
)
from hermes_lint.engine import (
    BaselineError,
    ConfigurationError,
    InvalidDiagnosticError,
    LintEngine,
    RuleExecutionError,
    RuleOverrides,
    apply_baseline,
    build_baseline,
    parse_baseline,
    parse_project_config,
    resolve_enabled_rule_ids,
    serialize_baseline,
)
from hermes_lint.linguistics import (
    LinguisticContractError,
    NlpSetupError,
    analysis_to_dict,
    load_preview_backend,
)
from hermes_lint.parsing import DocumentTooLargeError, UnsupportedFormatError, parse_document
from hermes_lint.reporting import (
    format_json,
    format_rule_explanation,
    format_rule_list,
    format_text,
)

EXIT_OK = 0
EXIT_DIAGNOSTICS = 1
EXIT_OPERATIONAL_ERROR = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hermes",
        description="Linter local de português técnico brasileiro.",
    )
    capability_group = parser.add_mutually_exclusive_group()
    capability_group.add_argument("--rules", action="store_true", help="lista regras executáveis")
    capability_group.add_argument("--explain", metavar="RULE_ID", help="explica uma regra")
    subparsers = parser.add_subparsers(dest="command")
    lint_parser = subparsers.add_parser("lint", help="analisa um documento TXT ou Markdown")
    lint_parser.add_argument("path", nargs="?", help="arquivo UTF-8 .txt, .md ou .markdown")
    lint_parser.add_argument("--format", choices=("text", "json"), default="text")
    lint_parser.add_argument("--config", help="configuração TOML explícita do projeto")
    lint_parser.add_argument("--enable-rule", action="append", default=[], metavar="ID")
    lint_parser.add_argument("--disable-rule", action="append", default=[], metavar="ID")
    baseline_group = lint_parser.add_mutually_exclusive_group()
    baseline_group.add_argument("--baseline", help="suprime diagnósticos de uma baseline")
    baseline_group.add_argument("--write-baseline", help="grava uma baseline atomicamente")
    analyze_parser = subparsers.add_parser(
        "analyze", help="expõe análise linguística local pt-BR (preview)"
    )
    analyze_parser.add_argument("path", help="arquivo UTF-8 .txt")
    analyze_parser.add_argument("--format", choices=("json",), default="json")
    return parser


def main(argv: Sequence[str] | None = None, *, registry: RuleRegistry | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    active_registry = registry or build_registry()
    if arguments.rules:
        print(format_rule_list(active_registry.all()), end="")
        return EXIT_OK
    if arguments.explain is not None:
        try:
            rule = active_registry.get(RuleId(arguments.explain))
        except UnknownRuleIdError as error:
            print(f"hermes: erro operacional: {error}", file=sys.stderr)
            return EXIT_OPERATIONAL_ERROR
        print(format_rule_explanation(rule.metadata), end="")
        return EXIT_OK
    if arguments.command == "lint":
        if arguments.path is None:
            print("Nenhuma regra estável está disponível.")
            return EXIT_OK
        return _lint(arguments, active_registry)
    if arguments.command == "analyze":
        return _analyze(arguments)
    parser.print_help()
    return EXIT_OK


def _lint(arguments: argparse.Namespace, registry: RuleRegistry) -> int:
    try:
        project_rules = RuleOverrides()
        if arguments.config is not None:
            config_path = Path(arguments.config)
            project_rules = parse_project_config(_read_utf8(config_path)).rules
        cli_rules = RuleOverrides(
            enable=tuple(RuleId(value) for value in arguments.enable_rule),
            disable=tuple(RuleId(value) for value in arguments.disable_rule),
        )
        enabled = resolve_enabled_rule_ids(registry, project=project_rules, cli=cli_rules)
        path = Path(arguments.path)
        document = parse_document(str(path), _read_utf8(path))
        diagnostics = LintEngine(registry).lint(RuleContext(document), enabled_rule_ids=enabled)
        if arguments.write_baseline is not None:
            written_baseline = build_baseline(document, diagnostics)
            baseline_text = serialize_baseline(written_baseline)
            _write_utf8_atomic(Path(arguments.write_baseline), baseline_text)
            count = len(written_baseline.fingerprints)
            print(f"Baseline gravada com {count} fingerprint(s) em {arguments.write_baseline}.")
            return EXIT_OK
        elif arguments.baseline is not None:
            baseline = parse_baseline(_read_utf8(Path(arguments.baseline)))
            diagnostics = apply_baseline(document, diagnostics, baseline)
        output = (
            format_json(diagnostics)
            if arguments.format == "json"
            else format_text(diagnostics, enabled_rule_count=len(enabled))
        )
        print(output, end="")
        return EXIT_DIAGNOSTICS if diagnostics else EXIT_OK
    except (
        BaselineError,
        CatalogMismatchError,
        ConfigurationError,
        DocumentTooLargeError,
        InvalidDiagnosticError,
        OSError,
        RuleExecutionError,
        UnicodeError,
        UnknownRuleIdError,
        UnsupportedFormatError,
    ) as error:
        print(f"hermes: erro operacional: {error}", file=sys.stderr)
        return EXIT_OPERATIONAL_ERROR


def _analyze(arguments: argparse.Namespace) -> int:
    try:
        path = Path(arguments.path)
        if path.suffix.lower() != ".txt":
            raise UnsupportedFormatError("análise linguística preview aceita somente arquivos .txt")
        document = parse_document(str(path), _read_utf8(path))
        analysis = load_preview_backend().analyze(document.text)
        payload = {
            "schema_version": "hermes-linguistic-analysis/v1",
            "status": "preview",
            "source": {
                "uri": str(path),
                "sha256": hashlib.sha256(document.text.encode("utf-8")).hexdigest(),
            },
            "analysis": analysis_to_dict(analysis),
            "metrics": {
                "source_characters": len(document.text),
                "source_utf8_bytes": len(document.text.encode("utf-8")),
                "surface_tokens": len(analysis.surface_tokens),
                "syntactic_words": len(analysis.words),
                "sentences": len(analysis.sentences),
            },
        }
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return EXIT_OK
    except (
        DocumentTooLargeError,
        LinguisticContractError,
        NlpSetupError,
        OSError,
        UnicodeError,
        UnsupportedFormatError,
    ) as error:
        print(f"hermes: erro operacional: {error}", file=sys.stderr)
        return EXIT_OPERATIONAL_ERROR


def _read_utf8(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return stream.read()


def _write_utf8_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(text)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = temporary.name
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and os.path.exists(temporary_path):
            os.unlink(temporary_path)


def entrypoint() -> None:
    raise SystemExit(main())
