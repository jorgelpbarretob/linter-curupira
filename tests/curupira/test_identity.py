import ast
import tomllib
from pathlib import Path


def test_distribution_and_primary_cli_use_curupira_identity() -> None:
    configuration = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert configuration["project"]["name"] == "curupira-lint"
    assert configuration["project"]["scripts"]["curupira"] == ("curupira_lint.cli:entrypoint")
    assert "hermes" not in configuration["project"]["scripts"]
    assert configuration["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == [
        "src/curupira_lint",
        "src/hermes_lint",
    ]

    for pyproject in Path(".").rglob("pyproject.toml"):
        candidate = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        assert "hermes" not in candidate.get("project", {}).get("scripts", {}), pyproject


def test_curupira_namespace_does_not_import_legacy_implementations() -> None:
    forbidden_roots = {"hermes_lint", "ste_lint"}

    for source_path in Path("src/curupira_lint").rglob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        imported_roots = {
            alias.name.partition(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported_roots.update(
            node.module.partition(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        )

        assert imported_roots.isdisjoint(forbidden_roots), source_path


def test_historical_namespaces_remain_isolated_from_curupira() -> None:
    for package, forbidden_roots in (
        ("hermes_lint", {"curupira_lint", "ste_lint"}),
        ("ste_lint", {"curupira_lint", "hermes_lint"}),
    ):
        for source_path in Path("src", package).rglob("*.py"):
            tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
            imported_roots = {
                alias.name.partition(".")[0]
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            }
            imported_roots.update(
                node.module.partition(".")[0]
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module
            )
            assert imported_roots.isdisjoint(forbidden_roots), source_path
