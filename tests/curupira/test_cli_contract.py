import json
from pathlib import Path

import pytest

from curupira_lint.cli import main
from curupira_lint.linguistics import (
    LinguisticAnalysis,
    LinguisticSentence,
    NlpSetupError,
    SurfaceToken,
    SyntacticWord,
)


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
            "CURUPIRA-PT-PONT-001",
            "--format",
            "json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["schema_version"] == "1.0"
    assert [item["rule_id"] for item in payload["diagnostics"]] == ["CURUPIRA-PT-PONT-001"]
    assert payload["diagnostics"][0]["location"]["start_offset"] == 15


def test_cli_writes_and_reapplies_a_curupira_baseline(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "procedimento.txt"
    baseline = tmp_path / "curupira-baseline.json"
    source.write_text("Feche a válvula; desligue a bomba.\n", encoding="utf-8")
    selection = ["--enable-rule", "CURUPIRA-PT-PONT-001"]

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
                "CURUPIRA-PT-PONT-001",
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


class _PreviewBackend:
    def analyze(self, text: str) -> LinguisticAnalysis:
        return LinguisticAnalysis(
            text=text,
            surface_tokens=(SurfaceToken("Ligue", 0, 5), SurfaceToken(".", 5, 6)),
            words=(
                SyntacticWord(0, "ligar", "VERB", None, (), "root", None, 0),
                SyntacticWord(1, ".", "PUNCT", None, (), "punct", 0, 0),
            ),
            sentences=(LinguisticSentence(0, 6, 0, 2, 0, 2),),
            backend="spaCy",
            backend_version="3.8.15",
            model="pt_core_news_sm",
            model_version="3.8.0",
            model_sha256="c304fa04db3af73cd08a250feacf560506e15a2ec2469bd1b09f06847f6b455c",
            configuration_sha256="preview-test",
        )


def test_cli_analyze_exposes_local_preview_as_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "procedimento.txt"
    source.write_text("Ligue.", encoding="utf-8")
    monkeypatch.setattr("curupira_lint.cli.load_preview_backend", lambda: _PreviewBackend())

    assert main(["analyze", str(source), "--format", "json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == "curupira-linguistic-analysis/v1"
    assert payload["status"] == "preview"
    assert payload["source"]["uri"] == str(source)
    assert payload["analysis"]["surface_tokens"][0] == {
        "text": "Ligue",
        "start_offset": 0,
        "end_offset": 5,
    }
    assert payload["metrics"] == {
        "source_characters": 6,
        "source_utf8_bytes": 6,
        "surface_tokens": 2,
        "syntactic_words": 2,
        "sentences": 1,
    }


def test_cli_analyze_reports_optional_install_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "procedimento.txt"
    source.write_text("Ligue.", encoding="utf-8")

    def unavailable() -> _PreviewBackend:
        raise NlpSetupError("instale o extra opcional")

    monkeypatch.setattr("curupira_lint.cli.load_preview_backend", unavailable)

    assert main(["analyze", str(source)]) == 2
    assert "instale o extra opcional" in capsys.readouterr().err


def test_cli_analyze_rejects_markdown_before_loading_nlp(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "procedimento.md"
    source.write_text("Ligue a bomba.", encoding="utf-8")
    loaded = False

    def unexpected_load() -> _PreviewBackend:
        nonlocal loaded
        loaded = True
        return _PreviewBackend()

    monkeypatch.setattr("curupira_lint.cli.load_preview_backend", unexpected_load)

    assert main(["analyze", str(source)]) == 2
    assert loaded is False
    assert "somente arquivos .txt" in capsys.readouterr().err
