#!/usr/bin/env python3
"""Audit PT4 corpora against declared candidate training sources without inference."""

from __future__ import annotations

import argparse
import bz2
import hashlib
import json
import subprocess
import unicodedata
from pathlib import Path
from typing import Any

PETROGOLD_COMMIT = "83ca567418405fdae830a3e5be55c29b6ed80a24"
BOSQUE_COMMIT = "625982f781b64ac793b3a818968ea9fc6ee5a8af"
PROPOSAL_SHA256 = "b0c21e03b8fa2f0e13e51927362819bbc77abc831a9aef3fcff580e30d15a438"
WIKINER_FILE_ID = 9446356
WIKINER_SIZE = 6059022
WIKINER_MD5 = "d74198c00ab91078747ee4a49aff5332"
WIKINER_SHA256 = "d34a73ca46ebae6c83db1f4d8057406e6ceed5a7ea579407c3b35120274c48d4"
WIKINER_METADATA_SHA256 = "eb3f2311604c6011bec33424a3b07329340ea2aa84a4c1efc5eeac016fe02d6f"


class AuditError(RuntimeError):
    """Raised when an input is not the expected frozen artifact."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def md5_file(path: Path) -> str:
    return hashlib.md5(path.read_bytes(), usedforsecurity=False).hexdigest()


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


def wikiner_texts(path: Path) -> list[str]:
    if path.stat().st_size != WIKINER_SIZE:
        raise AuditError("WikiNER archive size mismatch")
    if md5_file(path) != WIKINER_MD5 or sha256_file(path) != WIKINER_SHA256:
        raise AuditError("WikiNER archive digest mismatch")
    sentences: list[str] = []
    try:
        with bz2.open(path, mode="rt", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                fields = line.split()
                try:
                    forms = [field.rsplit("|", maxsplit=2)[0] for field in fields]
                except ValueError as error:
                    raise AuditError(f"invalid WikiNER token at line {line_number}") from error
                if any(field.count("|") < 2 for field in fields):
                    raise AuditError(f"invalid WikiNER token at line {line_number}")
                sentences.append(" ".join(forms))
    except (OSError, UnicodeDecodeError) as error:
        raise AuditError("WikiNER archive cannot be decoded") from error
    return sentences


def verify_wikiner_metadata(path: Path) -> dict[str, Any]:
    if sha256_file(path) != WIKINER_METADATA_SHA256:
        raise AuditError("WikiNER metadata digest mismatch")
    article = json.loads(path.read_text(encoding="utf-8"))
    selected = [file for file in article["files"] if file["id"] == WIKINER_FILE_ID]
    if len(selected) != 1:
        raise AuditError("WikiNER Portuguese file metadata is missing")
    file = selected[0]
    expected = {
        "name": "aij-wikiner-pt-wp3.bz2",
        "size": WIKINER_SIZE,
        "supplied_md5": WIKINER_MD5,
    }
    if any(file.get(key) != value for key, value in expected.items()):
        raise AuditError("WikiNER Portuguese file metadata diverged")
    if article.get("version") != 1 or article.get("license", {}).get("name") != "CC BY 4.0":
        raise AuditError("WikiNER version or license diverged")
    return article


def normalized(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).casefold().split())


def normalized_without_whitespace(text: str) -> str:
    return "".join(unicodedata.normalize("NFC", text).casefold().split())


def overlap(left: list[str], right: list[str]) -> dict[str, int]:
    return {
        "exact": len(set(left) & set(right)),
        "nfc_casefold_whitespace": len(
            {normalized(text) for text in left} & {normalized(text) for text in right}
        ),
        "nfc_casefold_remove_whitespace": len(
            {normalized_without_whitespace(text) for text in left}
            & {normalized_without_whitespace(text) for text in right}
        ),
    }


def audit(
    petrogold_root: Path,
    bosque_root: Path,
    wikiner_root: Path,
    proposal_path: Path,
) -> dict[str, Any]:
    verify_commit(petrogold_root, PETROGOLD_COMMIT)
    verify_commit(bosque_root, BOSQUE_COMMIT)
    petrogold_path = petrogold_root / "pt_petrogold-ud-test.conllu"
    bosque_paths = sorted(bosque_root.glob("pt_bosque-ud-*.conllu"))
    if len(bosque_paths) != 3:
        raise AuditError(f"expected 3 Bosque splits, got {len(bosque_paths)}")

    petrogold = conllu_texts(petrogold_path)
    bosque = [text for path in bosque_paths for text in conllu_texts(path)]
    wikiner_path = wikiner_root / "aij-wikiner-pt-wp3.bz2"
    metadata_path = wikiner_root / "figshare-article-5462500-v1.json"
    wikiner_metadata = verify_wikiner_metadata(metadata_path)
    wikiner = wikiner_texts(wikiner_path)
    proposal = proposal_texts(proposal_path)
    comparisons = {
        "petrogold_test_vs_bosque_r2_8": overlap(petrogold, bosque),
        "offset_proposal_vs_bosque_r2_8": overlap(proposal, bosque),
        "offset_proposal_vs_petrogold_test": overlap(proposal, petrogold),
        "petrogold_test_vs_wikiner_pt_wp3": overlap(petrogold, wikiner),
        "offset_proposal_vs_wikiner_pt_wp3": overlap(proposal, wikiner),
    }
    if any(value for result in comparisons.values() for value in result.values()):
        raise AuditError("material exact or normalized overlap detected")

    return {
        "schema_version": "hermes-pt4-contamination-audit/v1",
        "status": "pass",
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
            "wikiner": {
                "article_id": wikiner_metadata["id"],
                "doi": wikiner_metadata["doi"],
                "version": wikiner_metadata["version"],
                "license": wikiner_metadata["license"]["name"],
                "file_id": WIKINER_FILE_ID,
                "file_name": wikiner_path.name,
                "bytes": WIKINER_SIZE,
                "md5": WIKINER_MD5,
                "sha256": WIKINER_SHA256,
                "metadata_sha256": WIKINER_METADATA_SHA256,
                "sentence_count": len(wikiner),
            },
        },
        "normalization": [
            "exact reconstructed sentence",
            "Unicode NFC, casefold, collapse whitespace",
            "Unicode NFC, casefold, remove whitespace",
        ],
        "comparisons": comparisons,
        "unresolved": [],
        "wikiner_ner_enabled_in_bakeoff": False,
        "candidate_outputs_observed": False,
        "pont_001_data_used": False,
        "inference_authorized": False,
        "remaining_gate": "independent-human-review-of-160-offset-cases",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("petrogold_root", type=Path)
    parser.add_argument("bosque_root", type=Path)
    parser.add_argument("wikiner_root", type=Path)
    parser.add_argument("proposal", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = audit(args.petrogold_root, args.bosque_root, args.wikiner_root, args.proposal)
    payload = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8", newline="\n")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
