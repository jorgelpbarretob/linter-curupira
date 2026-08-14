import json
from pathlib import Path

import pytest

from hermes_lint.cli import main


def test_cli_runs_the_preview_rule_only_when_explicitly_enabled(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "procedimento.md"
    source.write_text("Feche a válvula; desligue a bomba.\n", encoding="utf-8")

    exit_code = main(
        [
            "lint",
            str(source),
            "--enable-rule",
            "HERMES-PT-PONT-001",
            "--format",
            "json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["schema_version"] == "1.0"
    assert [item["rule_id"] for item in payload["diagnostics"]] == ["HERMES-PT-PONT-001"]
    assert payload["diagnostics"][0]["location"]["start_offset"] == 15


def test_cli_writes_and_reapplies_a_hermes_baseline(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "procedimento.txt"
    baseline = tmp_path / "hermes-baseline.json"
    source.write_text("Feche a válvula; desligue a bomba.\n", encoding="utf-8")
    selection = ["--enable-rule", "HERMES-PT-PONT-001"]

    assert main(["lint", str(source), *selection, "--write-baseline", str(baseline)]) == 0
    capsys.readouterr()
    assert main(["lint", str(source), *selection, "--baseline", str(baseline)]) == 0

    assert "Nenhuma violação" in capsys.readouterr().out
    assert "STE-I9" not in baseline.read_text(encoding="utf-8")


def test_cli_preserves_crlf_when_reporting_offsets(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "procedimento.txt"
    source.write_bytes(b"Primeira linha.\r\nFeche; prossiga.\r\n")

    assert (
        main(
            [
                "lint",
                str(source),
                "--enable-rule",
                "HERMES-PT-PONT-001",
                "--format",
                "json",
            ]
        )
        == 1
    )

    diagnostic = json.loads(capsys.readouterr().out)["diagnostics"][0]
    assert diagnostic["location"] == {
        "uri": str(source),
        "start_offset": 22,
        "end_offset": 23,
        "start_line": 2,
        "start_column": 6,
        "end_line": 2,
        "end_column": 7,
    }
