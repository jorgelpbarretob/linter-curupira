from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

FREEZER_PATH = Path(__file__).parents[1] / "tools" / "hermes" / "freeze_pont_001_ground_truth.py"


def load_freezer() -> ModuleType:
    spec = importlib.util.spec_from_file_location("hermes_ground_truth_freeze", FREEZER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_freeze_rejects_repository_target(tmp_path: Path) -> None:
    freezer = load_freezer()

    with pytest.raises(freezer.FreezeError, match="outside the repository"):
        freezer.ensure_external(freezer.PROJECT_ROOT / "ground-truth")

    freezer.ensure_external(tmp_path)


def test_freeze_rejects_unapproved_digest(tmp_path: Path) -> None:
    freezer = load_freezer()
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (candidate / freezer.GROUND_TRUTH_NAME).write_text("{}\n", encoding="utf-8")

    with pytest.raises(freezer.FreezeError, match="digest mismatch"):
        freezer.freeze(candidate, tmp_path / "frozen")


def test_freezer_does_not_import_product_code() -> None:
    tree = ast.parse(FREEZER_PATH.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)

    assert not any(name == "ste_lint" or name.startswith("ste_lint.") for name in imported)
