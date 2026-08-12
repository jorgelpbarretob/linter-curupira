"""Dependency-free command-line composition and operational exit codes."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from ste_lint.catalog import build_registry
from ste_lint.domain import (
    CatalogMismatchError,
    RuleContext,
    RuleId,
    RuleRegistry,
    UnknownRuleIdError,
)
from ste_lint.engine import (
    ConfigurationError,
    InvalidDiagnosticError,
    LintEngine,
    RuleExecutionError,
    RuleOverrides,
    parse_project_config,
    resolve_enabled_rule_ids,
)
from ste_lint.parsing import (
    DocumentTooLargeError,
    UnsupportedFormatError,
    parse_document,
)
from ste_lint.reporting import format_json, format_text

EXIT_OK = 0
EXIT_DIAGNOSTICS = 1
EXIT_OPERATIONAL_ERROR = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ste",
        description="Local-first technical English linter.",
    )
    subparsers = parser.add_subparsers(dest="command")
    lint_parser = subparsers.add_parser(
        "lint",
        help="Lint one TXT or Markdown document.",
        description="Lint one document with the explicitly enabled executable rules.",
    )
    lint_parser.add_argument("path", nargs="?", help="UTF-8 .txt, .md, or .markdown file")
    lint_parser.add_argument("--format", choices=("text", "json"), default="text")
    lint_parser.add_argument("--config", help="explicit project TOML configuration")
    lint_parser.add_argument("--enable-rule", action="append", default=[], metavar="ID")
    lint_parser.add_argument("--disable-rule", action="append", default=[], metavar="ID")
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    registry: RuleRegistry | None = None,
) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)

    if arguments.command == "lint":
        if arguments.path is None:
            print("No stable rules are available yet.")
            return EXIT_OK
        return _lint(arguments, registry or build_registry())

    parser.print_help()
    return EXIT_OK


def _lint(arguments: argparse.Namespace, registry: RuleRegistry) -> int:
    try:
        project = _load_project_config(arguments.config)
        cli = RuleOverrides(
            enable=tuple(RuleId(value) for value in arguments.enable_rule),
            disable=tuple(RuleId(value) for value in arguments.disable_rule),
        )
        enabled_rule_ids = resolve_enabled_rule_ids(registry, project=project, cli=cli)
        source_text = _read_utf8(Path(arguments.path))
        document = parse_document(arguments.path, source_text)
        diagnostics = LintEngine(registry).lint(
            RuleContext(document), enabled_rule_ids=enabled_rule_ids
        )
    except (
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
        print(f"ste: operational error: {error}", file=sys.stderr)
        return EXIT_OPERATIONAL_ERROR

    if arguments.format == "json":
        output = format_json(diagnostics)
    else:
        output = format_text(diagnostics, enabled_rule_count=len(enabled_rule_ids))
    print(output, end="")
    return EXIT_DIAGNOSTICS if diagnostics else EXIT_OK


def _load_project_config(path: str | None) -> RuleOverrides | None:
    if path is None:
        return None
    return parse_project_config(_read_utf8(Path(path)))


def _read_utf8(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return stream.read()


def entrypoint() -> None:
    raise SystemExit(main())
