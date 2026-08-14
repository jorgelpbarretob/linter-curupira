#!/usr/bin/env python3
"""Prepare an external, detector-blind human-review packet for PONT-001."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_COMMIT = "0dcdb1dda898de2bd4431a898f86c170e109063f"
LICENSE_SHA256 = "9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411"
MANIFEST_SHA256 = "3eaf4069017593c4f9e0d0c573736899ccbf137e3792ba97161e94d0663f86e7"
EXPECTED_OCCURRENCES = 336
EXPECTED_CONTROLS = 73
CONTEXT_RADIUS = 4
PACKET_VERSION = "v2"

CSV_FIELDS = (
    "case_id",
    "record_type",
    "source_path",
    "source_file_sha256",
    "source_format",
    "language",
    "source_license",
    "line",
    "column",
    "unicode_offset",
    "utf8_byte_offset",
    "occurrence_index_in_document",
    "selection_rank",
    "context_first_line",
    "context_last_line",
    "context_sha256",
    "context",
    "domain",
    "truth",
    "structural_region",
    "expected_diagnostics",
    "rationale",
    "review_status",
    "reviewed_by",
    "reviewer_role",
    "reviewed_on",
    "decision_notes",
)

type ManifestRecord = dict[str, Any]
type ReviewRow = dict[str, str]


class AuditError(RuntimeError):
    """Raised when an input diverges from the accepted frozen artifacts."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def ensure_external_output(output_dir: Path) -> None:
    resolved = output_dir.resolve()
    if resolved == PROJECT_ROOT or resolved.is_relative_to(PROJECT_ROOT):
        raise AuditError("human-review content must be written outside the repository")


def verify_source_snapshot(source_root: Path) -> None:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=source_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if commit != SOURCE_COMMIT:
        raise AuditError(f"source commit mismatch: expected {SOURCE_COMMIT}, got {commit}")

    license_digest = sha256_bytes((source_root / "LICENSE").read_bytes())
    if license_digest != LICENSE_SHA256:
        raise AuditError(
            f"license digest mismatch: expected {LICENSE_SHA256}, got {license_digest}"
        )


def load_manifest(manifest_path: Path) -> list[ManifestRecord]:
    payload = manifest_path.read_bytes()
    digest = sha256_bytes(payload)
    if digest != MANIFEST_SHA256:
        raise AuditError(f"manifest digest mismatch: expected {MANIFEST_SHA256}, got {digest}")

    try:
        records = [json.loads(line) for line in payload.decode("utf-8").splitlines()]
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AuditError("manifest is not canonical UTF-8 JSONL") from error

    if not records or records[0].get("record_type") != "manifest":
        raise AuditError("manifest header is missing")
    occurrences = sum(row.get("record_type") == "literal_semicolon" for row in records)
    controls = sum(row.get("record_type") == "zero_semicolon_control" for row in records)
    if occurrences != EXPECTED_OCCURRENCES or controls != EXPECTED_CONTROLS:
        raise AuditError(
            "manifest record count mismatch: "
            f"expected {EXPECTED_OCCURRENCES}/{EXPECTED_CONTROLS}, got {occurrences}/{controls}"
        )
    return records


def source_payload(
    source_root: Path,
    record: ManifestRecord,
    cache: dict[str, tuple[bytes, str]],
) -> tuple[bytes, str]:
    source_path = str(record["source_path"])
    if source_path not in cache:
        payload = (source_root / source_path).read_bytes()
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise AuditError(f"source is not UTF-8: {source_path}") from error
        cache[source_path] = payload, text
    payload, text = cache[source_path]
    digest = sha256_bytes(payload)
    if digest != record["source_file_sha256"]:
        raise AuditError(f"source digest mismatch: {source_path}")
    return payload, text


def line_context(text: str, target_line: int) -> tuple[int, int, str]:
    lines = text.splitlines(keepends=True)
    first_line = max(1, target_line - CONTEXT_RADIUS)
    last_line = min(len(lines), target_line + CONTEXT_RADIUS)
    context = "".join(lines[first_line - 1 : last_line])
    return first_line, last_line, context


def csv_safe(value: str) -> str:
    if value.startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def blank_decision_fields() -> ReviewRow:
    return {
        "domain": "",
        "truth": "",
        "structural_region": "",
        "expected_diagnostics": "",
        "rationale": "",
        "review_status": "pending-human-review",
        "reviewed_by": "",
        "reviewer_role": "",
        "reviewed_on": "",
        "decision_notes": "",
    }


