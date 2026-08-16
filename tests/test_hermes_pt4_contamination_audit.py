from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

TOOL_PATH = Path(__file__).parents[1] / "tools" / "hermes" / "audit_pt4_corpus_contamination.py"


def load_tool() -> ModuleType:
    sys.path.insert(0, str(TOOL_PATH.parent))
    spec = importlib.util.spec_from_file_location("hermes_pt4_contamination", TOOL_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_overlap_detects_exact_and_normalized_matches() -> None:
    tool = load_tool()

    assert tool.overlap(["Pressão  ALTA"], ["pressão alta"]) == {
        "exact": 0,
        "nfc_casefold_whitespace": 1,
    }
    assert tool.overlap(["A bomba parou."], ["A válvula fechou."]) == {
        "exact": 0,
        "nfc_casefold_whitespace": 0,
    }


def test_auditor_is_model_blind_and_does_not_import_product_code() -> None:
    tree = ast.parse(TOOL_PATH.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)

    assert not any(
        name == "hermes_lint" or name.startswith("hermes_lint.") or name in {"spacy", "stanza"}
        for name in imported
    )
