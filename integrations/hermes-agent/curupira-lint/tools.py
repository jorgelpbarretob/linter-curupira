"""Local Curupira tool handler for Hermes Agent."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "curupira-hermes-preflight/v1"
WRAPPER_VERSION = "1.0.0"
RULE_ID = "CURUPIRA-PT-PONT-001"
SUPPORTED_SUFFIXES = frozenset({".md", ".markdown", ".txt"})
CURUPIRA_TIMEOUT_SECONDS = 30


def handle_curupira_lint(arguments: dict[str, Any], **kwargs: object) -> str:
    """Run the deterministic Curupira lint and return an auditable JSON event."""
    del kwargs
    started = time.monotonic_ns()
    try:
        return _handle_curupira_lint(arguments, started=started)
    except Exception:
        return _event(
            started=started,
            status="blocked",
            exit_code=2,
            curupira_version=None,
            operational_errors=[
                {
                    "code": "wrapper_error",
                    "message": "o wrapper Curupira terminou com erro operacional",
                }
            ],
        )


def _handle_curupira_lint(arguments: dict[str, Any], *, started: int) -> str:
    raw_paths = arguments.get("paths")
    if (
        not isinstance(raw_paths, list)
        or not raw_paths
        or any(not isinstance(path, str) or not path for path in raw_paths)
    ):
        return _event(
            started=started,
            status="blocked",
            exit_code=2,
            curupira_version=None,
            operational_errors=[
                {
                    "code": "invalid_arguments",
                    "message": "paths deve ser uma lista não vazia de caminhos",
                }
            ],
        )
    paths = [Path(raw_path).resolve() for raw_path in raw_paths]
    supported = [path for path in paths if path.suffix.lower() in SUPPORTED_SUFFIXES]
    skipped = [
        {"path": str(path), "reason": "unsupported_extension"}
        for path in paths
        if path.suffix.lower() not in SUPPORTED_SUFFIXES
    ]
    if not supported:
        return _event(
            started=started,
            status="not_applicable",
            exit_code=0,
            curupira_version=None,
            skipped=skipped,
        )
    executable = shutil.which("curupira")
    if executable is None:
        return _event(
            started=started,
            status="blocked",
            exit_code=2,
            curupira_version=None,
            skipped=skipped,
            operational_errors=[
                {
                    "code": "curupira_not_found",
                    "message": "executável curupira não encontrado no PATH",
                }
            ],
        )
    curupira_version = _probe_curupira_version(executable)
    if curupira_version is None:
        return _event(
            started=started,
            status="blocked",
            exit_code=2,
            curupira_version=None,
            skipped=skipped,
            operational_errors=[
                {
                    "code": "version_probe_failed",
                    "message": "versão do Curupira não pôde ser confirmada",
                }
            ],
        )
    config_path = Path(arguments["config_path"]).resolve() if arguments.get("config_path") else None
    config = None
    if config_path is not None:
        try:
            config_digest = hashlib.sha256(config_path.read_bytes()).hexdigest()
        except OSError:
            return _event(
                started=started,
                status="blocked",
                exit_code=2,
                curupira_version=curupira_version,
                skipped=skipped,
                config={"path": str(config_path), "sha256": None},
                operational_errors=[
                    {
                        "code": "config_read_error",
                        "path": str(config_path),
                        "message": "configuração não pôde ser lida",
                    }
                ],
            )
        config = {"path": str(config_path), "sha256": config_digest}
    files: list[dict[str, Any]] = []
    operational_errors: list[dict[str, str]] = []
    for path in supported:
        try:
            source = path.read_bytes()
        except OSError:
            operational_errors.append(
                {
                    "code": "input_read_error",
                    "path": str(path),
                    "message": "arquivo não pôde ser lido",
                }
            )
            continue
        file_started = time.monotonic_ns()
        command = [executable, "lint", str(path)]
        if config_path is not None:
            command.extend(("--config", str(config_path)))
        command.extend(("--enable-rule", RULE_ID, "--format", "json"))
        try:
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=CURUPIRA_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            files.append(_file_result(path, source, file_started, exit_code=2))
            operational_errors.append(
                {
                    "code": "curupira_timeout",
                    "path": str(path),
                    "message": (
                        f"Curupira excedeu o limite de {CURUPIRA_TIMEOUT_SECONDS} segundos"
                    ),
                }
            )
            continue
        except OSError:
            files.append(_file_result(path, source, file_started, exit_code=2))
            operational_errors.append(
                {
                    "code": "curupira_execution_error",
                    "path": str(path),
                    "message": "Curupira não pôde ser executado",
                }
            )
            continue
        diagnostics: list[object] = []
        file_exit_code = process.returncode
        if process.returncode in {0, 1}:
            try:
                output = json.loads(process.stdout)
                candidate_diagnostics = output["diagnostics"]
                if not isinstance(candidate_diagnostics, list):
                    raise TypeError("diagnostics must be a list")
                diagnostics = candidate_diagnostics
            except (json.JSONDecodeError, KeyError, TypeError):
                file_exit_code = 2
                operational_errors.append(
                    {
                        "code": "invalid_curupira_output",
                        "path": str(path),
                        "message": "Curupira não retornou o JSON esperado",
                    }
                )
        if process.returncode == 2:
            operational_errors.append(
                {
                    "code": "curupira_operational_error",
                    "message": (
                        process.stderr.strip()[:2000] or "Curupira terminou com erro operacional"
                    ),
                    "path": str(path),
                }
            )
        elif process.returncode not in {0, 1}:
            file_exit_code = 2
            operational_errors.append(
                {
                    "code": "unexpected_exit_code",
                    "message": f"Curupira terminou com código {process.returncode}",
                    "path": str(path),
                }
            )
        files.append(
            _file_result(
                path,
                source,
                file_started,
                exit_code=file_exit_code,
                diagnostics=diagnostics,
            )
        )
    exit_code = 2 if operational_errors else max((item["exit_code"] for item in files), default=0)
    status = "blocked" if exit_code == 2 else "needs_review" if exit_code == 1 else "passed"
    return _event(
        started=started,
        status=status,
        exit_code=exit_code,
        curupira_version=curupira_version,
        files=files,
        skipped=skipped,
        config=config,
        operational_errors=operational_errors,
    )


def _event(
    *,
    started: int,
    status: str,
    exit_code: int,
    curupira_version: str | None,
    files: list[dict[str, Any]] | None = None,
    skipped: list[dict[str, str]] | None = None,
    config: dict[str, str | None] | None = None,
    operational_errors: list[dict[str, str]] | None = None,
) -> str:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "event": "preflight_completed",
        "tool": "curupira_lint",
        "status": status,
        "exit_code": exit_code,
        "rules": [RULE_ID],
        "versions": {"wrapper": WRAPPER_VERSION, "curupira": curupira_version},
        "duration_ms": _elapsed_ms(started),
        "files": files or [],
        "skipped": skipped or [],
        "config": config,
        "operational_errors": operational_errors or [],
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _file_result(
    path: Path,
    source: bytes,
    started: int,
    *,
    exit_code: int,
    diagnostics: list[object] | None = None,
) -> dict[str, Any]:
    return {
        "path": str(path),
        "sha256": hashlib.sha256(source).hexdigest(),
        "size_bytes": len(source),
        "exit_code": exit_code,
        "duration_ms": _elapsed_ms(started),
        "diagnostics": diagnostics or [],
    }


def _probe_curupira_version(executable: str) -> str | None:
    interpreters: list[Path] = []
    try:
        with Path(executable).open(encoding="utf-8") as stream:
            shebang = stream.readline(1024).strip()
        interpreter = Path(shebang.removeprefix("#!"))
        if shebang.startswith("#!") and interpreter.name.startswith("python"):
            interpreters.append(interpreter)
        if Path(executable).parent == Path.home() / ".local" / "bin":
            interpreters.extend(
                (
                    Path.home()
                    / ".local"
                    / "share"
                    / "uv"
                    / "tools"
                    / "curupira-lint"
                    / "bin"
                    / "python",
                    Path.home() / ".local" / "pipx" / "venvs" / "curupira-lint" / "bin" / "python",
                )
            )
    except OSError:
        pass
    for interpreter in interpreters:
        version = _version_from_interpreter(interpreter)
        if version is not None:
            return version
    try:
        process = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    output = process.stdout.strip()
    if process.returncode == 0 and output.startswith("curupira "):
        return output.removeprefix("curupira ")
    return None


def _version_from_interpreter(interpreter: Path) -> str | None:
    try:
        metadata_process = subprocess.run(
            [
                str(interpreter),
                "-c",
                ("from importlib.metadata import version; print(version('curupira-lint'))"),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    version = metadata_process.stdout.strip()
    return version if metadata_process.returncode == 0 and version else None


def _elapsed_ms(started: int) -> int:
    return max(0, (time.monotonic_ns() - started) // 1_000_000)
