import pytest

from ste_lint.cli import main


def test_help_is_available(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--help"])

    assert exit_info.value.code == 0
    assert "Local-first technical English linter" in capsys.readouterr().out


def test_lint_reports_that_no_stable_rules_exist(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["lint"]) == 0
    assert capsys.readouterr().out.strip() == "No stable rules are available yet."
