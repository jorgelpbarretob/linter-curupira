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
