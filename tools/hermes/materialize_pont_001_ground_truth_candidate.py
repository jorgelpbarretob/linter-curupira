#!/usr/bin/env python3
"""Materialize label-only PONT-001 ground-truth candidate bytes outside Git."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import run_pont_001_grok_review as grok_review

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_SHA256 = "3eaf4069017593c4f9e0d0c573736899ccbf137e3792ba97161e94d0663f86e7"
PROPOSALS_SHA256 = "0f47850e2d8cf44d2019fa516a41d213b06d438e4e646f9236a70ab7e36ed9ce"
SOURCE_REPOSITORY = "https://github.com/kubernetes/website"
SOURCE_COMMIT = "0dcdb1dda898de2bd4431a898f86c170e109063f"
SOURCE_LICENSE = "CC-BY-4.0"
RULE_ID = "HERMES-PT-PONT-001"
OUTPUT_NAME = "pont-001-kubernetes-holdout-ground-truth-v1.jsonl"

type JsonObject = dict[str, Any]


class GroundTruthError(RuntimeError):
    """Raised when frozen inputs or delegated labels are not freeze-ready."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_jsonl(path: Path, expected_sha256: str) -> list[JsonObject]:
    payload = path.read_bytes()
    digest = sha256_bytes(payload)
    if digest != expected_sha256:
        raise GroundTruthError(
            f"digest mismatch for {path.name}: expected {expected_sha256}, got {digest}"
        )
    try:
        return [json.loads(line) for line in payload.decode("utf-8").splitlines()]
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GroundTruthError(f"invalid canonical JSONL: {path.name}") from error


def occurrence_coordinates(record: JsonObject) -> JsonObject:
    return {
        "occurrence_index_in_document": record["occurrence_index_in_document"],
        "unicode_offset": record["unicode_offset"],
        "utf8_byte_offset": record["utf8_byte_offset"],
        "line": record["line"],
        "column": record["column"],
    }


def build_ground_truth_records(
    manifest_records: list[JsonObject],
    proposals: list[JsonObject],
) -> list[JsonObject]:
    units = manifest_records[1:]
    if len(units) != 409 or len(proposals) != len(units):
        raise GroundTruthError("ground-truth inputs must contain exactly 409 aligned units")

    unit_ids = [record["case_id"] for record in units]
    proposal_ids = [record["case_id"] for record in proposals]
    if unit_ids != proposal_ids:
        raise GroundTruthError("manifest/proposal case_id order or bijection mismatch")

    records: list[JsonObject] = []
    for unit, proposal in zip(units, proposals, strict=True):
        grok_review.validate_review(proposal, str(unit["record_type"]))
        if proposal["requires_human"] is True:
            raise GroundTruthError(f"critical case is not adjudicated: {unit['case_id']}")

        unit_coordinates: JsonObject
        if unit["record_type"] == "literal_semicolon":
            unit_coordinates = occurrence_coordinates(unit)
        else:
            unit_coordinates = {
                "selection_rank": unit["selection_rank"],
                "selection_sha256": unit["selection_sha256"],
            }

        records.append(
            {
                "schema_version": "hermes-holdout-ground-truth/v1",
                "case_id": unit["case_id"],
                "rule_id": RULE_ID,
                "partition": "holdout",
                "language": "pt-BR",
                "source_origin": "external-licensed",
                "source_repository": SOURCE_REPOSITORY,
                "source_commit": SOURCE_COMMIT,
                "source_path": unit["source_path"],
                "source_file_sha256": unit["source_file_sha256"],
                "source_license": SOURCE_LICENSE,
                "unit_type": unit["record_type"],
                **unit_coordinates,
                "domain": proposal["domain"],
                "truth": proposal["truth"],
                "structural_region": proposal["structural_region"],
                "expected_diagnostics": proposal["expected_diagnostics"],
                "rationale": proposal["rationale"],
                "review_status": "approved-by-delegated-reviewer",
                "reviewed_by": "grok-4.6-build",
                "reviewer_role": "delegated-external-reviewer",
                "reviewed_on": "2026-08-14",
                "review_proposals_sha256": PROPOSALS_SHA256,
            }
        )
    return records


def canonical_ground_truth_bytes(records: list[JsonObject]) -> bytes:
    forbidden_fields = {"context", "text", "diagnostic", "model_output"}
    for record in records:
        leaked = forbidden_fields.intersection(record)
        if leaked:
            raise GroundTruthError(f"ground truth contains forbidden fields: {sorted(leaked)}")
    lines = [json.dumps(record, ensure_ascii=False, separators=(",", ":")) for record in records]
    return ("\n".join(lines) + "\n").encode("utf-8")


def write_candidate(output_dir: Path, records: list[JsonObject]) -> tuple[Path, str]:
    resolved = output_dir.resolve()
    if resolved == PROJECT_ROOT or resolved.is_relative_to(PROJECT_ROOT):
        raise GroundTruthError("ground truth must remain outside the repository")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise GroundTruthError("refusing to overwrite an existing ground-truth candidate")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / OUTPUT_NAME
    payload = canonical_ground_truth_bytes(records)
    digest = sha256_bytes(payload)
    output_path.write_bytes(payload)
    output_path.with_suffix(".sha256").write_text(
        f"{digest}  {output_path.name}\n",
        encoding="utf-8",
        newline="\n",
    )
    return output_path, digest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="frozen label-free manifest JSONL")
    parser.add_argument("proposals", type=Path, help="validated Grok proposals JSONL")
    parser.add_argument("output_dir", type=Path, help="new external candidate directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = load_jsonl(args.manifest, MANIFEST_SHA256)
    proposals = load_jsonl(args.proposals, PROPOSALS_SHA256)
    records = build_ground_truth_records(manifest, proposals)
    output_path, digest = write_candidate(args.output_dir, records)
    print(f"wrote {len(records)} records to {output_path}; sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
