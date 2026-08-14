#!/usr/bin/env python3
"""Executa uma vez o detector PONT-001 congelado sem consultar labels."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

from hermes_lint.catalog import build_registry
from hermes_lint.domain import RegionKind, RuleContext, RuleId
from hermes_lint.engine import LintEngine
from hermes_lint.parsing import parse_document
from tools.hermes.freeze_pont_001_detector import build_manifest, serialize_manifest

RULE_ID = RuleId("HERMES-PT-PONT-001")
HOLDOUT_MANIFEST = Path("corpus/hermes/pont-001-kubernetes-holdout-manifest-v1.jsonl")
HOLDOUT_MANIFEST_SHA256 = "3eaf4069017593c4f9e0d0c573736899ccbf137e3792ba97161e94d0663f86e7"
DETECTOR_FREEZE = Path("corpus/hermes/pont-001-detector-freeze-v1.json")
DETECTOR_FREEZE_SHA256 = "29bfebaeab126a33d7d0f4aaae44f83d53dd22f03496e30758693d0d9212bae8"
RESULT_NAME = "pont-001-first-execution-v1.json"
RESULT_SCHEMA = "hermes-holdout-execution/v1"


class HoldoutExecutionError(RuntimeError):
    """Impede execução ou materialização que viole o snapshot congelado."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path: Path, expected_sha256: str) -> list[dict[str, object]]:
    payload = path.read_bytes()
    actual = sha256_bytes(payload)
    if actual != expected_sha256:
        raise HoldoutExecutionError(
            f"hash divergente para {path}: esperado {expected_sha256}, obtido {actual}"
        )
    try:
        records = [json.loads(line) for line in payload.decode("utf-8").splitlines()]
    except (UnicodeError, json.JSONDecodeError) as error:
        raise HoldoutExecutionError(f"JSONL inválido em {path}: {error}") from error
    if not records or any(not isinstance(record, dict) for record in records):
        raise HoldoutExecutionError(f"registros inválidos em {path}")
    return records


def verify_detector_freeze(root: Path) -> dict[str, object]:
    freeze_path = root / DETECTOR_FREEZE
    payload = freeze_path.read_bytes()
    actual = sha256_bytes(payload)
    if actual != DETECTOR_FREEZE_SHA256:
        raise HoldoutExecutionError(
            f"manifesto do detector divergente: esperado {DETECTOR_FREEZE_SHA256}, obtido {actual}"
        )
    expected_payload = serialize_manifest(build_manifest(root)).encode("utf-8")
    if payload != expected_payload:
        raise HoldoutExecutionError("fontes atuais divergem do detector congelado")
    freeze = json.loads(payload)
    if not isinstance(freeze, dict) or freeze.get("rule_id") != RULE_ID:
        raise HoldoutExecutionError("manifesto do detector possui contrato inesperado")
    return freeze


