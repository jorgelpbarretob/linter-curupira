#!/usr/bin/env python3
"""Generate the frozen, label-free PONT-001 Kubernetes holdout manifest.

The manifest contains only provenance, paths, hashes, source coordinates and
deterministic selection metadata. It never copies source text, assigns labels
or imports/executes product code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "hermes-holdout-manifest/v1"
MANIFEST_ID = "pont-001-kubernetes-ptbr-holdout-v1"
RULE_ID = "HERMES-PT-PONT-001"
SOURCE_REPOSITORY = "https://github.com/kubernetes/website"
SOURCE_COMMIT = "0dcdb1dda898de2bd4431a898f86c170e109063f"
SOURCE_PREFIX = Path("content/pt-br")
SOURCE_LICENSE = "CC-BY-4.0"
SOURCE_ATTRIBUTION = "The Kubernetes Authors"
LICENSE_PATH = Path("LICENSE")
LICENSE_SHA256 = "9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411"
EXCLUDED_EXACT = Path("docs/sitemap.md")
EXCLUDED_PREFIX = Path("docs/reference/setup-tools/kubeadm/generated")
CONTROL_COUNT = 73
EXPECTED_MARKDOWN_FILES = 368
EXPECTED_ELIGIBLE_FILES = 326
EXPECTED_OCCURRENCE_FILES = 90
EXPECTED_OCCURRENCES = 336

FORBIDDEN_FIELDS = frozenset(
    {
        "diagnostic",
        "expected_diagnostics",
        "label",
        "rationale",
        "review_status",
        "text",
        "truth",
    }
)

type JsonValue = str | int | list[str]
type Record = dict[str, JsonValue]


class AuditError(RuntimeError):
    """Raised when the approved snapshot or preregistered counts diverge."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def repository_path(relative_path: Path) -> str:
    return (SOURCE_PREFIX / relative_path).as_posix()


def is_excluded(relative_path: Path) -> bool:
    return relative_path == EXCLUDED_EXACT or relative_path.is_relative_to(EXCLUDED_PREFIX)


def selection_key(source_path: str, source_commit: str = SOURCE_COMMIT) -> str:
    payload = source_commit.encode("ascii") + b"\0" + source_path.encode("utf-8")
    return sha256_bytes(payload)


def offset_to_position(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    line_start = text.rfind("\n", 0, offset) + 1
    return line, offset - line_start + 1


def eligible_documents(source_root: Path) -> tuple[list[Path], int]:
    localized_root = source_root / SOURCE_PREFIX
    markdown_files = sorted(path for path in localized_root.rglob("*.md") if path.is_file())
    eligible = [
        path for path in markdown_files if not is_excluded(path.relative_to(localized_root))
    ]
    return eligible, len(markdown_files)


def build_manifest_records(
    source_root: Path,
    *,
    control_count: int = CONTROL_COUNT,
) -> list[Record]:
    documents, markdown_count = eligible_documents(source_root)
    occurrence_rows: list[dict[str, Any]] = []
    control_rows: list[dict[str, str]] = []
    occurrence_file_count = 0

    for path in documents:
        payload = path.read_bytes()
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise AuditError(f"source is not UTF-8: {path}") from error

        relative_path = path.relative_to(source_root / SOURCE_PREFIX)
        source_path = repository_path(relative_path)
        file_sha256 = sha256_bytes(payload)
        offsets = [index for index, character in enumerate(text) if character == ";"]

        if not offsets:
            control_rows.append(
                {
                    "source_path": source_path,
                    "source_file_sha256": file_sha256,
                    "selection_sha256": selection_key(source_path),
                }
            )
            continue

        occurrence_file_count += 1
        for ordinal, unicode_offset in enumerate(offsets, start=1):
            line, column = offset_to_position(text, unicode_offset)
            occurrence_rows.append(
                {
                    "source_path": source_path,
                    "source_file_sha256": file_sha256,
                    "occurrence_index_in_document": ordinal,
                    "unicode_offset": unicode_offset,
                    "utf8_byte_offset": len(text[:unicode_offset].encode("utf-8")),
                    "line": line,
                    "column": column,
                }
            )

    occurrence_rows.sort(key=lambda row: (row["source_path"], row["unicode_offset"]))
    selected_controls = sorted(control_rows, key=lambda row: row["selection_sha256"])[
        :control_count
    ]

    header: Record = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "manifest",
        "manifest_id": MANIFEST_ID,
        "rule_id": RULE_ID,
        "partition": "holdout",
        "language": "pt-BR",
        "source_repository": SOURCE_REPOSITORY,
        "source_commit": SOURCE_COMMIT,
        "source_prefix": SOURCE_PREFIX.as_posix(),
        "source_license": SOURCE_LICENSE,
        "source_attribution": SOURCE_ATTRIBUTION,
        "license_path": LICENSE_PATH.as_posix(),
        "license_sha256": LICENSE_SHA256,
        "excluded_paths": [
            repository_path(EXCLUDED_EXACT),
            f"{repository_path(EXCLUDED_PREFIX)}/**",
        ],
        "control_selection_formula": (
            'sha256(source_commit + "\\0" + repository_relative_path_utf8)'
        ),
        "markdown_file_count": markdown_count,
        "eligible_file_count": len(documents),
        "occurrence_file_count": occurrence_file_count,
        "literal_semicolon_count": len(occurrence_rows),
        "control_document_count": len(selected_controls),
    }

    records: list[Record] = [header]
    for index, row in enumerate(occurrence_rows, start=1):
        records.append(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "literal_semicolon",
                "case_id": f"pont-holdout-occ-{index:04d}",
                "rule_id": RULE_ID,
                "partition": "holdout",
                **row,
            }
        )
    for index, row in enumerate(selected_controls, start=1):
        records.append(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "zero_semicolon_control",
                "case_id": f"pont-holdout-ctl-{index:03d}",
                "rule_id": RULE_ID,
                "partition": "holdout",
                "selection_rank": index,
                **row,
            }
        )
    return records


