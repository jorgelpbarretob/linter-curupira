"""Dependency-free command-line composition and operational exit codes."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import replace
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
    BaselineError,
    ConfigurationError,
    InvalidDiagnosticError,
    LintEngine,
    ProjectConfiguration,
    RuleExecutionError,
    RuleOverrides,
    apply_baseline,
    build_baseline,
    parse_baseline,
    parse_project_config,
    resolve_enabled_rule_ids,
    serialize_baseline,
)
from ste_lint.parsing import (
    DocumentTooLargeError,
    UnsupportedFormatError,
    parse_document,
)
from ste_lint.reporting import (
    format_json,
    format_rule_explanation,
    format_rule_list,
    format_text,
)
from ste_lint.vocabulary import (
    Vocabulary,
    VocabularyError,
    import_source_file,
    load_resource_file,
)

EXIT_OK = 0
EXIT_DIAGNOSTICS = 1
EXIT_OPERATIONAL_ERROR = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ste",
        description="Local-first technical English linter.",
    )
    capability_group = parser.add_mutually_exclusive_group()
    capability_group.add_argument(
        "--rules", action="store_true", help="list executable rule metadata"
    )
    capability_group.add_argument(
        "--explain", metavar="RULE_ID", help="explain one executable rule"
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
    lint_parser.add_argument(
        "--vocabulary",
        help="explicit canonical vocabulary resource; overrides project configuration",
    )
    lint_parser.add_argument(
        "--text-type",
        choices=("procedural", "descriptive", "procedural-note"),
        help="explicit text type; overrides the project configuration",
    )
    lint_parser.add_argument("--enable-rule", action="append", default=[], metavar="ID")
    lint_parser.add_argument("--disable-rule", action="append", default=[], metavar="ID")
    baseline_group = lint_parser.add_mutually_exclusive_group()
    baseline_group.add_argument(
        "--baseline", help="suppress diagnostics matching an existing baseline"
    )
    baseline_group.add_argument(
        "--write-baseline", help="atomically write a baseline from current diagnostics"
    )
    vocabulary_parser = subparsers.add_parser(
        "vocabulary",
        help="Manage explicit external vocabulary resources.",
    )
    vocabulary_subparsers = vocabulary_parser.add_subparsers(dest="vocabulary_command")
    import_parser = vocabulary_subparsers.add_parser(
        "import-json",
        help="Import one authorized source JSON into an explicit local cache.",
    )
    import_parser.add_argument("source", help="authorized source JSON")
    import_parser.add_argument("--cache-dir", required=True, help="explicit local cache directory")
    import_parser.add_argument(
        "--confirm-authorized",
        action="store_true",
        help="confirm the right to process this source; does not authorize redistribution",
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    registry: RuleRegistry | None = None,
) -> int:
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
            print(f"ste: operational error: {error}", file=sys.stderr)
            return EXIT_OPERATIONAL_ERROR
        print(format_rule_explanation(rule.metadata), end="")
        return EXIT_OK

    if arguments.command == "lint":
        if arguments.path is None:
            print("No stable rules are available yet.")
            return EXIT_OK
        return _lint(arguments, active_registry)
    if arguments.command == "vocabulary":
        return _vocabulary(arguments)

    parser.print_help()
    return EXIT_OK


def _lint(arguments: argparse.Namespace, registry: RuleRegistry) -> int:
    try:
        project = _load_project_config(arguments.config)
        cli = RuleOverrides(
            enable=tuple(RuleId(value) for value in arguments.enable_rule),
            disable=tuple(RuleId(value) for value in arguments.disable_rule),
        )
        enabled_rule_ids = resolve_enabled_rule_ids(registry, project=project.rules, cli=cli)
        capabilities: dict[str, object] = {}
        vocabulary_path = arguments.vocabulary or project.vocabulary_path
        if vocabulary_path is not None:
            resource = load_resource_file(Path(vocabulary_path))
            capabilities["vocabulary"] = Vocabulary(
                resource,
                technical_terms=project.technical_terms,
            )
        source_text = _read_utf8(Path(arguments.path))
        document = parse_document(arguments.path, source_text)
        text_type = arguments.text_type or project.text_type
        rule_configuration: dict[str, object] = {
            "technical_terms": project.technical_terms,
        }
        if text_type is not None:
            rule_configuration["text_type"] = text_type
        diagnostics = LintEngine(registry).lint(
            RuleContext(document, rule_configuration, capabilities),
            enabled_rule_ids=enabled_rule_ids,
        )
        if arguments.write_baseline is not None:
            baseline = build_baseline(document, diagnostics)
            _write_utf8_atomic(Path(arguments.write_baseline), serialize_baseline(baseline))
            count = len(baseline.fingerprints)
            noun = "fingerprint" if count == 1 else "fingerprints"
            print(f"Wrote baseline with {count} {noun} to {arguments.write_baseline}.")
            return EXIT_OK
        if arguments.baseline is not None:
            baseline = parse_baseline(_read_utf8(Path(arguments.baseline)))
            diagnostics = apply_baseline(document, diagnostics, baseline)
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
        VocabularyError,
    ) as error:
        print(f"ste: operational error: {error}", file=sys.stderr)
        return EXIT_OPERATIONAL_ERROR

    if arguments.format == "json":
        output = format_json(diagnostics)
    else:
        output = format_text(diagnostics, enabled_rule_count=len(enabled_rule_ids))
    print(output, end="")
    return EXIT_DIAGNOSTICS if diagnostics else EXIT_OK


def _load_project_config(path: str | None) -> ProjectConfiguration:
    if path is None:
        return ProjectConfiguration()
    config_path = Path(path)
    configuration = parse_project_config(_read_utf8(config_path))
    if configuration.vocabulary_path is None:
        return configuration
    vocabulary_path = Path(configuration.vocabulary_path)
    if not vocabulary_path.is_absolute():
        vocabulary_path = (config_path.parent / vocabulary_path).resolve()
    return replace(configuration, vocabulary_path=str(vocabulary_path))


def _vocabulary(arguments: argparse.Namespace) -> int:
    if arguments.vocabulary_command != "import-json":
        print("ste: operational error: a vocabulary subcommand is required", file=sys.stderr)
        return EXIT_OPERATIONAL_ERROR
    try:
        target = import_source_file(
            Path(arguments.source),
            Path(arguments.cache_dir),
            confirmed_authorized=arguments.confirm_authorized,
        )
    except (OSError, UnicodeError, VocabularyError) as error:
        print(f"ste: operational error: {error}", file=sys.stderr)
        return EXIT_OPERATIONAL_ERROR
    print(f"Imported authorized vocabulary resource to {target}.")
    return EXIT_OK


def _read_utf8(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return stream.read()


def _write_utf8_atomic(path: Path, text: str) -> None:
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as stream:
            stream.write(text)
            temporary_path = Path(stream.name)
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def entrypoint() -> None:
    raise SystemExit(main())
