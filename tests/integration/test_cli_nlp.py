import subprocess
import sys
from importlib import metadata
from pathlib import Path

import pytest

import ste_lint.cli
from ste_lint.cli import main
from ste_lint.nlp import NlpSetupError


def write_utf8(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        stream.write(text)


def test_enabled_nlp_rule_requires_explicit_nlp_configuration(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "manual.txt"
    write_utf8(source, "Remove the cover.\n")

    exit_code = main(
        ["lint", str(source), "--enable-rule", "STE-I9-NOTE-001", "--text-type", "procedural-note"]
    )

    assert exit_code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "requires an [nlp] configuration" in captured.err


def test_nlp_configuration_does_not_load_backend_when_no_nlp_rule_is_enabled(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "manual.txt"
    config = tmp_path / "ste-lint.toml"
    write_utf8(source, "Synthetic text.\n")
    write_utf8(
        config,
        "schema_version = 1\n"
        "[nlp]\n"
        'backend = "spacy"\n'
        'model_package = "en_core_web_sm"\n'
        'model_version = "3.8.0"\n',
    )

    def unexpected_load(configuration: object) -> object:
        del configuration
        raise AssertionError("NLP backend must remain lazy")

    monkeypatch.setattr(ste_lint.cli, "_load_nlp_backend", unexpected_load)

    assert main(["lint", str(source), "--config", str(config)]) == 0
    assert capsys.readouterr().out == "No executable rules are enabled.\n"


def test_default_cli_process_does_not_import_spacy_or_model() -> None:
    script = (
        "import sys; import ste_lint.cli; "
        "assert 'spacy' not in sys.modules; "
        "assert 'en_core_web_sm' not in sys.modules"
    )

    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr


def test_cli_maps_nlp_setup_failure_to_operational_exit(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "manual.txt"
    config = tmp_path / "ste-lint.toml"
    write_utf8(source, "Remove the access cover.\n")
    write_utf8(
        config,
        "schema_version = 1\n"
        "[rules]\n"
        'enable = ["STE-I9-NOTE-001"]\n'
        "[nlp]\n"
        'backend = "spacy"\n'
        'model_package = "en_core_web_sm"\n'
        'model_version = "3.8.0"\n',
    )

    def fail_setup(configuration: object) -> object:
        del configuration
        raise NlpSetupError("synthetic optional install failure")

    monkeypatch.setattr(ste_lint.cli, "_load_nlp_backend", fail_setup)

    assert main(["lint", str(source), "--config", str(config)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "synthetic optional install failure" in captured.err


def test_cli_runs_pinned_model_offline_when_nlp_is_explicitly_enabled(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    try:
        if metadata.version("spacy") != "3.8.15" or metadata.version("en-core-web-sm") != "3.8.0":
            pytest.skip("pinned NLP environment is not installed")
    except metadata.PackageNotFoundError:
        pytest.skip("pinned NLP environment is not installed")
    source = tmp_path / "manual.txt"
    config = tmp_path / "ste-lint.toml"
    write_utf8(source, "Remove the access cover.\n")
    write_utf8(
        config,
        "schema_version = 1\n"
        'text_type = "procedural-note"\n'
        "[rules]\n"
        'enable = ["STE-I9-NOTE-001"]\n'
        "[nlp]\n"
        'backend = "spacy"\n'
        'model_package = "en_core_web_sm"\n'
        'model_version = "3.8.0"\n',
    )

    assert main(["lint", str(source), "--config", str(config)]) == 1
    output = capsys.readouterr().out
    assert "info STE-I9-NOTE-001" in output
    assert "Remove" in output
