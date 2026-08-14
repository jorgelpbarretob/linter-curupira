"""Apresentação determinística no limite da aplicação."""

from __future__ import annotations

import json
from collections.abc import Iterable

from hermes_lint.domain import Diagnostic

JSON_SCHEMA_VERSION = "1.0"


def format_json(diagnostics: Iterable[Diagnostic]) -> str:
    payload = {
        "schema_version": JSON_SCHEMA_VERSION,
        "diagnostics": [_diagnostic_to_json(item) for item in _ordered(diagnostics)],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def format_text(diagnostics: Iterable[Diagnostic], *, enabled_rule_count: int) -> str:
    ordered = _ordered(diagnostics)
    if not ordered:
        if enabled_rule_count == 0:
            return "Nenhuma regra executável está habilitada.\n"
        return "Nenhuma violação foi detectada pelas regras habilitadas.\n"
    blocks: list[str] = []
    for item in ordered:
        location = item.location
        lines = [
            (
                f"{location.uri}:{location.start_line}:{location.start_column} "
                f"{item.severity.value} {item.rule_id}"
            ),
            f"  span: [{location.start_offset}, {location.end_offset})",
            f"  fonte: {item.source.standard} {item.source.issue}, {item.source.locator}",
            f"  mensagem: {item.message}",
            f"  explicação: {item.explanation}",
        ]
        if item.suggestion is not None:
            lines.append(f"  sugestão: {item.suggestion}")
        if item.evidence is not None:
            lines.append(f"  evidência: {item.evidence}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + "\n"


def _ordered(diagnostics: Iterable[Diagnostic]) -> tuple[Diagnostic, ...]:
    return tuple(
        sorted(
            diagnostics,
            key=lambda item: (
                item.location.uri,
                item.location.start_offset,
                item.location.end_offset,
                str(item.rule_id),
            ),
        )
    )


def _diagnostic_to_json(diagnostic: Diagnostic) -> dict[str, object]:
    source = diagnostic.source
    location = diagnostic.location
    return {
        "rule_id": str(diagnostic.rule_id),
        "source": {
            "standard": source.standard,
            "issue": source.issue,
            "locator": source.locator,
        },
        "severity": diagnostic.severity.value,
        "location": {
            "uri": location.uri,
            "start_offset": location.start_offset,
            "end_offset": location.end_offset,
            "start_line": location.start_line,
            "start_column": location.start_column,
            "end_line": location.end_line,
            "end_column": location.end_column,
        },
        "message": diagnostic.message,
        "explanation": diagnostic.explanation,
        "suggestion": diagnostic.suggestion,
        "evidence": diagnostic.evidence,
    }
