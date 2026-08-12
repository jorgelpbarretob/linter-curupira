"""Explicit local cache I/O for authorized vocabulary imports."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from ste_lint.vocabulary.loader import (
    MAX_RESOURCE_BYTES,
    VocabularyError,
    import_source,
    parse_resource,
    serialize_resource,
)
from ste_lint.vocabulary.models import VocabularyResource


def import_source_file(
    source_path: Path,
    cache_dir: Path,
    *,
    confirmed_authorized: bool,
) -> Path:
    if not confirmed_authorized:
        raise VocabularyError("vocabulary import requires --confirm-authorized")
    raw = _read_limited(source_path, label="vocabulary source")
    resource = import_source(raw)
    resolved_cache = cache_dir.resolve()
    resolved_cache.mkdir(parents=True, exist_ok=True)
    target = resolved_cache / f"{resource.provenance.source_sha256}.json"
    _write_atomic(target, serialize_resource(resource))
    return target


def load_resource_file(path: Path) -> VocabularyResource:
    raw = _read_limited(path, label="vocabulary resource")
    return parse_resource(raw)


def _read_limited(path: Path, *, label: str) -> bytes:
    try:
        with path.open("rb") as stream:
            raw = stream.read(MAX_RESOURCE_BYTES + 1)
    except OSError as error:
        detail = error.strerror or str(error)
        raise VocabularyError(f"cannot read {label} {path}: {detail}") from error
    if len(raw) > MAX_RESOURCE_BYTES:
        raise VocabularyError(f"{label} {path} exceeds the 16 MiB limit")
    return raw


def _write_atomic(path: Path, raw: bytes) -> None:
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "wb",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as stream:
            stream.write(raw)
            temporary_path = Path(stream.name)
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
