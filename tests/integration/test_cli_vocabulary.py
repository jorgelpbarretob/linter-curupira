import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
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
)
from ste_lint.vocabulary import Vocabulary, parse_resource


def write_bytes(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def synthetic_source() -> bytes:
    return json.dumps(
        {
            "format": "ste-lint-vocabulary-source",
            "schema_version": 1,
            "standard": "ASD-STE100",
            "issue": "9",
            "entries": [
                {
                    "term": "flux valve",
                    "part_of_speech": "synthetic-noun",
                    "meaning_id": "synthetic-1",
                    "case_sensitive": False,
                }
            ],
        },
        separators=(",", ":"),
    ).encode()


def test_import_json_requires_authorization_and_writes_atomic_cache(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "authorized-source.json"
    cache = tmp_path / "cache"
    raw = synthetic_source()
    write_bytes(source, raw)

    assert main(["vocabulary", "import-json", str(source), "--cache-dir", str(cache)]) == 2
    assert "--confirm-authorized" in capsys.readouterr().err

    exit_code = main(
        [
            "vocabulary",
            "import-json",
            str(source),
            "--cache-dir",
            str(cache),
            "--confirm-authorized",
        ]
    )

    expected = cache / f"{hashlib.sha256(raw).hexdigest()}.json"
    assert exit_code == 0
    assert str(expected) in capsys.readouterr().out
    assert parse_resource(expected.read_bytes()).entries[0].term == "flux valve"
    assert not list(cache.glob(".*.tmp"))


@dataclass(frozen=True)
class VocabularyCapabilityRule:
    metadata: RuleMetadata

    def check(self, context: RuleContext) -> Iterable[Diagnostic]:
        vocabulary = context.capabilities["vocabulary"]
        assert isinstance(vocabulary, Vocabulary)
        assert vocabulary.lookup("FLUX VALVE").status == "matched"
        assert vocabulary.lookup("LOCAL TERM").status == "technical"
        return ()


def capability_registry() -> RuleRegistry:
    metadata = RuleMetadata(
        rule_id=RuleId("PROJECT-VOCAB-TEST-001"),
        title="Synthetic vocabulary capability",
        source=SourceReference("PROJECT", "1", "synthetic-test"),
        kind=RuleKind.DETERMINISTIC,
        default_severity=Severity.INFO,
        summary="Tests vocabulary composition without a normative diagnostic.",
        implementation_status="stable",
    )
    registry = RuleRegistry((metadata,))
    registry.register(VocabularyCapabilityRule(metadata))
    return registry


def test_lint_loads_config_relative_vocabulary_and_overlay(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "authorized-source.json"
    cache = tmp_path / "project" / "cache"
    write_bytes(source, synthetic_source())
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
    capsys.readouterr()
    resource = next(cache.glob("*.json"))
    document = tmp_path / "manual.txt"
    document.write_text("Synthetic text.\n", encoding="utf-8", newline="")
    config = tmp_path / "project" / "ste-lint.toml"
    config.write_text(
        "schema_version = 1\n"
        "[glossary]\n"
        'terms = ["local term"]\n'
        "[vocabulary]\n"
        f'path = "cache/{resource.name}"\n',
        encoding="utf-8",
        newline="",
    )

    exit_code = main(
        ["lint", str(document), "--config", str(config)],
        registry=capability_registry(),
    )

    assert exit_code == 0
    assert "No violations were detected" in capsys.readouterr().out


def test_explicit_invalid_vocabulary_fails_before_rules(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    document = tmp_path / "manual.txt"
    document.write_text("Synthetic text.\n", encoding="utf-8", newline="")

    assert main(["lint", str(document), "--vocabulary", str(tmp_path / "missing.json")]) == 2
    error = capsys.readouterr().err
    assert "vocabulary" in error
    assert "missing.json" in error


def test_explicit_vocabulary_is_validated_before_document_read(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing_vocabulary = tmp_path / "missing-vocabulary.json"

    exit_code = main(
        [
            "lint",
            str(tmp_path / "missing-document.txt"),
            "--vocabulary",
            str(missing_vocabulary),
        ]
    )

    assert exit_code == 2
    assert "missing-vocabulary.json" in capsys.readouterr().err


def test_cli_vocabulary_overrides_invalid_project_path(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "source.json"
    cache = tmp_path / "cache"
    write_bytes(source, synthetic_source())
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
    capsys.readouterr()
    resource = next(cache.glob("*.json"))
    document = tmp_path / "manual.txt"
    document.write_text("Synthetic text.\n", encoding="utf-8", newline="")
    config = tmp_path / "ste-lint.toml"
    config.write_text(
        "schema_version = 1\n"
        "[glossary]\n"
        'terms = ["local term"]\n'
        "[vocabulary]\n"
        'path = "missing.json"\n',
        encoding="utf-8",
        newline="",
    )

    exit_code = main(
        [
            "lint",
            str(document),
            "--config",
            str(config),
            "--vocabulary",
            str(resource),
        ],
        registry=capability_registry(),
    )

    assert exit_code == 0
    assert "No violations were detected" in capsys.readouterr().out


def test_import_rejects_wrong_issue_without_creating_cache(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "wrong-issue.json"
    cache = tmp_path / "cache"
    write_bytes(source, synthetic_source().replace(b'"issue":"9"', b'"issue":"8"'))

    exit_code = main(
        [
            "vocabulary",
            "import-json",
            str(source),
            "--cache-dir",
            str(cache),
            "--confirm-authorized",
        ]
    )

    assert exit_code == 2
    assert "issue" in capsys.readouterr().err
    assert not cache.exists()
