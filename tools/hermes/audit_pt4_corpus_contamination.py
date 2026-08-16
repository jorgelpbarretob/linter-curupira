#!/usr/bin/env python3
"""Audit PT4 corpora against declared candidate training sources without inference."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import unicodedata
from pathlib import Path
from typing import Any

PETROGOLD_COMMIT = "83ca567418405fdae830a3e5be55c29b6ed80a24"
BOSQUE_COMMIT = "625982f781b64ac793b3a818968ea9fc6ee5a8af"
PROPOSAL_SHA256 = "b0c21e03b8fa2f0e13e51927362819bbc77abc831a9aef3fcff580e30d15a438"


class AuditError(RuntimeError):
    """Raised when an input is not the expected frozen artifact."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_commit(root: Path, expected: str) -> None:
    actual = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if actual != expected:
        raise AuditError(f"commit mismatch for {root}: expected {expected}, got {actual}")


def conllu_texts(path: Path) -> list[str]:
    return [
        line.removeprefix("# text = ").rstrip("\n")
        for line in path.open(encoding="utf-8")
        if line.startswith("# text = ")
    ]


def proposal_texts(path: Path) -> list[str]:
    if sha256_file(path) != PROPOSAL_SHA256:
        raise AuditError("offset proposal digest mismatch")
    try:
        return [json.loads(line)["text"] for line in path.open(encoding="utf-8")]
    except (json.JSONDecodeError, KeyError) as error:
        raise AuditError("offset proposal is not canonical JSONL") from error


def normalized(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).casefold().split())


def overlap(left: list[str], right: list[str]) -> dict[str, int]:
    return {
        "exact": len(set(left) & set(right)),
        "nfc_casefold_whitespace": len(
            {normalized(text) for text in left} & {normalized(text) for text in right}
        ),
    }


def audit(petrogold_root: Path, bosque_root: Path, proposal_path: Path) -> dict[str, Any]:
    verify_commit(petrogold_root, PETROGOLD_COMMIT)
    verify_commit(bosque_root, BOSQUE_COMMIT)
    petrogold_path = petrogold_root / "pt_petrogold-ud-test.conllu"
    bosque_paths = sorted(bosque_root.glob("pt_bosque-ud-*.conllu"))
    if len(bosque_paths) != 3:
        raise AuditError(f"expected 3 Bosque splits, got {len(bosque_paths)}")

    petrogold = conllu_texts(petrogold_path)
    bosque = [text for path in bosque_paths for text in conllu_texts(path)]
    proposal = proposal_texts(proposal_path)
    comparisons = {
        "petrogold_test_vs_bosque_r2_8": overlap(petrogold, bosque),
        "offset_proposal_vs_bosque_r2_8": overlap(proposal, bosque),
        "offset_proposal_vs_petrogold_test": overlap(proposal, petrogold),
    }
    if any(value for result in comparisons.values() for value in result.values()):
        raise AuditError("material exact or normalized overlap detected")

    return {
        "schema_version": "hermes-pt4-contamination-audit/v1",
        "status": "conditional-pass-wikiner-pending",
        "checked_on": "2026-08-16",
        "inputs": {
            "petrogold": {
                "release": "r2.18",
                "commit": PETROGOLD_COMMIT,
                "sentence_count": len(petrogold),
                "test_sha256": sha256_file(petrogold_path),
            },
            "bosque": {
                "release": "r2.8",
                "commit": BOSQUE_COMMIT,
                "sentence_count": len(bosque),
                "split_sha256": {path.name: sha256_file(path) for path in bosque_paths},
            },
            "offset_proposal": {
                "case_count": len(proposal),
                "sha256": PROPOSAL_SHA256,
            },
        },
        "normalization": "Unicode NFC, casefold, collapse whitespace",
        "comparisons": comparisons,
        "unresolved": [
            {
                "source": "WikiNER",
                "declared_use": "named-entity recognition training source",
                "ner_enabled_in_bakeoff": False,
                "snapshot_compared": False,
                "required_before_inference": (
                    "freeze and compare an immutable snapshot, or establish from model "
                    "provenance that excluded components cannot carry WikiNER influence"
                ),
            }
        ],
        "candidate_outputs_observed": False,
        "pont_001_data_used": False,
        "inference_authorized": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("petrogold_root", type=Path)
    parser.add_argument("bosque_root", type=Path)
    parser.add_argument("proposal", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = audit(args.petrogold_root, args.bosque_root, args.proposal)
    payload = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8", newline="\n")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
