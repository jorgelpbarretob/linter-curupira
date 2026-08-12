import json
import socket
from pathlib import Path

import pytest

from ste_lint.cli import main


def test_default_lint_path_does_not_open_a_socket(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def blocked_socket(*args: object, **kwargs: object) -> socket.socket:
        del args, kwargs
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", blocked_socket)
    source = tmp_path / "manual.txt"
    source.write_text("Synthetic text.\n", encoding="utf-8", newline="")

    assert main(["lint", str(source)]) == 0


def test_vocabulary_import_and_lint_do_not_open_a_socket(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def blocked_socket(*args: object, **kwargs: object) -> socket.socket:
        del args, kwargs
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", blocked_socket)
    source = tmp_path / "source.json"
    source.write_text(
        json.dumps(
            {
                "format": "ste-lint-vocabulary-source",
                "schema_version": 1,
                "standard": "ASD-STE100",
                "issue": "9",
                "entries": [],
            },
            separators=(",", ":"),
        ),
        encoding="utf-8",
        newline="",
    )
    cache = tmp_path / "cache"

    assert (
        main(
            [
                "vocabulary",
                "import-json",
                str(source),
                "--cache-dir",
                str(cache),
                "--confirm-authorized",
            ]
        )
        == 0
    )
    document = tmp_path / "manual.txt"
    document.write_text("Synthetic text.\n", encoding="utf-8", newline="")
    resource = next(cache.glob("*.json"))

    assert main(["lint", str(document), "--vocabulary", str(resource)]) == 0