def canonical_manifest_bytes(records: list[Record]) -> bytes:
    for record in records:
        forbidden = FORBIDDEN_FIELDS.intersection(record)
        if forbidden:
            names = ", ".join(sorted(forbidden))
            raise AuditError(f"manifest contains forbidden label/content fields: {names}")
    lines = [json.dumps(record, ensure_ascii=False, separators=(",", ":")) for record in records]
    return ("\n".join(lines) + "\n").encode("utf-8")


def verify_snapshot(source_root: Path) -> None:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=source_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if commit != SOURCE_COMMIT:
        raise AuditError(f"source commit mismatch: expected {SOURCE_COMMIT}, got {commit}")

    license_path = source_root / LICENSE_PATH
    license_digest = sha256_bytes(license_path.read_bytes())
    if license_digest != LICENSE_SHA256:
        raise AuditError(
            f"license digest mismatch: expected {LICENSE_SHA256}, got {license_digest}"
        )


def verify_preregistered_counts(records: list[Record]) -> None:
    header = records[0]
    expected = {
        "markdown_file_count": EXPECTED_MARKDOWN_FILES,
        "eligible_file_count": EXPECTED_ELIGIBLE_FILES,
        "occurrence_file_count": EXPECTED_OCCURRENCE_FILES,
        "literal_semicolon_count": EXPECTED_OCCURRENCES,
        "control_document_count": CONTROL_COUNT,
    }
    mismatches = [
        f"{field}: expected {value}, got {header[field]}"
        for field, value in expected.items()
        if header[field] != value
    ]
    if mismatches:
        raise AuditError("preregistered count mismatch: " + "; ".join(mismatches))


def write_manifest(records: list[Record], output_path: Path) -> str:
    payload = canonical_manifest_bytes(records)
    digest = sha256_bytes(payload)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(payload)
    output_path.with_suffix(".sha256").write_text(
        f"{digest}  {output_path.name}\n",
        encoding="utf-8",
        newline="\n",
    )
    return digest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", type=Path, help="checkout root for kubernetes/website")
    parser.add_argument("output", type=Path, help="destination .jsonl manifest")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_root = args.source_root.resolve()
    verify_snapshot(source_root)
    records = build_manifest_records(source_root)
    verify_preregistered_counts(records)
    digest = write_manifest(records, args.output)
    print(f"wrote {len(records)} records; sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
