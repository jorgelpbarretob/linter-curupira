import json
from pathlib import Path

import pytest

from curupira_lint.cli import main


def test_curupira_runs_the_preview_rule_under_the_new_namespace(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "procedimento.txt"
    source.write_text("Feche a válvula; prossiga.\n", encoding="utf-8")

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
    assert [item["rule_id"] for item in payload["diagnostics"]] == ["CURUPIRA-PT-PONT-001"]
    assert payload["diagnostics"][0]["source"]["standard"] == "Curupira"


def test_curupira_reports_the_new_rule_id_for_a_legacy_hermes_selection(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "procedimento.txt"
    source.write_text("Feche a válvula; prossiga.\n", encoding="utf-8")

    exit_code = main(["lint", str(source), "--enable-rule", "HERMES-PT-PONT-001"])

    assert exit_code == 2
    assert "HERMES-PT-PONT-001 foi renomeado para CURUPIRA-PT-PONT-001" in (capsys.readouterr().err)


def test_curupira_lint_requires_a_document_path() -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["lint"])

    assert exit_info.value.code == 2


def test_curupira_without_arguments_prints_help(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main([]) == 0
    assert "Linter local de documentação técnica em português brasileiro" in capsys.readouterr().out


@pytest.mark.parametrize("command", ["analyze", "semantic-review"])
def test_preview_analysis_commands_reject_markdown(
    command: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "procedimento.md"
    source.write_text("Feche a válvula.", encoding="utf-8")

    assert main([command, str(source)]) == 2
    assert "aceita somente arquivos .txt" in capsys.readouterr().err


def test_curupira_lint_excludes_supported_markdown_regions(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "procedimento.markdown"
    source.write_text(
        "---\ntitulo: valor; oculto\n---\n"
        "Use `chave;valor`.\n"
        "Abra [referência](https://example.invalid/?a=1;b=2).\n"
        "```text\nignorado; código\n```\n",
        encoding="utf-8",
    )

    exit_code = main(
        ["lint", str(source), "--enable-rule", "CURUPIRA-PT-PONT-001", "--format", "json"]
    )

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["diagnostics"] == []


def test_semantic_review_without_api_key_is_an_operational_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "procedimento.txt"
    source.write_text("Feche a válvula.", encoding="utf-8")
    monkeypatch.delenv("MARITACA_API_KEY", raising=False)

    assert main(["semantic-review", str(source)]) == 2
    assert "MARITACA_API_KEY ausente" in capsys.readouterr().err


def test_semantic_review_is_explicit_and_reports_sabiazinho_provenance(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "procedimento.txt"
    source.write_text("Depois disso, reinicie.", encoding="utf-8")
    monkeypatch.setenv("MARITACA_API_KEY", "test-key")
    monkeypatch.setattr(
        "curupira_lint.cli.review_with_sabiazinho",
        lambda _text, **_kwargs: {
            "engine": {
                "provider": "maritaca",
                "model_requested": "sabiazinho-4-2026-01-06",
                "model_returned": "sabiazinho-4-2026-01-06",
            },
            "usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
            "observations": [],
        },
    )

    assert main(["semantic-review", str(source)]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == "curupira-semantic-review/v1"
    assert payload["status"] == "preview"
    assert payload["review"]["engine"]["provider"] == "maritaca"
