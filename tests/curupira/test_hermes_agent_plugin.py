import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

PLUGIN_ROOT = Path(__file__).parents[2] / "integrations" / "hermes-agent" / "curupira-lint"


@pytest.fixture(autouse=True)
def _isolate_telemetry_home(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))


def _load_plugin_tools() -> ModuleType:
    spec = importlib.util.spec_from_file_location("curupira_hermes_tools", PLUGIN_ROOT / "tools.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_plugin() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "curupira_hermes_plugin",
        PLUGIN_ROOT / "__init__.py",
        submodule_search_locations=[str(PLUGIN_ROOT)],
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_curupira_lint_returns_auditable_passed_event_for_clean_document(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "procedimento.md"
    source.write_text("Feche a válvula. Em seguida, desligue a bomba.\n", encoding="utf-8")
    monkeypatch.setenv(
        "PATH",
        f"{Path(__file__).parents[2] / '.venv' / 'bin'}{os.pathsep}{os.environ['PATH']}",
    )

    payload = json.loads(_load_plugin_tools().handle_curupira_lint({"paths": [str(source)]}))

    assert payload["schema_version"] == "curupira-hermes-preflight/v1"
    assert payload["event"] == "preflight_completed"
    assert payload["tool"] == "curupira_lint"
    assert payload["status"] == "passed"
    assert payload["exit_code"] == 0
    assert payload["rules"] == ["CURUPIRA-PT-PONT-001"]
    assert payload["versions"] == {"wrapper": "1.1.0", "curupira": "0.3.0"}
    assert payload["duration_ms"] >= 0
    assert payload["operational_errors"] == []
    assert payload["files"] == [
        {
            "path": str(source.resolve()),
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "size_bytes": len(source.read_bytes()),
            "exit_code": 0,
            "duration_ms": payload["files"][0]["duration_ms"],
            "diagnostics": [],
        }
    ]


def test_curupira_lint_returns_needs_review_with_diagnostics(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "procedimento.txt"
    source.write_text("Feche a válvula; desligue a bomba.\n", encoding="utf-8")
    monkeypatch.setenv(
        "PATH",
        f"{Path(__file__).parents[2] / '.venv' / 'bin'}{os.pathsep}{os.environ['PATH']}",
    )

    payload = json.loads(_load_plugin_tools().handle_curupira_lint({"paths": [str(source)]}))

    assert payload["status"] == "needs_review"
    assert payload["exit_code"] == 1
    assert payload["operational_errors"] == []
    assert payload["files"][0]["exit_code"] == 1
    assert [item["rule_id"] for item in payload["files"][0]["diagnostics"]] == [
        "CURUPIRA-PT-PONT-001"
    ]


def test_curupira_lint_persists_sanitized_telemetry_without_the_cli_shim(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "procedimento.txt"
    source.write_text("Feche a válvula; prossiga.\n", encoding="utf-8")
    executable = tmp_path / "curupira"
    executable.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "--version" ]; then echo "curupira 0.3.0"; exit 0; fi\n'
        'printf \'%s\\n\' \'{"schema_version":"1.0","diagnostics":[{'
        '"rule_id":"CURUPIRA-PT-PONT-001","severity":"info",'
        '"location":{"start_line":1,"start_column":16,'
        '"excerpt":"Feche a válvula; prossiga."},'
        '"message":"Ponto e vírgula em prosa lintável.",'
        '"evidence":"Feche a válvula; prossiga."}]} \'\n'
        "exit 1\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    hermes_home = tmp_path / ".hermes"
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    monkeypatch.setenv("PATH", str(tmp_path))

    payload = json.loads(_load_plugin_tools().handle_curupira_lint({"paths": [str(source)]}))

    assert payload["status"] == "needs_review"
    telemetry_path = hermes_home / "cron" / "state" / "curupira-usage" / "preflight-events.jsonl"
    records = [json.loads(line) for line in telemetry_path.read_text(encoding="utf-8").splitlines()]
    assert records == [
        {
            "schema_version": "curupira-hermes-preflight-telemetry/v1",
            "event": "preflight_completed",
            "recorded_at": records[0]["recorded_at"],
            "invocation_id": records[0]["invocation_id"],
            "tool": "curupira_lint",
            "status": "needs_review",
            "exit_code": 1,
            "rules": ["CURUPIRA-PT-PONT-001"],
            "versions": {"wrapper": "1.1.0", "curupira": "0.3.0"},
            "duration_ms": records[0]["duration_ms"],
            "files": [
                {
                    "path": str(source.resolve()),
                    "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    "size_bytes": len(source.read_bytes()),
                    "exit_code": 1,
                    "duration_ms": records[0]["files"][0]["duration_ms"],
                    "diagnostics": [
                        {
                            "rule_id": "CURUPIRA-PT-PONT-001",
                            "severity": "info",
                            "location": {"start_line": 1, "start_column": 16},
                        }
                    ],
                }
            ],
            "skipped": [],
            "config": None,
            "operational_errors": [],
            "runtime": {
                "pid": os.getpid(),
                "ppid": os.getppid(),
                "curupira_executable": str(executable.resolve()),
            },
        }
    ]
    assert records[0]["recorded_at"].endswith("Z")
    assert len(records[0]["invocation_id"]) == 36
    assert "Feche a válvula" not in telemetry_path.read_text(encoding="utf-8")


def test_curupira_lint_blocks_when_telemetry_cannot_be_persisted(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "module.py"
    source.write_text("print('fora do preflight')\n", encoding="utf-8")
    invalid_home = tmp_path / "not-a-directory"
    invalid_home.write_text("occupied", encoding="utf-8")
    monkeypatch.setenv("HERMES_HOME", str(invalid_home))

    payload = json.loads(_load_plugin_tools().handle_curupira_lint({"paths": [str(source)]}))

    assert payload["status"] == "blocked"
    assert payload["exit_code"] == 2
    assert payload["operational_errors"] == [
        {
            "code": "telemetry_write_error",
            "message": "a evidência do preflight Curupira não pôde ser persistida",
        }
    ]


def test_curupira_lint_blocks_when_the_executable_is_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "procedimento.md"
    source.write_text("Feche a válvula.\n", encoding="utf-8")
    monkeypatch.setenv("PATH", str(tmp_path / "empty-bin"))

    payload = json.loads(_load_plugin_tools().handle_curupira_lint({"paths": [str(source)]}))

    assert payload["status"] == "blocked"
    assert payload["exit_code"] == 2
    assert payload["files"] == []
    assert payload["operational_errors"] == [
        {
            "code": "curupira_not_found",
            "message": "executável curupira não encontrado no PATH",
        }
    ]


def test_curupira_lint_is_not_applicable_without_supported_documents(tmp_path: Path) -> None:
    source = tmp_path / "module.py"
    source.write_text("print('fora do preflight')\n", encoding="utf-8")

    payload = json.loads(_load_plugin_tools().handle_curupira_lint({"paths": [str(source)]}))

    assert payload["status"] == "not_applicable"
    assert payload["exit_code"] == 0
    assert payload["files"] == []
    assert payload["skipped"] == [
        {
            "path": str(source.resolve()),
            "reason": "unsupported_extension",
        }
    ]


def test_curupira_lint_blocks_and_records_an_invalid_allowed_config(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "procedimento.md"
    source.write_text("Feche a válvula.\n", encoding="utf-8")
    config = tmp_path / "curupira.toml"
    config.write_text("schema_version = 2\n", encoding="utf-8")
    monkeypatch.setenv(
        "PATH",
        f"{Path(__file__).parents[2] / '.venv' / 'bin'}{os.pathsep}{os.environ['PATH']}",
    )

    payload = json.loads(
        _load_plugin_tools().handle_curupira_lint(
            {"paths": [str(source)], "config_path": str(config)}
        )
    )

    assert payload["status"] == "blocked"
    assert payload["exit_code"] == 2
    assert payload["config"] == {
        "path": str(config.resolve()),
        "sha256": hashlib.sha256(config.read_bytes()).hexdigest(),
    }
    assert payload["files"][0]["exit_code"] == 2
    assert payload["files"][0]["diagnostics"] == []
    assert payload["operational_errors"][0]["code"] == "curupira_operational_error"
    assert "schema_version deve ser 1" in payload["operational_errors"][0]["message"]


def test_curupira_lint_returns_json_when_a_supported_input_cannot_be_read(
    tmp_path: Path,
    monkeypatch,
) -> None:
    missing = tmp_path / "missing.md"
    monkeypatch.setenv(
        "PATH",
        f"{Path(__file__).parents[2] / '.venv' / 'bin'}{os.pathsep}{os.environ['PATH']}",
    )

    payload = json.loads(_load_plugin_tools().handle_curupira_lint({"paths": [str(missing)]}))

    assert payload["status"] == "blocked"
    assert payload["exit_code"] == 2
    assert payload["files"] == []
    assert payload["operational_errors"] == [
        {
            "code": "input_read_error",
            "path": str(missing.resolve()),
            "message": "arquivo não pôde ser lido",
        }
    ]


def test_plugin_registers_curupira_lint_as_a_structured_hermes_tool() -> None:
    registrations = []

    class Context:
        def register_tool(self, **registration) -> None:
            registrations.append(registration)

        def register_hook(self, *_args, **_kwargs) -> None:
            pass

        def dispatch_tool(self, *_args, **_kwargs) -> str:
            return "{}"

    _load_plugin().register(Context())

    assert len(registrations) == 1
    registration = registrations[0]
    assert registration["name"] == "curupira_lint"
    assert registration["toolset"] == "curupira"
    assert registration["schema"]["parameters"]["required"] == ["paths"]
    assert registration["schema"]["parameters"]["properties"]["paths"]["items"] == {
        "type": "string"
    }
    assert registration["handler"].__name__ == "handle_curupira_lint"


def test_output_gate_allows_completion_after_a_passed_preflight() -> None:
    hooks = {}
    dispatched = []

    class Context:
        def register_tool(self, **_registration) -> None:
            pass

        def register_hook(self, name, callback) -> None:
            hooks[name] = callback

        def dispatch_tool(self, name, arguments) -> str:
            dispatched.append((name, arguments))
            return json.dumps(
                {
                    "event": "preflight_completed",
                    "status": "passed",
                    "exit_code": 0,
                    "files": [],
                    "operational_errors": [],
                }
            )

    _load_plugin().register(Context())

    directive = hooks["pre_verify"](
        attempt=0,
        changed_paths=["/tmp/guia.md", "/tmp/module.py"],
    )

    assert directive is None
    assert dispatched == [
        (
            "curupira_lint",
            {"paths": ["/tmp/guia.md", "/tmp/module.py"]},
        )
    ]


def test_output_gate_grants_one_repair_for_curupira_diagnostics() -> None:
    hooks = {}

    class Context:
        def register_tool(self, **_registration) -> None:
            pass

        def register_hook(self, name, callback) -> None:
            hooks[name] = callback

        def dispatch_tool(self, _name, _arguments) -> str:
            return json.dumps(
                {
                    "event": "preflight_completed",
                    "status": "needs_review",
                    "exit_code": 1,
                    "files": [
                        {
                            "path": "/tmp/guia.md",
                            "diagnostics": [
                                {
                                    "rule_id": "CURUPIRA-PT-PONT-001",
                                    "location": {
                                        "start_line": 2,
                                        "start_column": 18,
                                    },
                                    "message": "Evite ponto e vírgula.",
                                }
                            ],
                        }
                    ],
                    "operational_errors": [],
                }
            )

    _load_plugin().register(Context())

    directive = hooks["pre_verify"](attempt=0, changed_paths=["/tmp/guia.md"])

    assert directive["action"] == "continue"
    assert "CURUPIRA-PT-PONT-001" in directive["message"]
    assert "/tmp/guia.md:2" in directive["message"]


def test_output_gate_blocks_residual_diagnostics_after_the_repair() -> None:
    hooks = {}

    class Context:
        def register_tool(self, **_registration) -> None:
            pass

        def register_hook(self, name, callback) -> None:
            hooks[name] = callback

        def dispatch_tool(self, _name, _arguments) -> str:
            return json.dumps(
                {
                    "event": "preflight_completed",
                    "status": "needs_review",
                    "exit_code": 1,
                    "files": [
                        {
                            "path": "/tmp/guia.md",
                            "diagnostics": [
                                {
                                    "rule_id": "CURUPIRA-PT-PONT-001",
                                    "location": {
                                        "start_line": 2,
                                        "start_column": 18,
                                    },
                                    "message": "Evite ponto e vírgula.",
                                }
                            ],
                        }
                    ],
                    "operational_errors": [],
                }
            )

    _load_plugin().register(Context())

    directive = hooks["pre_verify"](attempt=1, changed_paths=["/tmp/guia.md"])

    assert directive["action"] == "block_completion"
    assert "diagnóstico residual" in directive["message"]
    assert "CURUPIRA-PT-PONT-001" in directive["message"]


def test_output_gate_blocks_an_operational_preflight_error_without_repair() -> None:
    hooks = {}

    class Context:
        def register_tool(self, **_registration) -> None:
            pass

        def register_hook(self, name, callback) -> None:
            hooks[name] = callback

        def dispatch_tool(self, _name, _arguments) -> str:
            return json.dumps(
                {
                    "event": "preflight_completed",
                    "status": "blocked",
                    "exit_code": 2,
                    "files": [],
                    "operational_errors": [
                        {
                            "code": "curupira_not_found",
                            "message": "executável não encontrado",
                        }
                    ],
                }
            )

    _load_plugin().register(Context())

    directive = hooks["pre_verify"](attempt=0, changed_paths=["/tmp/guia.md"])

    assert directive["action"] == "block_completion"
    assert "erro operacional" in directive["message"]
    assert "curupira_not_found" in directive["message"]


def test_output_gate_fails_closed_when_tool_dispatch_crashes() -> None:
    hooks = {}

    class Context:
        def register_tool(self, **_registration) -> None:
            pass

        def register_hook(self, name, callback) -> None:
            hooks[name] = callback

        def dispatch_tool(self, _name, _arguments) -> str:
            raise RuntimeError("registry unavailable")

    _load_plugin().register(Context())

    directive = hooks["pre_verify"](attempt=0, changed_paths=["/tmp/guia.md"])

    assert directive == {
        "action": "block_completion",
        "message": "Curupira output gate failed: tool dispatch error.",
    }


def test_output_gate_fails_closed_without_a_valid_preflight_event() -> None:
    hooks = {}

    class Context:
        def register_tool(self, **_registration) -> None:
            pass

        def register_hook(self, name, callback) -> None:
            hooks[name] = callback

        def dispatch_tool(self, _name, _arguments) -> str:
            return json.dumps({"status": "passed", "exit_code": 0})

    _load_plugin().register(Context())

    directive = hooks["pre_verify"](attempt=0, changed_paths=["/tmp/guia.md"])

    assert directive == {
        "action": "block_completion",
        "message": "Curupira output gate failed: invalid preflight event.",
    }


def test_output_gate_fails_closed_on_inconsistent_status_and_exit_code() -> None:
    hooks = {}

    class Context:
        def register_tool(self, **_registration) -> None:
            pass

        def register_hook(self, name, callback) -> None:
            hooks[name] = callback

        def dispatch_tool(self, _name, _arguments) -> str:
            return json.dumps(
                {
                    "event": "preflight_completed",
                    "status": "passed",
                    "exit_code": 1,
                    "files": [],
                    "operational_errors": [],
                }
            )

    _load_plugin().register(Context())

    directive = hooks["pre_verify"](attempt=0, changed_paths=["/tmp/guia.md"])

    assert directive == {
        "action": "block_completion",
        "message": "Curupira output gate failed: invalid preflight event.",
    }


def test_curupira_lint_blocks_when_the_cli_returns_invalid_json(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "procedimento.md"
    source.write_text("Feche a válvula.\n", encoding="utf-8")
    executable = tmp_path / "curupira"
    executable.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "--version" ]; then echo \'curupira 0.3.0\'; exit 0; fi\n'
        "echo 'not-json'\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))

    payload = json.loads(_load_plugin_tools().handle_curupira_lint({"paths": [str(source)]}))

    assert payload["status"] == "blocked"
    assert payload["exit_code"] == 2
    assert payload["files"][0]["diagnostics"] == []
    assert payload["operational_errors"] == [
        {
            "code": "invalid_curupira_output",
            "path": str(source.resolve()),
            "message": "Curupira não retornou o JSON esperado",
        }
    ]


def test_curupira_lint_blocks_when_the_cli_version_cannot_be_proven(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "procedimento.md"
    source.write_text("Feche a válvula.\n", encoding="utf-8")
    executable = tmp_path / "curupira"
    executable.write_text("#!/bin/sh\nexit 2\n", encoding="utf-8")
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))

    payload = json.loads(_load_plugin_tools().handle_curupira_lint({"paths": [str(source)]}))

    assert payload["status"] == "blocked"
    assert payload["exit_code"] == 2
    assert payload["versions"] == {"wrapper": "1.1.0", "curupira": None}
    assert payload["files"] == []
    assert payload["operational_errors"] == [
        {
            "code": "version_probe_failed",
            "message": "versão do Curupira não pôde ser confirmada",
        }
    ]


def test_curupira_lint_recovers_version_from_a_python_console_script(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "procedimento.md"
    source.write_text("Feche a válvula.\n", encoding="utf-8")
    executable = tmp_path / "curupira"
    python = Path(__file__).parents[2] / ".venv" / "bin" / "python"
    executable.write_text(f"#!{python}\nraise SystemExit(2)\n", encoding="utf-8")
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))

    payload = json.loads(_load_plugin_tools().handle_curupira_lint({"paths": [str(source)]}))

    assert payload["versions"] == {"wrapper": "1.1.0", "curupira": "0.3.0"}
    assert payload["operational_errors"][0]["code"] == "curupira_operational_error"


def test_curupira_lint_blocks_on_timeout_and_still_returns_an_event(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "procedimento.md"
    source.write_text("Feche a válvula.\n", encoding="utf-8")
    module = _load_plugin_tools()
    monkeypatch.setattr(module.shutil, "which", lambda _name: "/usr/bin/curupira")

    def run(command, **kwargs):
        if command[1:] == ["--version"]:
            return subprocess.CompletedProcess(command, 0, "curupira 0.3.0\n", "")
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(module.subprocess, "run", run)

    payload = json.loads(module.handle_curupira_lint({"paths": [str(source)]}))

    assert payload["status"] == "blocked"
    assert payload["exit_code"] == 2
    assert payload["operational_errors"] == [
        {
            "code": "curupira_timeout",
            "path": str(source.resolve()),
            "message": "Curupira excedeu o limite de 30 segundos",
        }
    ]


def test_curupira_lint_blocks_when_the_explicit_config_cannot_be_read(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "procedimento.md"
    source.write_text("Feche a válvula.\n", encoding="utf-8")
    config = tmp_path / "missing.toml"
    monkeypatch.setenv(
        "PATH",
        f"{Path(__file__).parents[2] / '.venv' / 'bin'}{os.pathsep}{os.environ['PATH']}",
    )

    payload = json.loads(
        _load_plugin_tools().handle_curupira_lint(
            {"paths": [str(source)], "config_path": str(config)}
        )
    )

    assert payload["status"] == "blocked"
    assert payload["exit_code"] == 2
    assert payload["config"] == {"path": str(config.resolve()), "sha256": None}
    assert payload["files"] == []
    assert payload["operational_errors"] == [
        {
            "code": "config_read_error",
            "path": str(config.resolve()),
            "message": "configuração não pôde ser lida",
        }
    ]
