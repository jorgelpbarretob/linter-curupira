"""Baseline de diagnósticos baseada em conteúdo, sem armazenar trechos."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass

from hermes_lint.domain import Diagnostic, Document

BASELINE_SCHEMA_VERSION = "1.0"
_FINGERPRINT_VERSION = "1"
_FINGERPRINT = re.compile(r"^sha256:[0-9a-f]{64}$")
_WHITESPACE = re.compile(r"\s+")


class BaselineError(ValueError):
    """Indica baseline fora do contrato estrito."""


@dataclass(frozen=True, slots=True)
class Baseline:
    fingerprints: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if len(set(self.fingerprints)) != len(self.fingerprints):
            raise BaselineError("baseline contém fingerprints duplicados")
        if any(_FINGERPRINT.fullmatch(value) is None for value in self.fingerprints):
            raise BaselineError("baseline contém fingerprint inválido")


def build_baseline(document: Document, diagnostics: Iterable[Diagnostic]) -> Baseline:
    return Baseline(tuple(sorted(set(_fingerprints(document, diagnostics)))))


def apply_baseline(
    document: Document,
    diagnostics: Iterable[Diagnostic],
    baseline: Baseline,
) -> tuple[Diagnostic, ...]:
    ordered = tuple(diagnostics)
    fingerprints = _fingerprints(document, ordered)
    suppressed = set(baseline.fingerprints)
    return tuple(
        diagnostic
        for diagnostic, fingerprint in zip(ordered, fingerprints, strict=True)
        if fingerprint not in suppressed
    )


def serialize_baseline(baseline: Baseline) -> str:
    payload = {
        "schema_version": BASELINE_SCHEMA_VERSION,
        "fingerprints": sorted(baseline.fingerprints),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def parse_baseline(text: str) -> Baseline:
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as error:
        raise BaselineError(f"JSON de baseline inválido: {error}") from error
    if not isinstance(raw, dict):
        raise BaselineError("baseline deve ser um objeto JSON")
    unknown = set(raw) - {"schema_version", "fingerprints"}
    if unknown:
        raise BaselineError(f"chaves desconhecidas: {', '.join(sorted(unknown))}")
    if raw.get("schema_version") != BASELINE_SCHEMA_VERSION:
        raise BaselineError(f"schema_version deve ser {BASELINE_SCHEMA_VERSION}")
    fingerprints = raw.get("fingerprints")
    if not isinstance(fingerprints, list) or any(
        not isinstance(value, str) for value in fingerprints
    ):
        raise BaselineError("fingerprints deve ser um array de strings")
    return Baseline(tuple(sorted(fingerprints)))


def _fingerprints(document: Document, diagnostics: Iterable[Diagnostic]) -> tuple[str, ...]:
    occurrences: dict[str, int] = {}
    result: list[str] = []
    for diagnostic in diagnostics:
        identity = _content_identity(document, diagnostic)
        ordinal = occurrences.get(identity, 0)
        occurrences[identity] = ordinal + 1
        canonical = f"{identity}\nordinal={ordinal}"
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        result.append(f"sha256:{digest}")
    return tuple(result)


def _content_identity(document: Document, diagnostic: Diagnostic) -> str:
    location = diagnostic.location
    span_text = document.text[location.start_offset : location.end_offset]
    context = _context_text(document.text, location.start_offset, location.end_offset)
    uri = location.uri.replace("\\", "/")
    return "\n".join(
        (
            f"algorithm={_FINGERPRINT_VERSION}",
            f"rule_id={diagnostic.rule_id}",
            f"uri={uri}",
            f"span={_collapse_whitespace(span_text)}",
            f"context={_collapse_whitespace(context)}",
        )
    )


def _context_text(text: str, start: int, end: int) -> str:
    context_start = text.rfind("\n", 0, start) + 1
    next_newline = text.find("\n", end)
    context_end = len(text) if next_newline < 0 else next_newline
    return text[context_start:context_end]


def _collapse_whitespace(value: str) -> str:
    return _WHITESPACE.sub(" ", value).strip()
