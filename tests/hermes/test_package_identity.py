import tomllib
from pathlib import Path


def test_distribution_and_cli_use_the_approved_hermes_identity() -> None:
    configuration = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert configuration["project"]["name"] == "hermes-lint"
    assert configuration["project"]["scripts"] == {"hermes": "hermes_lint.cli:entrypoint"}
    assert configuration["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == [
        "src/hermes_lint"
    ]
