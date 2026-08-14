import ast
from dataclasses import replace
from pathlib import Path

import pytest

from hermes_lint.catalog import RULE_CATALOG, build_registry
from hermes_lint.domain import CatalogMismatchError, RegionKind
from hermes_lint.parsing import parse_document


def test_parser_preserves_unicode_crlf_and_excludes_supported_markdown() -> None:
    text = (
        "Café pronto; prossiga.\r\n"
        "Use `chave;valor` e abra [a página](https://example.invalid/?a=1;b=2).\r\n"
        "```text\r\nignorado; código\r\n```\r\n"
    )

    document = parse_document("procedimento.md", text)

    assert document.text == text
    assert "Café pronto; prossiga." in document.lintable_text
    for ignored in ("chave;valor", "https://example.invalid", "ignorado; código"):
        assert document.kind_at(text.index(ignored)) is RegionKind.IGNORED
    semicolon = text.index(";")
    location = document.location(document.tokens[3].span)
    assert (location.start_offset, location.start_line) == (semicolon, 1)


def test_catalog_contains_only_the_authorial_hermes_namespace() -> None:
    assert [metadata.rule_id for metadata in RULE_CATALOG] == ["HERMES-PT-PONT-001"]
    assert all(metadata.source.standard == "Hermes" for metadata in RULE_CATALOG)


def test_registry_rejects_an_english_rule_namespace() -> None:
    english = replace(RULE_CATALOG[0], rule_id="STE-I9-PUNCT-001")

    with pytest.raises(CatalogMismatchError, match="namespace"):
        type(build_registry())((english,))


def test_hermes_package_does_not_import_the_frozen_english_package() -> None:
    offenders: list[str] = []
    for path in Path("src/hermes_lint").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            else:
                continue
            if any(name == "ste_lint" or name.startswith("ste_lint.") for name in names):
                offenders.append(str(path))
    assert offenders == []