def verify_source_snapshot(source_root: Path, header: Mapping[str, object]) -> None:
    expected_commit = _string(header, "source_commit")
    completed = subprocess.run(
        ["git", "-C", str(source_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0 or completed.stdout.strip() != expected_commit:
        raise HoldoutExecutionError("checkout não corresponde ao commit congelado")
    license_path = safe_source_path(source_root, _string(header, "license_path"))
    if sha256_file(license_path) != _string(header, "license_sha256"):
        raise HoldoutExecutionError("licença do checkout diverge do snapshot")


def safe_source_path(source_root: Path, relative_path: str) -> Path:
    if not relative_path or Path(relative_path).is_absolute():
        raise HoldoutExecutionError(f"path de fonte inseguro: {relative_path!r}")
    resolved_root = source_root.resolve()
    candidate = (resolved_root / relative_path).resolve()
    if not candidate.is_relative_to(resolved_root):
        raise HoldoutExecutionError(f"path escapa do snapshot: {relative_path}")
    return candidate


def execute_records(
    source_root: Path,
    records: Sequence[Mapping[str, object]],
    *,
    detector_sha256: str,
    manifest_sha256: str,
) -> dict[str, object]:
    if not records or records[0].get("record_type") != "manifest":
        raise HoldoutExecutionError("cabeçalho do manifesto ausente")
    header = records[0]
    cases = records[1:]
    if any(record.get("rule_id") != RULE_ID for record in records):
        raise HoldoutExecutionError("rule_id inesperado no manifesto")

    case_ids = [_string(record, "case_id") for record in cases]
    if len(case_ids) != len(set(case_ids)):
        raise HoldoutExecutionError("case_id duplicado no manifesto")

    records_by_path: dict[str, list[Mapping[str, object]]] = {}
    for record in cases:
        source_path = _string(record, "source_path")
        records_by_path.setdefault(source_path, []).append(record)

    engine = LintEngine(build_registry())
    diagnostics: list[dict[str, object]] = []
    diagnostic_spans: dict[str, set[tuple[int, int]]] = {}
    lintable_words = 0
    for source_path in sorted(records_by_path):
        path = safe_source_path(source_root, source_path)
        expected_hashes = {
            _string(record, "source_file_sha256") for record in records_by_path[source_path]
        }
        if len(expected_hashes) != 1 or sha256_file(path) not in expected_hashes:
            raise HoldoutExecutionError(f"hash da fonte diverge: {source_path}")
        with path.open("r", encoding="utf-8", newline="") as stream:
            text = stream.read()
        document = parse_document(source_path, text)
        lintable_words += sum(
            token.kind is RegionKind.LINTABLE
            and any(character.isalpha() for character in token.text)
            for token in document.tokens
        )
        emitted = engine.lint(RuleContext(document), enabled_rule_ids=(RULE_ID,))
        spans: set[tuple[int, int]] = set()
        for diagnostic in emitted:
            span = (diagnostic.location.start_offset, diagnostic.location.end_offset)
            if span in spans:
                raise HoldoutExecutionError(f"diagnóstico duplicado em {source_path}:{span[0]}")
            spans.add(span)
            diagnostics.append(
                {
                    "source_path": source_path,
                    "start_offset": span[0],
                    "end_offset": span[1],
                    "rule_id": str(diagnostic.rule_id),
                }
            )
        diagnostic_spans[source_path] = spans

    case_results: list[dict[str, object]] = []
    known_spans: set[tuple[str, int, int]] = set()
    for record in cases:
        record_type = _string(record, "record_type")
        case_id = _string(record, "case_id")
        source_path = _string(record, "source_path")
        spans = diagnostic_spans[source_path]
        if record_type == "literal_semicolon":
            start = _integer(record, "unicode_offset")
            expected_span = (start, start + 1)
            known_spans.add((source_path, *expected_span))
            case_results.append(
                {
                    "case_id": case_id,
                    "record_type": record_type,
                    "source_path": source_path,
                    "start_offset": start,
                    "end_offset": start + 1,
                    "emitted_exact": expected_span in spans,
                }
            )
        elif record_type == "zero_semicolon_control":
            case_results.append(
                {
                    "case_id": case_id,
                    "record_type": record_type,
                    "source_path": source_path,
                    "diagnostic_count": len(spans),
                }
            )
        else:
            raise HoldoutExecutionError(f"record_type inesperado: {record_type}")

    diagnostics.sort(
        key=lambda item: (_string(item, "source_path"), _integer(item, "start_offset"))
    )
    unmatched = [
        diagnostic
        for diagnostic in diagnostics
        if (
            _string(diagnostic, "source_path"),
            _integer(diagnostic, "start_offset"),
            _integer(diagnostic, "end_offset"),
        )
        not in known_spans
    ]
    return {
        "schema_version": RESULT_SCHEMA,
        "rule_id": str(RULE_ID),
        "detector_freeze_sha256": DETECTOR_FREEZE_SHA256,
        "detector_sha256": detector_sha256,
        "holdout_manifest_sha256": manifest_sha256,
        "source_commit": _string(header, "source_commit"),
        "case_count": len(case_results),
        "literal_case_count": sum(
            result["record_type"] == "literal_semicolon" for result in case_results
        ),
        "control_case_count": sum(
            result["record_type"] == "zero_semicolon_control" for result in case_results
        ),
        "diagnostic_count": len(diagnostics),
        "unmatched_diagnostic_count": len(unmatched),
        "lintable_word_count": lintable_words,
        "case_results": case_results,
        "diagnostics": diagnostics,
    }


def canonical_json(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def materialize(output_dir: Path, result: Mapping[str, object]) -> tuple[Path, str]:
    if output_dir.exists():
        raise HoldoutExecutionError(f"diretório de saída já existe: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=output_dir.parent))
    try:
        result_path = temporary / RESULT_NAME
        payload = canonical_json(result)
        result_path.write_bytes(payload)
        digest = sha256_bytes(payload)
        (temporary / f"{RESULT_NAME}.sha256").write_text(
            f"{digest}  {RESULT_NAME}\n", encoding="ascii", newline="\n"
        )
        os.replace(temporary, output_dir)
    except BaseException:
        for child in temporary.iterdir():
            child.unlink(missing_ok=True)
        temporary.rmdir()
        raise
    return output_dir / RESULT_NAME, digest


def _string(record: Mapping[str, object], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str):
        raise HoldoutExecutionError(f"campo {key} não é string")
    return value


def _integer(record: Mapping[str, object], key: str) -> int:
    value = record.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise HoldoutExecutionError(f"campo {key} não é inteiro")
    return value


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    options = parser.parse_args(argv)
    try:
        root = options.root.resolve()
        freeze = verify_detector_freeze(root)
        records = read_jsonl(root / HOLDOUT_MANIFEST, HOLDOUT_MANIFEST_SHA256)
        verify_source_snapshot(options.source_root.resolve(), records[0])
        result = execute_records(
            options.source_root.resolve(),
            records,
            detector_sha256=_string(freeze, "detector_sha256"),
            manifest_sha256=HOLDOUT_MANIFEST_SHA256,
        )
        result_path, digest = materialize(options.output_dir.resolve(), result)
    except (HoldoutExecutionError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"ABORT\t{error}", file=sys.stderr)
        return 2
    print(f"RESULT\t{result_path}")
    print(f"RESULT_SHA256\t{digest}")
    print(f"CASES\t{result['case_count']}")
    print(f"DIAGNOSTICS\t{result['diagnostic_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
