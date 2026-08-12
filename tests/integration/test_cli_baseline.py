import json
from pathlib import Path

import pytest

from ste_lint.cli import main


def write_utf8(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        stream.write(text)


def test_cli_writes_and_applies_baseline_without_storing_document_text(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "manual.txt"
    baseline = tmp_path / "baseline.json"
    write_utf8(source, "Inspect the valve; replace the seal.\n")
    rule_args = ["--enable-rule", "STE-I9-PUNCT-001"]

    exit_code = main(
        [
            "lint",
            str(source),
            *rule_args,
            "--write-baseline",
            str(baseline),
        ]
    )

    assert exit_code == 0
    assert "Wrote baseline with 1 fingerprint" in capsys.readouterr().out
    raw_baseline = baseline.read_text(encoding="utf-8")
    assert "Inspect" not in raw_baseline
    assert json.loads(raw_baseline)["schema_version"] == "1.0"
    assert not list(tmp_path.glob(f".{baseline.name}.*.tmp"))

    exit_code = main(
        [
            "lint",
            str(source),
            *rule_args,
            "--baseline",
            str(baseline),
            "--format",
            "json",
        ]
    )

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["diagnostics"] == []


def test_changed_context_is_not_suppressed_by_baseline(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "manual.txt"
    baseline = tmp_path / "baseline.json"
    write_utf8(source, "Inspect the valve; replace the seal.\n")
    args = ["--enable-rule", "STE-I9-PUNCT-001"]
    assert main(["lint", str(source), *args, "--write-baseline", str(baseline)]) == 0
    capsys.readouterr()
    write_utf8(source, "Inspect the pump; replace the seal.\n")

    exit_code = main(["lint", str(source), *args, "--baseline", str(baseline), "--format", "json"])

    assert exit_code == 1
    assert len(json.loads(capsys.readouterr().out)["diagnostics"]) == 1


def test_invalid_baseline_is_an_operational_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "manual.txt"
    baseline = tmp_path / "baseline.json"
    write_utf8(source, "Inspect the valve; replace the seal.\n")
    write_utf8(baseline, '{"schema_version":"2.0","fingerprints":[]}')

    exit_code = main(["lint", str(source), "--baseline", str(baseline)])

    assert exit_code == 2
    assert "schema_version" in capsys.readouterr().err


def test_baseline_and_write_baseline_are_mutually_exclusive() -> None:
    parser_error = pytest.raises(SystemExit)

    with parser_error as error:
        main(
            [
                "lint",
                "manual.txt",
                "--baseline",
                "old.json",
                "--write-baseline",
                "new.json",
            ]
        )

    assert error.value.code == 2
