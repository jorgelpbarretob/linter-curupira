import tomllib
from pathlib import Path


def test_distribution_keeps_the_hermes_python_package_without_shadowing_hermes_agent() -> None:
    configuration = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert "hermes" not in configuration["project"]["scripts"]
    assert (
        "src/hermes_lint" in configuration["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"]
    )