def build_review_rows(source_root: Path, records: list[ManifestRecord]) -> list[ReviewRow]:
    rows: list[ReviewRow] = []
    cache: dict[str, tuple[bytes, str]] = {}

    for record in records[1:]:
        payload, text = source_payload(source_root, record, cache)
        common: ReviewRow = {
            "case_id": str(record["case_id"]),
            "record_type": str(record["record_type"]),
            "source_path": str(record["source_path"]),
            "source_file_sha256": str(record["source_file_sha256"]),
            "source_format": "markdown",
            "language": "pt-BR",
            "source_license": "CC-BY-4.0",
            "line": "",
            "column": "",
            "unicode_offset": "",
            "utf8_byte_offset": "",
            "occurrence_index_in_document": "",
            "selection_rank": "",
            "context_first_line": "",
            "context_last_line": "",
            "context_sha256": "",
            "context": "",
            **blank_decision_fields(),
        }

        if record["record_type"] == "literal_semicolon":
            unicode_offset = int(record["unicode_offset"])
            utf8_byte_offset = int(record["utf8_byte_offset"])
            line = int(record["line"])
            if text[unicode_offset : unicode_offset + 1] != ";":
                raise AuditError(f"target is not a literal semicolon: {record['case_id']}")
            if len(text[:unicode_offset].encode("utf-8")) != utf8_byte_offset:
                raise AuditError(f"UTF-8 offset mismatch: {record['case_id']}")

            first_line, last_line, context = line_context(text, line)
            common.update(
                {
                    "line": str(line),
                    "column": str(record["column"]),
                    "unicode_offset": str(unicode_offset),
                    "utf8_byte_offset": str(utf8_byte_offset),
                    "occurrence_index_in_document": str(record["occurrence_index_in_document"]),
                    "context_first_line": str(first_line),
                    "context_last_line": str(last_line),
                    "context_sha256": sha256_bytes(context.encode("utf-8")),
                    "context": csv_safe(context),
                }
            )
        elif record["record_type"] == "zero_semicolon_control":
            if b";" in payload:
                raise AuditError(f"control contains a literal semicolon: {record['case_id']}")
            common["selection_rank"] = str(record["selection_rank"])
        else:
            raise AuditError(f"unsupported manifest record: {record['record_type']}")
        rows.append(common)

    if len({row["case_id"] for row in rows}) != len(rows):
        raise AuditError("duplicate case_id in review packet")
    return rows


def canonical_csv_bytes(rows: list[ReviewRow]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def packet_readme() -> str:
    return """# Revisão humana — HERMES-PT-PONT-001

Este diretório fica fora do repositório. Não mova o CSV para Git, fixtures,
prompts, wheel ou testes. A revisão deve permanecer cega a qualquer detector.

Use `pont-001-human-review-v2.csv` e confira o arquivo original indicado por
`source_path` no checkout Kubernetes congelado. Para cada ocorrência literal,
preencha `truth` com `violation`, `out_of_scope` ou `ambiguous`. Para cada
controle, use `non_violation`. Preencha também `domain`, `structural_region`,
`expected_diagnostics`, `rationale`, `review_status`, `reviewed_by`,
`reviewer_role` e `reviewed_on`, conforme
`docs/hermes-annotation-guide-v0.1.md`.

Para `ambiguous`, deixe `expected_diagnostics` vazio. Para os demais casos,
use `1` somente em `violation` e `0` em `out_of_scope` ou `non_violation`.
Casos rejeitados continuam no log com `review_status=rejected`.

O campo `context` contém somente uma janela de apoio. O arquivo-fonte é a
autoridade para decidir limites de frontmatter, fences, links e markup.

Depois do preenchimento integral, valide o CSV sem executar o produto:

```text
.venv/bin/python tools/hermes/validate_pont_001_human_review.py \
  /caminho/para/kubernetes-website \
  corpus/hermes/pont-001-kubernetes-holdout-manifest-v1.jsonl \
  /caminho/para/pont-001-human-review-v2.csv
```
"""


def write_packet(output_dir: Path, rows: list[ReviewRow]) -> dict[str, str | int]:
    ensure_external_output(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"pont-001-human-review-{PACKET_VERSION}.csv"
    readme_path = output_dir / "README.md"
    csv_payload = canonical_csv_bytes(rows)
    readme_payload = packet_readme().encode("utf-8")
    if csv_path.exists() and csv_path.read_bytes() != csv_payload:
        raise AuditError("refusing to overwrite an edited human-review CSV")
    csv_path.write_bytes(csv_payload)
    readme_path.write_bytes(readme_payload)

    summary: dict[str, str | int] = {
        "schema_version": "hermes-human-review-packet/v2",
        "source_commit": SOURCE_COMMIT,
        "input_manifest_sha256": MANIFEST_SHA256,
        "case_count": len(rows),
        "literal_semicolon_count": sum(row["record_type"] == "literal_semicolon" for row in rows),
        "control_document_count": sum(
            row["record_type"] == "zero_semicolon_control" for row in rows
        ),
        "review_csv_sha256": sha256_bytes(csv_payload),
        "readme_sha256": sha256_bytes(readme_payload),
    }
    summary_payload = (
        json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    (output_dir / "review-packet-manifest.json").write_bytes(summary_payload)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", type=Path, help="checkout root for kubernetes/website")
    parser.add_argument("manifest", type=Path, help="frozen label-free holdout manifest")
    parser.add_argument("output_dir", type=Path, help="external review directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_root = args.source_root.resolve()
    verify_source_snapshot(source_root)
    records = load_manifest(args.manifest)
    rows = build_review_rows(source_root, records)
    summary = write_packet(args.output_dir, rows)
    print(
        f"wrote {summary['case_count']} pending-review cases; "
        f"csv_sha256={summary['review_csv_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
