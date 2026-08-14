"""Gera o manifesto canônico do detector HERMES-PT-PONT-001."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Sequence
from pathlib import Path

SCHEMA_VERSION = "hermes-detector-freeze/v1"
RULE_ID = "HERMES-PT-PONT-001"
DEVELOPMENT_CORPUS = Path("corpus/hermes/pont-001-development-v1.jsonl")


def build_manifest(root: Path) -> dict[str, object]:
    source_paths = [Path("pyproject.toml"), Path("uv.lock")]
    source_paths.extend(
        path.relative_to(root)
        for path in (root / "src" / "hermes_lint").rglob("*.py")
        if path.is_file()
    )
    entries = [
        {"path": path.as_posix(), "sha256": _sha256(root / path)}
        for path in sorted(source_paths, key=lambda item: item.as_posix())
    ]
    canonical = "".join(f"{entry['path']}\0{entry['sha256']}\n" for entry in entries)
    return {
        "schema_version": SCHEMA_VERSION,
        "rule_id": RULE_ID,
        "implementation_status": "preview",
        "detector_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "development_corpus": {
            "path": DEVELOPMENT_CORPUS.as_posix(),
            "sha256": _sha256(root / DEVELOPMENT_CORPUS),
        },
        "source_files": entries,
    }


def serialize_manifest(manifest: dict[str, object]) -> str:
    return json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args(argv)
    payload = serialize_manifest(build_manifest(arguments.root.resolve()))
    if arguments.output is None:
        print(payload, end="")
    else:
        arguments.output.write_text(payload, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
