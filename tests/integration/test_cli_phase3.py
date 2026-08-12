import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from ste_lint.cli import main
from ste_lint.domain import (
    Diagnostic,
    RuleContext,
    RuleId,
    RuleKind,
    RuleMetadata,
    RuleRegistry,
    Severity,
    SourceReference,
    TextSpan,
)


def metadata() -> RuleMetadata:
    return RuleMetadata(
        rule_id=RuleId("PROJECT-TEST-001"),
        title="Synthetic project rule",
        source=SourceReference(standard="PROJECT", issue="1", locator="local-test"),
        kind=RuleKind.DETERMINISTIC,
        default_severity=Severity.WARNING,
        summary="A synthetic CLI test.",
        implementation_status="stable",
    )


@dataclass
class CliRule:
    metadata: RuleMetadata
    emit: bool = True
    error: Exception | None = None
    seen_text: str | None = field(default=None, init=False)
    calls: int = field(default=0, init=False)

    def check(self, context: RuleContext) -> Iterable[Diagnostic]:
        self.calls += 1
        self.seen_text = context.document.text
        if self.error is not None:
            raise self.error
        if not self.emit:
            return ()
        return (
            Diagnostic(
                rule_id=self.metadata.rule_id,
                source=self.metadata.source,
                severity=Severity.WARNING,
                location=context.document.location(TextSpan(0, 1)),
                message="Synthetic message.",
                explanation="Synthetic explanation.",
            ),
        )


def registry_with(rule: CliRule) -> RuleRegistry:
    registry = RuleRegistry((rule.metadata,))
    registry.register(rule)
    return registry


def write_utf8(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        stream.write(text)


def test_cli_returns_zero_and_versioned_json_with_no_rules(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "manual.txt"
    write_utf8(source, "Synthetic text.\n")

    exit_code = main(["lint", str(source), "--format", "json"])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == {
        "schema_version": "1.0",
        "diagnostics": [],
    }


def test_cli_returns_one_for_valid_diagnostics_and_preserves_crlf(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "manual.txt"
    write_utf8(source, "A\r\nB\r\n")
    rule = CliRule(metadata())

    exit_code = main(["lint", str(source)], registry=registry_with(rule))

    assert exit_code == 1
    assert rule.seen_text == "A\r\nB\r\n"
    output = capsys.readouterr().out
    assert "warning PROJECT-TEST-001" in output
    assert "explanation: Synthetic explanation." in output


def test_cli_config_can_disable_rule_before_execution(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "manual.txt"
    config = tmp_path / "ste-lint.toml"
    write_utf8(source, "Synthetic text.\n")
    write_utf8(
        config,
        'schema_version = 1\n[rules]\ndisable = ["PROJECT-TEST-001"]\n',
    )
    rule = CliRule(metadata())

    exit_code = main(["lint", str(source), "--config", str(config)], registry=registry_with(rule))

    assert exit_code == 0
    assert rule.calls == 0
    assert capsys.readouterr().out == "No executable rules are enabled.\n"


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        (["lint", "missing.txt"], "operational error"),
        (["lint", "manual.txt", "--enable-rule", "PROJECT-UNKNOWN-999"], "unknown rule_id"),
    ],
)
def test_cli_returns_two_for_operational_input_errors(
    arguments: list[str], message: str, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main(arguments)

    assert exit_code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert message in captured.err


def test_cli_rejects_existing_unsupported_format(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "manual.pdf"
    write_utf8(source, "Synthetic text.\n")

    assert main(["lint", str(source)]) == 2
    assert "not supported" in capsys.readouterr().err


def test_cli_returns_two_and_identifies_rule_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "manual.txt"
    write_utf8(source, "Synthetic text.\n")
    rule = CliRule(metadata(), error=RuntimeError("synthetic failure"))

    exit_code = main(["lint", str(source)], registry=registry_with(rule))

    assert exit_code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "PROJECT-TEST-001" in captured.err
    assert "synthetic failure" not in captured.err
