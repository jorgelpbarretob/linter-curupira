import hashlib
from pathlib import Path

from tools.curupira.freeze_pont_001_detector import build_manifest, serialize_manifest


def test_detector_freeze_manifest_is_sorted_complete_and_reproducible() -> None:
    root = Path.cwd()
    manifest = build_manifest(root)

    assert manifest == build_manifest(root)
    assert manifest["schema_version"] == "curupira-detector-freeze/v1"
    assert manifest["rule_id"] == "CURUPIRA-PT-PONT-001"
    assert manifest["implementation_status"] == "preview"
    assert manifest["development_corpus"] == {
        "path": "corpus/hermes/pont-001-development-v1.jsonl",
        "sha256": "51f52007848deaae5169171354d900488df9faedbf073a17a48b14d714703bfc",
    }
    paths = [entry["path"] for entry in manifest["source_files"]]
    assert paths == sorted(paths)
    assert "src/curupira_lint/rules/pont_001.py" in paths
    assert all(not path.startswith("src/hermes_lint/") for path in paths)


def test_frozen_detector_manifest_matches_current_sources() -> None:
    root = Path.cwd()
    manifest_path = root / "corpus/curupira/pont-001-detector-freeze-v1.json"
    checksum_path = root / "corpus/curupira/pont-001-detector-freeze-v1.sha256"

    frozen = manifest_path.read_text(encoding="utf-8")
    assert frozen == serialize_manifest(build_manifest(root))
    expected_checksum = hashlib.sha256(frozen.encode("utf-8")).hexdigest()
    assert checksum_path.read_text(encoding="ascii") == (
        f"{expected_checksum}  pont-001-detector-freeze-v1.json\n"
    )
