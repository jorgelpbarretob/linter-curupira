"""Conservative, lossless Markdown region classifier."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ste_lint.domain import Document
from ste_lint.parsing.core import _check_size, build_document, regions_from_ignored_mask

_FENCE = re.compile(r"^[ ]{0,3}(`{3,}|~{3,})")
_HEADING = re.compile(r"^[ ]{0,3}#{1,6}(?:[ \t]+|$)")
_SETEXT = re.compile(r"^[ ]{0,3}(?:=+|-+)[ \t]*$")
_LIST_MARKER = re.compile(r"^[ ]{0,3}(?:[-+*]|\d+[.)])[ \t]+")
_BLOCKQUOTE = re.compile(r"^[ ]{0,3}>[ \t]?")
_REFERENCE_DEFINITION = re.compile(r"^[ ]{0,3}\[[^]]+\]:[ \t]*\S+")
_HTML_TAG = re.compile(r"</?[A-Za-z][^>]*>")
_HTML_ENTITY = re.compile(r"&(?:#[0-9]+|#[xX][0-9A-Fa-f]+|[A-Za-z][A-Za-z0-9]+);")
_AUTOLINK = re.compile(r"<(?:https?://|mailto:)[^>]+>")
_IMAGE = re.compile(r"!\[[^]\n]*]\([^\n)]*\)")
_LINK = re.compile(r"\[([^]\n]+)]\(([^\n)]*)\)")


@dataclass(frozen=True, slots=True)
class _Line:
    start: int
    end: int
    content_end: int


def parse_markdown(uri: str, text: str) -> Document:
    _check_size(text)
    ignored = bytearray(len(text))
    lines = _lines(text)
    _mark_front_matter(text, lines, ignored)
    _mark_fences(text, lines, ignored)
    _mark_block_markup(text, lines, ignored)
    _mark_inline_markup(text, lines, ignored)
    return build_document(uri, text, regions_from_ignored_mask(text, ignored))


def _lines(text: str) -> tuple[_Line, ...]:
    lines: list[_Line] = []
    offset = 0
    for value in text.splitlines(keepends=True):
        content_end = offset + len(value.rstrip("\r\n"))
        lines.append(_Line(offset, offset + len(value), content_end))
        offset += len(value)
    if offset < len(text):
        lines.append(_Line(offset, len(text), len(text)))
    return tuple(lines)


def _content(text: str, line: _Line) -> str:
    return text[line.start : line.content_end]


def _mark(ignored: bytearray, start: int, end: int) -> None:
    if end > start:
        ignored[start:end] = b"\x01" * (end - start)


def _is_marked(ignored: bytearray, start: int, end: int) -> bool:
    return any(ignored[start:end])


def _mark_front_matter(text: str, lines: tuple[_Line, ...], ignored: bytearray) -> None:
    if not lines or _content(text, lines[0]).strip() != "---":
        return
    for line in lines[1:]:
        if _content(text, line).strip() in {"---", "..."}:
            _mark(ignored, 0, line.end)
            return


def _mark_fences(text: str, lines: tuple[_Line, ...], ignored: bytearray) -> None:
    index = 0
    while index < len(lines):
        line = lines[index]
        if _is_marked(ignored, line.start, line.end):
            index += 1
            continue
        match = _FENCE.match(_content(text, line))
        if match is None:
            index += 1
            continue
        marker = match.group(1)
        end = len(text)
        closing_index = len(lines)
        for candidate_index in range(index + 1, len(lines)):
            candidate = _content(text, lines[candidate_index]).lstrip(" ")
            is_closing_fence = (
                candidate.startswith(marker[0] * len(marker))
                and not candidate.strip(marker[0]).strip()
            )
            if is_closing_fence:
                end = lines[candidate_index].end
                closing_index = candidate_index + 1
                break
        _mark(ignored, line.start, end)
        index = closing_index


def _mark_block_markup(text: str, lines: tuple[_Line, ...], ignored: bytearray) -> None:
    for index, line in enumerate(lines):
        if _is_marked(ignored, line.start, line.end):
            continue
        content = _content(text, line)
        if _HEADING.match(content) or _REFERENCE_DEFINITION.match(content):
            _mark(ignored, line.start, line.end)
            continue
        if content.startswith("    ") or content.startswith("\t"):
            _mark(ignored, line.start, line.end)
            continue
        if index + 1 < len(lines) and _SETEXT.match(_content(text, lines[index + 1])):
            _mark(ignored, line.start, lines[index + 1].end)
            continue
        list_match = _LIST_MARKER.match(content)
        if list_match is not None:
            _mark(ignored, line.start, line.start + list_match.end())
        quote_match = _BLOCKQUOTE.match(content)
        if quote_match is not None:
            _mark(ignored, line.start, line.start + quote_match.end())

    index = 0
    while index + 1 < len(lines):
        header = _content(text, lines[index])
        delimiter = _content(text, lines[index + 1])
        if "|" not in header or not _is_table_delimiter(delimiter):
            index += 1
            continue
        end_index = index + 2
        while end_index < len(lines) and "|" in _content(text, lines[end_index]):
            end_index += 1
        _mark(ignored, lines[index].start, lines[end_index - 1].end)
        index = end_index


def _is_table_delimiter(value: str) -> bool:
    stripped = value.strip().strip("|")
    cells = [cell.strip() for cell in stripped.split("|")]
    return len(cells) >= 2 and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def _mark_inline_markup(text: str, lines: tuple[_Line, ...], ignored: bytearray) -> None:
    for line in lines:
        content = _content(text, line)
        for pattern in (_AUTOLINK, _IMAGE, _HTML_TAG, _HTML_ENTITY):
            for match in pattern.finditer(content):
                _mark(ignored, line.start + match.start(), line.start + match.end())
        for match in _LINK.finditer(content):
            absolute_start = line.start + match.start()
            label_start = line.start + match.start(1)
            label_end = line.start + match.end(1)
            absolute_end = line.start + match.end()
            _mark(ignored, absolute_start, label_start)
            _mark(ignored, label_end, absolute_end)
        _mark_code_spans(content, line.start, ignored)
        for offset, character in enumerate(content):
            absolute = line.start + offset
            if ignored[absolute]:
                continue
            is_escape = character == "\\" and offset + 1 < len(content)
            is_delimiter = character in "*_~" and _is_markup_delimiter(content, offset)
            if is_escape or is_delimiter:
                _mark(ignored, absolute, absolute + 1)


def _mark_code_spans(content: str, line_start: int, ignored: bytearray) -> None:
    offset = 0
    while offset < len(content):
        if content[offset] != "`":
            offset += 1
            continue
        run_end = offset + 1
        while run_end < len(content) and content[run_end] == "`":
            run_end += 1
        marker = content[offset:run_end]
        closing = content.find(marker, run_end)
        if closing < 0:
            _mark(ignored, line_start + offset, line_start + run_end)
            offset = run_end
            continue
        _mark(ignored, line_start + offset, line_start + closing + len(marker))
        offset = closing + len(marker)


def _is_markup_delimiter(content: str, offset: int) -> bool:
    before = content[offset - 1] if offset else " "
    after = content[offset + 1] if offset + 1 < len(content) else " "
    return before.isspace() or after.isspace() or before in "([{" or after in ".,;:!?)]}"
