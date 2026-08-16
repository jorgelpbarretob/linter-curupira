from __future__ import annotations

import importlib.metadata
import subprocess
import sys

import pytest

from curupira_lint.linguistics import load_preview_backend
from tools.hermes.pt4_spacy_adapter import deny_network


def test_importing_base_cli_does_not_load_optional_nlp_packages() -> None:
    command = (
        "import sys; import curupira_lint.cli; "
        "assert 'spacy' not in sys.modules; "
        "assert 'pt_core_news_sm' not in sys.modules"
    )

    completed = subprocess.run(
        [sys.executable, "-c", command],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr


def test_pinned_preview_backend_runs_with_network_denied() -> None:
    try:
        spacy_version = importlib.metadata.version("spacy")
        model_version = importlib.metadata.version("pt_core_news_sm")
    except importlib.metadata.PackageNotFoundError:
        pytest.skip("extra NLP preview não instalado")
    if (spacy_version, model_version) != ("3.8.15", "3.8.0"):
        pytest.skip("versões fixadas do NLP preview não instaladas")
    text = "Feche a válvula.\r\n"

    with deny_network():
        analysis = load_preview_backend().analyze(text)

    assert analysis.text == text
    assert len(analysis.sentences) == 1
    assert all(
        text[token.start_offset : token.end_offset] == token.text
        for token in analysis.surface_tokens
    )
