import ast
from pathlib import Path


def test_domain_does_not_import_outer_layers() -> None:
    domain = Path("src/ste_lint/domain")
    forbidden = {"cli", "engine", "nlp", "parsing", "reporting", "semantic", "vocabulary"}
    imported: set[str] = set()

    for path in domain.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    parts = alias.name.split(".")
                    imported.add(parts[1] if parts[0] == "ste_lint" else parts[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                parts = node.module.split(".")
                imported.add(parts[1] if parts[0] == "ste_lint" else parts[0])

    assert imported.isdisjoint(forbidden)
