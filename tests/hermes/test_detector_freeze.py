import hashlib
from pathlib import Path

from tools.hermes.freeze_pont_001_detector import build_manifest, serialize_manifest


def test_detector_freeze_manifest_is_sorted_complete_and_reproducible() -> None:
    root = Path.cwd()

    first = build_manifest(root)
    second = build_manifest(root)

    assert first == second
    assert first["schema_version"] == "hermes-detector-freeze/v1"
    assert first["rule_id"] == "HERMES-PT-PONT-001"
    paths = [entry["path"] for entry in first["source_files"]]
    assert paths == sorted(paths)
    assert "pyproject.toml" in paths
    assert "uv.lock" in paths
    assert "src/hermes_lint/rules/pont_001.py" in paths
    assert all("ste_lint" not in path for path in paths)

    canonical = "".join(f"{entry['path']}\0{entry['sha256']}\n" for entry in first["source_files"])
    assert first["detector_sha256"] == hashlib.sha256(canonical.encode()).hexdigest()


def test_frozen_detector_manifest_matches_current_sources() -> None:
    root = Path.cwd()
    manifest_path = root / "corpus/hermes/pont-001-detector-freeze-v3.json"
    checksum_path = root / "corpus/hermes/pont-001-detector-freeze-v3.sha256"

    frozen = manifest_path.read_text(encoding="utf-8")
    assert frozen == serialize_manifest(build_manifest(root))

    expected_checksum, expected_name = checksum_path.read_text(encoding="ascii").split()
    assert expected_name == manifest_path.name
    assert hashlib.sha256(frozen.encode("utf-8")).hexdigest() == expected_checksum
