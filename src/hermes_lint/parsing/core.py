"""Mecânica compartilhada do parser lossless."""

from __future__ import annotations

import re
from pathlib import PurePath

from hermes_lint.domain import Document, RegionKind, Sentence, TextRegion, TextSpan, Token

MAX_DOCUMENT_CHARS = 1_000_000
_TOKEN_PATTERN = re.compile(r"\s+|[\w]+(?:[-'][\w]+)*|[^\w\s]", re.UNICODE)


class UnsupportedFormatError(ValueError):
    """Indica ausência de adapter para o formato solicitado."""


class DocumentTooLargeError(ValueError):
    """Indica documento acima do limite determinístico."""


def _check_size(text: str) -> None:
    if len(text) > MAX_DOCUMENT_CHARS:
        raise DocumentTooLargeError(
            f"documento excede o máximo de {MAX_DOCUMENT_CHARS} pontos de código Unicode"
        )


def parse_document(uri: str, text: str) -> Document:
    suffix = PurePath(uri).suffix.lower()
    if suffix == ".txt":
        return parse_text(uri, text)
    if suffix in {".md", ".markdown"}:
        from hermes_lint.parsing.markdown import parse_markdown

        return parse_markdown(uri, text)
    raise UnsupportedFormatError(f"formato {suffix or '<sem extensão>'} não suportado")


def parse_text(uri: str, text: str) -> Document:
    _check_size(text)
    regions = (
        (TextRegion(TextSpan(0, len(text)), RegionKind.LINTABLE, "plain-text"),) if text else ()
    )
    return build_document(uri, text, regions)


def build_document(uri: str, text: str, regions: tuple[TextRegion, ...]) -> Document:
    tokens = _tokenize(text, regions)
    sentences = _sentences(tokens)
    return Document(uri=uri, text=text, regions=regions, tokens=tokens, sentences=sentences)


def regions_from_ignored_mask(text: str, ignored: bytearray) -> tuple[TextRegion, ...]:
    if not text:
        return ()
    regions: list[TextRegion] = []
    start = 0
    current = ignored[0]
    for offset in range(1, len(text)):
        if ignored[offset] == current:
            continue
        kind = RegionKind.IGNORED if current else RegionKind.LINTABLE
        reason = "markdown" if current else "prose"
        regions.append(TextRegion(TextSpan(start, offset), kind, reason))
        start = offset
        current = ignored[offset]
    kind = RegionKind.IGNORED if current else RegionKind.LINTABLE
    reason = "markdown" if current else "prose"
    regions.append(TextRegion(TextSpan(start, len(text)), kind, reason))
    return tuple(regions)


def _tokenize(text: str, regions: tuple[TextRegion, ...]) -> tuple[Token, ...]:
    tokens: list[Token] = []
    for region in regions:
        fragment = text[region.span.start_offset : region.span.end_offset]
        for match in _TOKEN_PATTERN.finditer(fragment):
            start = region.span.start_offset + match.start()
            end = region.span.start_offset + match.end()
            tokens.append(Token(TextSpan(start, end), match.group(), region.kind))
    return tuple(tokens)


def _sentences(tokens: tuple[Token, ...]) -> tuple[Sentence, ...]:
    sentences: list[Sentence] = []
    current: list[Token] = []
    for token in tokens:
        if token.kind is RegionKind.IGNORED:
            continue
        current.append(token)
        if token.text in {".", "!", "?"}:
            sentence = _make_sentence(current, is_complete=True)
            if sentence is not None:
                sentences.append(sentence)
            current = []
    sentence = _make_sentence(current, is_complete=False)
    if sentence is not None:
        sentences.append(sentence)
    return tuple(sentences)


def _make_sentence(tokens: list[Token], *, is_complete: bool) -> Sentence | None:
    while tokens and tokens[0].text.isspace():
        tokens.pop(0)
    while tokens and tokens[-1].text.isspace():
        tokens.pop()
    if not tokens:
        return None
    parts: list[TextSpan] = []
    for token in tokens:
        if parts and parts[-1].end_offset == token.span.start_offset:
            parts[-1] = TextSpan(parts[-1].start_offset, token.span.end_offset)
        else:
            parts.append(token.span)
    return Sentence(tuple(parts), is_complete=is_complete)
