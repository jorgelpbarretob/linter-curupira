import json
from pathlib import Path

import pytest

from ste_lint.cli import main


def write_utf8(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        stream.write(text)


def test_rules_lists_all_preview_rules_in_rule_id_order(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["--rules"]) == 0

    lines = capsys.readouterr().out.splitlines()
    assert [line.split("\t", 1)[0] for line in lines] == [
        "STE-I9-LIST-001",
        "STE-I9-NOTE-001",
        "STE-I9-PARA-001",
        "STE-I9-PUNCT-001",
        "STE-I9-SENT-001",
        "STE-I9-SENT-002",
        "STE-I9-VOICE-001",
    ]
    assert all("preview" in line for line in lines)


def test_explain_prints_traceable_project_metadata(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["--explain", "STE-I9-PUNCT-001"]) == 0

    output = capsys.readouterr().out
    assert "STE-I9-PUNCT-001" in output
    assert "ASD-STE100 issue 9" in output
    assert "Part 1, Section 8, Rule 8.1" in output
    assert "preview" in output
    assert "Reports a semicolon found in lintable prose." in output


def test_explain_unknown_rule_is_an_operational_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["--explain", "STE-I9-UNKNOWN-999"]) == 2
    assert "unknown executable rule_id" in capsys.readouterr().err


def test_preview_rule_runs_only_with_explicit_enable(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "manual.txt"
    write_utf8(source, "Inspect the valve; replace the seal.\n")

    assert main(["lint", str(source), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["diagnostics"] == []

    exit_code = main(
        [
            "lint",
            str(source),
            "--format",
            "json",
            "--enable-rule",
            "STE-I9-PUNCT-001",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert [item["rule_id"] for item in payload["diagnostics"]] == ["STE-I9-PUNCT-001"]
