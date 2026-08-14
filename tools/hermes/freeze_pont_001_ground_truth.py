#!/usr/bin/env python3
"""Freeze the maintainer-approved PONT-001 ground-truth bytes outside Git."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GROUND_TRUTH_NAME = "pont-001-kubernetes-holdout-ground-truth-v1.jsonl"
GROUND_TRUTH_SHA256 = "6cab9e0a4090df19fc5c3cc5a8e93122413160f523e032367ec25849567abab6"


class FreezeError(RuntimeError):
    """Raised when approved bytes diverge or a frozen target already exists."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def ensure_external(path: Path) -> None:
    resolved = path.resolve()
    if resolved == PROJECT_ROOT or resolved.is_relative_to(PROJECT_ROOT):
        raise FreezeError("ground-truth custody must remain outside the repository")


def freeze(candidate_dir: Path, frozen_dir: Path) -> dict[str, str | int]:
    ensure_external(candidate_dir)
    ensure_external(frozen_dir)
    candidate_path = candidate_dir / GROUND_TRUTH_NAME
    payload = candidate_path.read_bytes()
    digest = sha256_bytes(payload)
    if digest != GROUND_TRUTH_SHA256:
        raise FreezeError(
            f"candidate digest mismatch: expected {GROUND_TRUTH_SHA256}, got {digest}"
        )
    if payload.count(b"\n") != 409:
        raise FreezeError("candidate must contain exactly 409 canonical JSONL records")
    if frozen_dir.exists() and any(frozen_dir.iterdir()):
        raise FreezeError("refusing to overwrite an existing frozen ground truth")

    frozen_dir.mkdir(parents=True, exist_ok=True)
    frozen_path = frozen_dir / GROUND_TRUTH_NAME
    frozen_path.write_bytes(payload)
    frozen_path.with_suffix(".sha256").write_text(
        f"{digest}  {frozen_path.name}\n",
        encoding="utf-8",
        newline="\n",
    )
    approval: dict[str, str | int] = {
        "schema_version": "hermes-ground-truth-freeze-approval/v1",
        "rule_id": "HERMES-PT-PONT-001",
        "partition": "holdout",
        "record_count": 409,
        "ground_truth_sha256": digest,
        "approved_by": "project-maintainer",
        "approver_role": "maintainer",
        "approved_on": "2026-08-14",
        "approval_scope": "freeze-exact-ground-truth-bytes",
        "source_candidate": str(candidate_path),
    }
    approval_payload = (
        json.dumps(approval, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    (frozen_dir / "APPROVAL.json").write_bytes(approval_payload)

    if frozen_path.read_bytes() != payload:
        raise FreezeError("frozen bytes differ from approved candidate")
    return approval


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate_dir", type=Path, help="approved candidate directory")
    parser.add_argument("frozen_dir", type=Path, help="new final custody directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    approval = freeze(args.candidate_dir, args.frozen_dir)
    print(json.dumps(approval, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
