#!/usr/bin/env python3
"""Independent, count-only scanner for product-evidence Round 2.

This program intentionally lives outside the product package. It audits frozen
Git snapshots before counting superinclusive review units and never emits source
text or ground-truth labels.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from bisect import bisect_right
from contextlib import suppress
from pathlib import Path
from typing import NamedTuple

SEED = "ste-lint-product-evidence-r2-2026-08-13"
EXPECTED_WORDS = 21_972
EXPECTED_MANIFEST_SHA256 = "4f09744c7eb7e1f460e68f4185b478037a4ee4500fb329bd5a62dc74cddd73a3"
SCHEMA_VERSION = "ste-lint-product-evidence-inventory/v1"
ROUND_ID = "round-2-2026-08-13"
INVENTORY_A = Path("/tmp/ste-lint-product-evidence-round2-inventory-a.jsonl")
INVENTORY_B = Path("/tmp/ste-lint-product-evidence-round2-inventory-b.jsonl")

type JsonValue = str | int | bool | list[str]
type Record = dict[str, JsonValue]


class AuditError(RuntimeError):
    """Raised before scanning when a frozen input diverges."""


class Source(NamedTuple):
    source_id: str
    commit: str
    path_prefix: str
    license_sha256: str
    default_root: str


class Frame(NamedTuple):
    source_id: str
    text_type: str
    path: str
    tree: str


class Document(NamedTuple):
    source_id: str
    text_type: str
    key: str
    sha256: str
    path: str


class ScanCounts(NamedTuple):
    sentence_complete: int
    sentence_incomplete: int
    paragraphs: int
    punctuation: int
    list_runs: int

    @property
    def sentence_units(self) -> int:
        return self.sentence_complete + self.sentence_incomplete


class ProjectionData(NamedTuple):
    projection: str
    lines: list[str]
    line_starts: list[int]
    content_ends: list[int]
    structural: list[bool]
    line_kinds: list[str]
    uncertain_lines: list[bool]
    uncertain_positions: list[bool]


class Block(NamedTuple):
    kind: str
    start: int
    end: int
    first_line: int
    last_line: int
    uncertain: bool


class ListRun(NamedTuple):
    start: int
    end: int
    first_line: int
    last_line: int
    indentation: int
    marker_family: str
    peer_count: int


SOURCES = {
    "dapr": Source(
        "dapr",
        "f337722b406a95ae9fab932f1294b09f824ca20f",
        "daprdocs/",
        "0b9cab20a5e2ae7e44f40a5ee6b8416f12d2135a547f9fef00e5b61f8d5be99a",
        "/tmp/ste-round2-dapr-docs",
    ),
    "otel": Source(
        "otel",
        "8d47fa1c9303ae1e1807e1c7a122720ba62986ed",
        "content/",
        "6f9997b6f85f473f853aeef19b5f16504dd228ba99cee70e5a19211df947a2b3",
        "/tmp/ste-round2-opentelemetry-docs",
    ),
}

FRAMES = (
    Frame(
        "dapr",
        "procedural",
        "daprdocs/content/en/getting-started/quickstarts",
        "36db4ace5247d22f79ccca15e1d65d288ed64ad0",
    ),
    Frame(
        "dapr",
        "descriptive",
        "daprdocs/content/en/concepts",
        "3aa1d6e6cc5f1a716e5926200700f59e75e6fa57",
    ),
    Frame(
        "otel",
        "procedural",
        "content/en/docs/zero-code",
        "b63291ce569cfda5c26e8b841e7834e6a604a703",
    ),
    Frame(
        "otel",
        "descriptive",
        "content/en/docs/concepts",
        "9be2405d69bc114e6d0d3227232e32664a88b109",
    ),
)

DOCUMENTS = (
    Document(
        "dapr",
        "procedural",
        "6f33fbe189b24db4be04d1215c4c4500c4901d019d67f47ffac8bebfc2e898c0",
        "bbd806d2d7299bb3db37f1114f21386636f8e9ecd584ff952ddc2760f7fcab15",
        "daprdocs/content/en/getting-started/quickstarts/configuration-quickstart.md",
    ),
    Document(
        "dapr",
        "procedural",
        "e4c08ee46b9ed8cc0da62d48ff39dc9abcb16a7347163008f5323fbc111b13cc",
        "437d6011195d9fc3a3ce9cc2fba4c84b5ba9396d47e43b91bd78dbdeb2de2c86",
        "daprdocs/content/en/getting-started/quickstarts/jobs-quickstart.md",
    ),
    Document(
        "dapr",
        "procedural",
        "eb7002bdaa5fd02056f31f19a1c95152d6fa9c64a547363aeadf37ba2d306649",
        "70c54a69d452325b8518c275950929a609287c6f88b05f3fb53e7a7458b87368",
        "daprdocs/content/en/getting-started/quickstarts/cryptography-quickstart.md",
    ),
    Document(
        "dapr",
        "procedural",
        "f3aef296165938d91d512b24fc7f1f25a477b90257e1497a21fd35a939e5fb99",
        "324ead76d29eb3d7d633a3a497aef55f8b1b15d9e2192878de6c140759d2341d",
        "daprdocs/content/en/getting-started/quickstarts/secrets-quickstart.md",
    ),
    Document(
        "dapr",
        "descriptive",
        "0ac18827deb60c2bb384de1ff77d238c99b8b44ea02706c299f9067512e94ee9",
        "ba9b586529b557d632eb243f79579bbd97d63737da102b53e616272947cf6a4c",
        "daprdocs/content/en/concepts/dapr-services/sidecar.md",
    ),
    Document(
        "dapr",
        "descriptive",
        "1bdd674e17723787557c9e329f133a42caa4e9a6424f447022db18b8ed5a299b",
        "daad265b1c8c82049f9c21a040b2919a4a5766b037708df027d657c2dad18921",
        "daprdocs/content/en/concepts/dapr-services/placement.md",
    ),
    Document(
        "dapr",
        "descriptive",
        "3f6c3aa4e6ffd445964f7fa1ff6932678362f510836c2cd3f5dffde8c826c07e",
        "5b2964a8877088595b0fcb9b6e1ae97aca20bbdde2ace4dbcffee1f13b8ad681",
        "daprdocs/content/en/concepts/terminology.md",
    ),
    Document(
        "dapr",
        "descriptive",
        "4395e0386c63aa8669a5ade49a96e4a78eb961cffd1ed90ca411cb0de1339dfe",
        "8caa7f174fb59fca65a6062dcf43a13cea65daff474c3e242c8f6a664c7bfa41",
        "daprdocs/content/en/concepts/dapr-services/sidecar-injector.md",
    ),
    Document(
        "otel",
        "procedural",
        "003f884207e3de150e975a3ed1642fde0bdac017ddf1a3e4f814fc07e1099404",
        "175c9288d30c0152ab769d4910e9a8af86a9cee57970b9eb8015f2413cee41e0",
        "content/en/docs/zero-code/obi/configure/service-discovery.md",
    ),
    Document(
        "otel",
        "procedural",
        "007da80080793cedc35b811641fa105f50765f9b850bfe11a14d155164e4489d",
        "ab7dd019d7e8390a09d0e6ff537be23cadcbc7af3cbe463ae341209627b074f0",
        "content/en/docs/zero-code/obi/configure/routes-decorator.md",
    ),
    Document(
        "otel",
        "procedural",
        "01a0ef561a05af0209028eb7bcf82b54dafe9e964aa777b0654323160649d161",
        "b47335a58308ce3e9916dbe6f4646b8c1c7e264c4c9c66bf02eb4dc2b564ad1f",
        "content/en/docs/zero-code/dotnet/instrumentations.md",
    ),
    Document(
        "otel",
        "procedural",
        "081289a86519f06dfd689cd22d0ab06de416b9bb27a53b7756f106727c799d30",
        "7e608d18914d942e344bb8ae6f27a9c1c349ff172768b95f272ec06c4082b674",
        "content/en/docs/zero-code/obi/network/config.md",
    ),
    Document(
        "otel",
        "descriptive",
        "0e29d15cd094193b1eebc4c0f34627d38fc4e8e5c83fac4e2336286d6603b280",
        "20950feea860a7ce64b1d51b7e96e95f1bafb354f6a8e35021eb0ca058c2427d",
        "content/en/docs/concepts/signals/logs.md",
    ),
    Document(
        "otel",
        "descriptive",
        "27bb342a0c01d87ae6f7111a107afa9d25ca8e2a9898e9d107096dfd6fdb5e3f",
        "e114163e1eecc33e146a502784c484ca482648a1f278c24ab4809262d2cc0061",
        "content/en/docs/concepts/signals/traces.md",
    ),
    Document(
        "otel",
        "descriptive",
        "29b48f40f7e1b9b29b16ffa45206eed4bf0be7dcd21ff8bfe5eaf9c236cd0c50",
        "03201825a7fa873f107834e36a34c180dfd95a2798ace2c14987740b707bcaac",
        "content/en/docs/concepts/distributions.md",
    ),
    Document(
        "otel",
        "descriptive",
        "4487b57e5fa23c10dd319c9fe52928369e98fb52dd62515c5df2c75f05244007",
        "73df1da94d246ce1a2a9dfc2a97bd10a73740a1135d4bfbe1acf7977fa26ac92",
        "content/en/docs/concepts/instrumentation/code-based.md",
    ),
)

CAPS = {
    "STE-I9-SENT-001": 650,
    "STE-I9-SENT-002": 650,
    "STE-I9-PARA-001": 300,
    "STE-I9-PUNCT-001": 200,
    "STE-I9-LIST-001": 200,
}

EXPECTED_INVENTORY_COUNTS = {
    "STE-I9-SENT-001": 558,
    "STE-I9-SENT-002": 329,
    "STE-I9-PARA-001": 144,
    "STE-I9-PUNCT-001": 69,
    "STE-I9-LIST-001": 73,
}

SENT001_EXCLUDED_PATHS = frozenset(
    {
        "daprdocs/content/en/getting-started/quickstarts/secrets-quickstart.md",
    }
)

_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_ATX = re.compile(r"^ {0,3}#{1,6}(?:\s|$)")
_SETEXT = re.compile(r"^ {0,3}(?:=+|-+)\s*$")
_THEMATIC = re.compile(r"^ {0,3}(?:(?:\*\s*){3,}|(?:-\s*){3,}|(?:_\s*){3,})$")
_REFERENCE = re.compile(r"^ {0,3}\[[^]]+\]:")
_TABLE_SEPARATOR = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
_LIST_MARKER = re.compile(r"^( *)(?P<marker>(?:[-+*])|(?:\d+[.)]))\s+(?P<body>.*)$")
_BLOCKQUOTE = re.compile(r"^ {0,3}>\s?(.*)$")
_SHORTCODE_ONLY = re.compile(r"^\s*\{\{[<%].*[>%]\}\}\s*$")
_HTML_ONLY = re.compile(r"^\s*</?[A-Za-z][^>]*>\s*$")
_TERMINAL = re.compile(r"[.!?](?=[\"'’”\)\]]*(?:\s|$))")


def selection_key(seed: str, path: str) -> str:
    payload = bytes(f"{seed}|{path}", encoding="utf-8")
    return hashlib.sha256(payload).hexdigest()


def verify_digest(data: bytes, expected: str, label: str) -> str:
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise AuditError(f"{label}: digest mismatch: expected {expected}, got {actual}")
    return actual


def _git(root: Path, *arguments: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *arguments],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise AuditError(f"git audit failed for {root}: {error}") from error
    return result.stdout.strip()


def _structural_mask(lines: list[str]) -> list[bool]:
    structural = [False] * len(lines)

    if lines and lines[0].rstrip("\r\n") == "---":
        structural[0] = True
        for index in range(1, len(lines)):
            structural[index] = True
            if lines[index].rstrip("\r\n") in {"---", "..."}:
                break

    fence_char = ""
    fence_size = 0
    in_comment = False
    for index, raw_line in enumerate(lines):
        line = raw_line.rstrip("\r\n")
        if structural[index]:
            continue

        if in_comment:
            structural[index] = True
            if "-->" in line:
                in_comment = False
            continue

        if "<!--" in line:
            structural[index] = True
            if "-->" not in line.split("<!--", maxsplit=1)[1]:
                in_comment = True
            continue

        fence = _FENCE.match(line)
        if fence_char:
            structural[index] = True
            token = fence.group(1) if fence else ""
            if token.startswith(fence_char) and len(token) >= fence_size:
                fence_char = ""
                fence_size = 0
            continue
        if fence:
            token = fence.group(1)
            fence_char = token[0]
            fence_size = len(token)
            structural[index] = True
            continue

        if (
            _ATX.match(line)
            or _THEMATIC.match(line)
            or _REFERENCE.match(line)
            or _SHORTCODE_ONLY.match(line)
            or _HTML_ONLY.match(line)
            or line.startswith("    ")
            or line.startswith("\t")
        ):
            structural[index] = True

    for index in range(1, len(lines)):
        line = lines[index].rstrip("\r\n")
        if not structural[index] and _SETEXT.match(line) and lines[index - 1].strip():
            structural[index] = True
            structural[index - 1] = True
        if not structural[index] and _TABLE_SEPARATOR.match(line):
            structural[index] = True
            structural[index - 1] = True
            following = index + 1
            while following < len(lines) and "|" in lines[following] and lines[following].strip():
                structural[following] = True
                following += 1

    return structural


def _replace_with_spaces(match: re.Match[str]) -> str:
    return " " * len(match.group(0))


def _keep_link_label(match: re.Match[str]) -> str:
    return match.group(1) + (" " * (len(match.group(0)) - len(match.group(1))))


def _clean_inline(text: str) -> str:
    text = re.sub(r"!\[[^]]*\]\([^)]*\)", _replace_with_spaces, text)
    text = re.sub(r"`+[^`]*`+", _replace_with_spaces, text)
    text = re.sub(r"<(?:(?:https?|mailto):)[^>]+>", _replace_with_spaces, text)
    text = re.sub(r"\[([^]]+)]\([^)]*\)", _keep_link_label, text)
    text = re.sub(r"\[([^]]+)]\[[^]]*]", _keep_link_label, text)
    text = re.sub(r"\{\{[<%].*?[>%]\}\}", _replace_with_spaces, text)
    text = re.sub(r"</?[A-Za-z][^>]*>", _replace_with_spaces, text)
    text = re.sub(r"&(?:#[0-9]+|#x[0-9A-Fa-f]+|[A-Za-z][A-Za-z0-9]+);", " ", text)
    return text


def _validate_newlines(text: str) -> None:
    forbidden = {"\v", "\f", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"}
    if any(character in text for character in forbidden):
        raise AuditError("unsupported Unicode line separator")
    for index, character in enumerate(text):
        if character == "\r" and (index + 1 == len(text) or text[index + 1] != "\n"):
            raise AuditError("unsupported isolated CR line separator")


def _line_layout(text: str) -> tuple[list[str], list[int], list[int]]:
    _validate_newlines(text)
    lines = text.splitlines(keepends=True)
    starts: list[int] = []
    content_ends: list[int] = []
    offset = 0
    for line in lines:
        starts.append(offset)
        content_end = offset + len(line)
        if line.endswith("\n"):
            content_end -= 1
            if content_end > offset and text[content_end - 1] == "\r":
                content_end -= 1
        content_ends.append(content_end)
        offset += len(line)
    if not lines and text:
        raise AuditError("line partition failed")
    return lines, starts, content_ends


def _mark_line_range(
    structural: list[bool], line_kinds: list[str], start: int, end: int, kind: str
) -> None:
    for index in range(start, end + 1):
        structural[index] = True
        line_kinds[index] = kind


def _classify_projection_lines(
    lines: list[str],
) -> tuple[list[bool], list[str], list[bool]]:
    structural = [False] * len(lines)
    line_kinds = ["visible"] * len(lines)
    uncertain = [False] * len(lines)

    if lines and lines[0].rstrip("\r\n") == "---":
        closing = next(
            (
                index
                for index in range(1, len(lines))
                if lines[index].rstrip("\r\n") in {"---", "..."}
            ),
            None,
        )
        if closing is None:
            uncertain = [True] * len(lines)
        else:
            _mark_line_range(structural, line_kinds, 0, closing, "front_matter")

    index = 0
    while index < len(lines):
        if structural[index]:
            index += 1
            continue
        line = lines[index].rstrip("\r\n")
        fence = _FENCE.match(line)
        if fence:
            token = fence.group(1)
            closing = next(
                (
                    candidate
                    for candidate in range(index + 1, len(lines))
                    if (match := _FENCE.match(lines[candidate].rstrip("\r\n")))
                    and match.group(1).startswith(token[0])
                    and len(match.group(1)) >= len(token)
                ),
                None,
            )
            if closing is None:
                for candidate in range(index, len(lines)):
                    uncertain[candidate] = True
                index += 1
            else:
                _mark_line_range(structural, line_kinds, index, closing, "fence")
                index = closing + 1
            continue

        if "<!--" in line:
            closing = index if "-->" in line.split("<!--", maxsplit=1)[1] else None
            if closing is None:
                closing = next(
                    (
                        candidate
                        for candidate in range(index + 1, len(lines))
                        if "-->" in lines[candidate]
                    ),
                    None,
                )
            if closing is None:
                for candidate in range(index, len(lines)):
                    uncertain[candidate] = True
                index += 1
            else:
                _mark_line_range(structural, line_kinds, index, closing, "html_comment")
                index = closing + 1
            continue

        kind = ""
        if _ATX.match(line):
            kind = "heading"
        elif _THEMATIC.match(line):
            kind = "thematic_break"
        elif _REFERENCE.match(line):
            kind = "reference_definition"
        elif _SHORTCODE_ONLY.match(line):
            kind = "shortcode"
        elif _HTML_ONLY.match(line):
            kind = "html_block"
        elif line.startswith("    ") or line.startswith("\t"):
            kind = "indented_code"
        if kind and not uncertain[index]:
            structural[index] = True
            line_kinds[index] = kind
        index += 1

    for index in range(1, len(lines)):
        line = lines[index].rstrip("\r\n")
        if (
            not structural[index]
            and not uncertain[index]
            and _SETEXT.match(line)
            and lines[index - 1].strip()
        ):
            _mark_line_range(structural, line_kinds, index - 1, index, "heading")
        if not structural[index] and not uncertain[index] and _TABLE_SEPARATOR.match(line):
            structural[index] = True
            structural[index - 1] = True
            line_kinds[index] = "table"
            line_kinds[index - 1] = "table"
            following = index + 1
            while following < len(lines) and "|" in lines[following] and lines[following].strip():
                structural[following] = True
                line_kinds[following] = "table"
                following += 1

    return structural, line_kinds, uncertain


def _mask(characters: list[str], start: int, end: int) -> None:
    for index in range(start, end):
        if characters[index] not in {"\r", "\n"}:
            characters[index] = " "


def _mask_inline_projection(characters: list[str], raw: str, base: int) -> bool:
    patterns_full = (
        r"!\[[^]]*\]\([^)]*\)",
        r"`+[^`]*`+",
        r"<(?:(?:https?|mailto):)[^>]+>",
        r"\{\{[<%].*?[>%]\}\}",
        r"</?[A-Za-z][^>]*>",
        r"&(?:#[0-9]+|#x[0-9A-Fa-f]+|[A-Za-z][A-Za-z0-9]+);",
    )
    for pattern in patterns_full:
        for match in re.finditer(pattern, raw):
            _mask(characters, base + match.start(), base + match.end())

    for pattern in (r"\[([^]]+)]\([^)]*\)", r"\[([^]]+)]\[[^]]*]"):
        for match in re.finditer(pattern, raw):
            label_start, label_end = match.span(1)
            _mask(characters, base + match.start(), base + label_start)
            _mask(characters, base + label_end, base + match.end())

    backtick_runs = re.findall(r"`+", raw)
    uncertain = len(backtick_runs) % 2 == 1
    uncertain = uncertain or raw.count("{{") != raw.count("}}")
    return uncertain


def build_projection(text: str) -> ProjectionData:
    lines, starts, content_ends = _line_layout(text)
    structural, line_kinds, uncertain_lines = _classify_projection_lines(lines)
    characters = list(text)
    uncertain_positions = [False] * len(text)

    for index, _line in enumerate(lines):
        start = starts[index]
        end = content_ends[index]
        raw = text[start:end]
        if structural[index]:
            _mask(characters, start, end)
            continue

        list_marker = _LIST_MARKER.match(raw)
        quote = _BLOCKQUOTE.match(raw)
        if list_marker:
            body_start = list_marker.start("body")
            _mask(characters, start, start + body_start)
        elif quote:
            body_start = quote.start(1)
            _mask(characters, start, start + body_start)

        if _mask_inline_projection(characters, raw, start):
            uncertain_lines[index] = True
        if uncertain_lines[index]:
            for position in range(start, end):
                uncertain_positions[position] = True

    return ProjectionData(
        projection="".join(characters),
        lines=lines,
        line_starts=starts,
        content_ends=content_ends,
        structural=structural,
        line_kinds=line_kinds,
        uncertain_lines=uncertain_lines,
        uncertain_positions=uncertain_positions,
    )


def _extract_blocks(data: ProjectionData) -> list[Block]:
    blocks: list[Block] = []
    kind = ""
    first_line = -1
    last_line = -1
    marker_indent = -1
    block_uncertain = False

    def flush() -> None:
        nonlocal kind, first_line, last_line, marker_indent, block_uncertain
        if first_line >= 0:
            start = data.line_starts[first_line]
            end = data.content_ends[last_line]
            if re.search(r"\w", data.projection[start:end]):
                blocks.append(Block(kind, start, end, first_line, last_line, block_uncertain))
        kind = ""
        first_line = -1
        last_line = -1
        marker_indent = -1
        block_uncertain = False

    for index, raw_line in enumerate(data.lines):
        line = raw_line.rstrip("\r\n")
        if data.structural[index] or not line.strip():
            flush()
            continue

        list_match = _LIST_MARKER.match(line)
        if list_match:
            flush()
            kind = "list"
            first_line = index
            last_line = index
            marker_indent = len(list_match.group(1))
            block_uncertain = data.uncertain_lines[index]
            continue

        quote_match = _BLOCKQUOTE.match(line)
        if quote_match:
            if kind != "quote":
                flush()
                kind = "quote"
                first_line = index
            last_line = index
            block_uncertain = block_uncertain or data.uncertain_lines[index]
            continue

        indentation = len(line) - len(line.lstrip(" "))
        if kind == "list" and indentation > marker_indent:
            last_line = index
            block_uncertain = block_uncertain or data.uncertain_lines[index]
            continue

        if kind != "prose":
            flush()
            kind = "prose"
            first_line = index
        last_line = index
        block_uncertain = block_uncertain or data.uncertain_lines[index]

    flush()
    return blocks


def _first_non_whitespace(text: str, start: int, end: int) -> int | None:
    for index in range(start, end):
        if not text[index].isspace():
            return index
    return None


def _last_non_whitespace(text: str, start: int, end: int) -> int | None:
    for index in range(end - 1, start - 1, -1):
        if not text[index].isspace():
            return index
    return None


class _ActiveRun:
    def __init__(
        self,
        *,
        start: int,
        end: int,
        first_line: int,
        indentation: int,
        marker_family: str,
    ) -> None:
        self.start = start
        self.end = end
        self.first_line = first_line
        self.last_line = first_line
        self.indentation = indentation
        self.marker_family = marker_family
        self.peer_count = 1

    def freeze(self) -> ListRun:
        return ListRun(
            self.start,
            self.end,
            self.first_line,
            self.last_line,
            self.indentation,
            self.marker_family,
            self.peer_count,
        )


def _extract_list_runs(data: ProjectionData) -> list[ListRun]:
    active: dict[tuple[int, str], _ActiveRun] = {}
    completed: list[ListRun] = []

    def finish(key: tuple[int, str]) -> None:
        run = active.pop(key)
        if run.peer_count >= 2:
            completed.append(run.freeze())

    for index, raw_line in enumerate(data.lines):
        line = raw_line.rstrip("\r\n")
        if data.structural[index] or _BLOCKQUOTE.match(line):
            for key in tuple(active):
                finish(key)
            continue
        if not line.strip():
            continue

        marker = _LIST_MARKER.match(line)
        if marker:
            indentation = len(marker.group(1))
            family = "ordered" if marker.group("marker")[0].isdigit() else "bullet"
            for key in tuple(active):
                if key[0] > indentation or (key[0] == indentation and key[1] != family):
                    finish(key)
            for key, run in active.items():
                if key[0] < indentation:
                    run.end = data.content_ends[index]
                    run.last_line = index
            key = (indentation, family)
            if key in active:
                run = active[key]
                run.peer_count += 1
                run.end = data.content_ends[index]
                run.last_line = index
            else:
                active[key] = _ActiveRun(
                    start=data.line_starts[index],
                    end=data.content_ends[index],
                    first_line=index,
                    indentation=indentation,
                    marker_family=family,
                )
            continue

        indentation = len(line) - len(line.lstrip(" "))
        for key in tuple(active):
            if indentation <= key[0]:
                finish(key)
        for run in active.values():
            run.end = data.content_ends[index]
            run.last_line = index

    for key in tuple(active):
        finish(key)
    return completed


def offset_to_position(text: str, offset: int) -> tuple[int, int]:
    if offset < 0 or offset > len(text):
        raise ValueError(f"offset out of range: {offset}")
    starts = [0]
    starts.extend(index + 1 for index, character in enumerate(text) if character == "\n")
    line_index = bisect_right(starts, offset) - 1
    return line_index + 1, offset - starts[line_index] + 1


def _digest_text_slice(text: str, start: int, end: int) -> str:
    return hashlib.sha256(text[start:end].encode()).hexdigest()


def _nul_digest(prefix: str, values: tuple[str, ...]) -> str:
    payload = "\0".join(values).encode()
    return prefix + hashlib.sha256(payload).hexdigest()


def _case_id(document: Document, rule_id: str, start: int, end: int, unit_kind: str) -> str:
    return _nul_digest(
        "r2-",
        (
            ROUND_ID,
            rule_id,
            document.source_id,
            document.path,
            str(start),
            str(end),
            unit_kind,
        ),
    )


def _ambiguity_group(document: Document, block: Block) -> str:
    return _nul_digest(
        "ag-",
        (
            ROUND_ID,
            "ambiguity",
            document.source_id,
            document.path,
            str(block.start),
            str(block.end),
        ),
    )


def _has_uncertain(data: ProjectionData, start: int, end: int) -> bool:
    return any(data.uncertain_positions[start:end])


def _common_record(
    text: str,
    document: Document,
    *,
    rule_id: str,
    start: int,
    end: int,
    unit_kind: str,
    structural_context: str,
    has_uncertain_markup: bool,
) -> Record:
    start_line, start_column = offset_to_position(text, start)
    end_line, end_column = offset_to_position(text, end)
    return {
        "schema_version": SCHEMA_VERSION,
        "round_id": ROUND_ID,
        "case_id": _case_id(document, rule_id, start, end, unit_kind),
        "rule_id": rule_id,
        "source_id": document.source_id,
        "commit": SOURCES[document.source_id].commit,
        "path": document.path,
        "text_type": document.text_type,
        "start_offset": start,
        "end_offset": end,
        "start_line": start_line,
        "start_column": start_column,
        "end_line": end_line,
        "end_column": end_column,
        "unit_kind": unit_kind,
        "structural_context": structural_context,
        "has_uncertain_markup": has_uncertain_markup,
        "slice_sha256": _digest_text_slice(text, start, end),
        "truth": "pending-review",
        "review_status": "pending-review",
    }


def _alpha_runs(text: str) -> int:
    count = 0
    in_run = False
    for character in text:
        if character.isalpha():
            if not in_run:
                count += 1
                in_run = True
        else:
            in_run = False
    return count


def _sentence_records(
    text: str, data: ProjectionData, document: Document, blocks: list[Block]
) -> list[Record]:
    if document.text_type == "procedural":
        if document.path in SENT001_EXCLUDED_PATHS:
            return []
        rule_id = "STE-I9-SENT-001"
    else:
        rule_id = "STE-I9-SENT-002"

    records: list[Record] = []
    closing = "\"'’”)]"
    strip_characters = " \t\r\n\"'’”)]"
    for block in blocks:
        projection = data.projection[block.start : block.end]
        cursor = 0
        context = "uncertain" if block.uncertain else "visible_prose"
        for match in _TERMINAL.finditer(projection):
            first = _first_non_whitespace(projection, cursor, match.end())
            if first is None:
                cursor = match.end()
                continue
            relative_end = match.end()
            while relative_end < len(projection) and projection[relative_end] in closing:
                relative_end += 1
            start = block.start + first
            end = block.start + relative_end
            record = _common_record(
                text,
                document,
                rule_id=rule_id,
                start=start,
                end=end,
                unit_kind="sentence_complete",
                structural_context=context,
                has_uncertain_markup=block.uncertain,
            )
            record.update(
                {
                    "sentence_status": "complete",
                    "terminal": match.group(0),
                    "raw_alpha_token_count": _alpha_runs(data.projection[start:end]),
                    "ambiguity_group": _ambiguity_group(document, block),
                    "block_start_offset": block.start,
                    "block_end_offset": block.end,
                }
            )
            records.append(record)
            cursor = relative_end

        tail = projection[cursor:]
        stripped = tail.strip(strip_characters)
        if re.search(r"\w", stripped):
            left = len(tail) - len(tail.lstrip(strip_characters))
            right = len(tail.rstrip(strip_characters))
            start = block.start + cursor + left
            end = block.start + cursor + right
            record = _common_record(
                text,
                document,
                rule_id=rule_id,
                start=start,
                end=end,
                unit_kind="sentence_incomplete",
                structural_context=context,
                has_uncertain_markup=block.uncertain,
            )
            record.update(
                {
                    "sentence_status": "incomplete",
                    "terminal": "",
                    "raw_alpha_token_count": _alpha_runs(data.projection[start:end]),
                    "ambiguity_group": _ambiguity_group(document, block),
                    "block_start_offset": block.start,
                    "block_end_offset": block.end,
                }
            )
            records.append(record)
    return records


def _paragraph_records(
    text: str, data: ProjectionData, document: Document, blocks: list[Block]
) -> list[Record]:
    if document.text_type != "descriptive":
        return []
    records: list[Record] = []
    for block in blocks:
        if block.kind != "prose":
            continue
        start = _first_non_whitespace(data.projection, block.start, block.end)
        last = _last_non_whitespace(data.projection, block.start, block.end)
        if start is None or last is None:
            continue
        context = "uncertain" if block.uncertain else "visible_prose"
        record = _common_record(
            text,
            document,
            rule_id="STE-I9-PARA-001",
            start=start,
            end=last + 1,
            unit_kind="paragraph",
            structural_context=context,
            has_uncertain_markup=block.uncertain,
        )
        record.update(
            {
                "candidate_terminal_count": len(
                    list(_TERMINAL.finditer(data.projection[block.start : block.end]))
                ),
                "block_start_offset": block.start,
                "block_end_offset": block.end,
            }
        )
        records.append(record)
    return records


def _punctuation_records(text: str, data: ProjectionData, document: Document) -> list[Record]:
    records: list[Record] = []
    for start, character in enumerate(text):
        if character != ";":
            continue
        uncertain = data.uncertain_positions[start]
        line = bisect_right(data.line_starts, start) - 1
        if uncertain:
            context = "uncertain"
        elif data.structural[line] or data.projection[start] != ";":
            context = "markup_or_code"
        else:
            context = "visible_prose"
        record = _common_record(
            text,
            document,
            rule_id="STE-I9-PUNCT-001",
            start=start,
            end=start + 1,
            unit_kind="semicolon",
            structural_context=context,
            has_uncertain_markup=uncertain,
        )
        record["punctuation"] = ";"
        records.append(record)
    return records


_BLOCKER_ORDER = (
    "heading",
    "fence",
    "thematic_break",
    "blockquote",
    "more_than_one_blank_line",
)


def _list_record(
    text: str,
    data: ProjectionData,
    document: Document,
    run: ListRun,
    blocks: list[Block],
) -> Record:
    candidates = [block for block in blocks if block.end <= run.start]
    lead = max(candidates, key=lambda block: (block.end, block.start)) if candidates else None
    blockers_found: set[str] = set()

    if lead is None:
        lead_status = "not_found"
        lead_start = -1
        lead_end = -1
        lead_digest = ""
        blank_lines = -1
        list_terminal = "absent"
    else:
        first_between = lead.last_line + 1
        between = range(first_between, run.first_line)
        blank_lines = sum(not data.lines[index].strip() for index in between)
        if blank_lines > 1:
            blockers_found.add("more_than_one_blank_line")
        for index in between:
            kind = data.line_kinds[index]
            if kind in {"heading", "fence", "thematic_break"}:
                blockers_found.add(kind)
            if _BLOCKQUOTE.match(data.lines[index].rstrip("\r\n")):
                blockers_found.add("blockquote")

        first = _first_non_whitespace(data.projection, lead.start, lead.end)
        last = _last_non_whitespace(data.projection, lead.start, lead.end)
        if first is None or last is None:
            raise AuditError(f"{document.path}: visible lead-in has no projected content")
        lead_start = first
        lead_end = last + 1
        lead_digest = _digest_text_slice(text, lead_start, lead_end)
        interval_uncertain = lead.uncertain or any(data.uncertain_lines[index] for index in between)
        lead_status = "uncertain" if interval_uncertain else "found"
        terminal = data.projection[last]
        if terminal == ".":
            list_terminal = "period"
        elif terminal == ":":
            list_terminal = "colon"
        elif terminal:
            list_terminal = "other"
        else:
            list_terminal = "absent"

    uncertain = _has_uncertain(data, run.start, run.end)
    record = _common_record(
        text,
        document,
        rule_id="STE-I9-LIST-001",
        start=run.start,
        end=run.end,
        unit_kind="list_run",
        structural_context="uncertain" if uncertain else "visible_prose",
        has_uncertain_markup=uncertain,
    )
    record.update(
        {
            "marker_family": run.marker_family,
            "indentation": run.indentation,
            "peer_count": run.peer_count,
            "blank_lines_before": blank_lines,
            "lead_in_status": lead_status,
            "lead_in_start_offset": lead_start,
            "lead_in_end_offset": lead_end,
            "lead_in_slice_sha256": lead_digest,
            "list_terminal": list_terminal,
            "blockers": [blocker for blocker in _BLOCKER_ORDER if blocker in blockers_found],
        }
    )
    return record


def extract_document_records(text: str, document: Document) -> list[Record]:
    data = build_projection(text)
    blocks = _extract_blocks(data)
    records = _sentence_records(text, data, document, blocks)
    records.extend(_paragraph_records(text, data, document, blocks))
    records.extend(_punctuation_records(text, data, document))
    records.extend(
        _list_record(text, data, document, run, blocks) for run in _extract_list_runs(data)
    )
    return sort_inventory_records(records)


_SOURCE_ORDER = {"dapr": 0, "otel": 1}
_RULE_ORDER = {
    "STE-I9-SENT-001": 0,
    "STE-I9-SENT-002": 1,
    "STE-I9-PARA-001": 2,
    "STE-I9-PUNCT-001": 3,
    "STE-I9-LIST-001": 4,
}
_UNIT_ORDER = {
    "sentence_complete": 0,
    "sentence_incomplete": 1,
    "paragraph": 2,
    "semicolon": 3,
    "list_run": 4,
}


def _record_string(record: Record, key: str) -> str:
    value = record[key]
    if not isinstance(value, str):
        raise AuditError(f"record field {key} is not a string")
    return value


def _record_integer(record: Record, key: str) -> int:
    value = record[key]
    if not isinstance(value, int) or isinstance(value, bool):
        raise AuditError(f"record field {key} is not an integer")
    return value


def _record_sort_key(record: Record) -> tuple[int, str, int, int, int, int, str]:
    source_id = _record_string(record, "source_id")
    rule_id = _record_string(record, "rule_id")
    unit_kind = _record_string(record, "unit_kind")
    return (
        _SOURCE_ORDER[source_id],
        _record_string(record, "path"),
        _record_integer(record, "start_offset"),
        _record_integer(record, "end_offset"),
        _RULE_ORDER[rule_id],
        _UNIT_ORDER[unit_kind],
        _record_string(record, "case_id"),
    )


def sort_inventory_records(records: list[Record]) -> list[Record]:
    return sorted(records, key=_record_sort_key)


def canonical_inventory_bytes(records: list[Record]) -> bytes:
    ordered = sort_inventory_records(records)
    lines = [
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for record in ordered
    ]
    return ("\n".join(lines) + "\n").encode()


_COMMON_FIELDS = {
    "schema_version",
    "round_id",
    "case_id",
    "rule_id",
    "source_id",
    "commit",
    "path",
    "text_type",
    "start_offset",
    "end_offset",
    "start_line",
    "start_column",
    "end_line",
    "end_column",
    "unit_kind",
    "structural_context",
    "has_uncertain_markup",
    "slice_sha256",
    "truth",
    "review_status",
}
_SPECIFIC_FIELDS = {
    "STE-I9-SENT-001": {
        "sentence_status",
        "terminal",
        "raw_alpha_token_count",
        "ambiguity_group",
        "block_start_offset",
        "block_end_offset",
    },
    "STE-I9-SENT-002": {
        "sentence_status",
        "terminal",
        "raw_alpha_token_count",
        "ambiguity_group",
        "block_start_offset",
        "block_end_offset",
    },
    "STE-I9-PARA-001": {
        "candidate_terminal_count",
        "block_start_offset",
        "block_end_offset",
    },
    "STE-I9-PUNCT-001": {"punctuation"},
    "STE-I9-LIST-001": {
        "marker_family",
        "indentation",
        "peer_count",
        "blank_lines_before",
        "lead_in_status",
        "lead_in_start_offset",
        "lead_in_end_offset",
        "lead_in_slice_sha256",
        "list_terminal",
        "blockers",
    },
}


def _document_index() -> dict[tuple[str, str], Document]:
    return {(document.source_id, document.path): document for document in DOCUMENTS}


def _validate_record_schema(record: Record) -> None:
    rule_id = _record_string(record, "rule_id")
    expected = _COMMON_FIELDS | _SPECIFIC_FIELDS[rule_id]
    if set(record) != expected:
        missing = sorted(expected - set(record))
        extra = sorted(set(record) - expected)
        raise AuditError(f"{rule_id}: schema mismatch: missing={missing}, extra={extra}")
    if record["schema_version"] != SCHEMA_VERSION or record["round_id"] != ROUND_ID:
        raise AuditError(f"{rule_id}: schema literals mismatch")
    if record["truth"] != "pending-review" or record["review_status"] != "pending-review":
        raise AuditError(f"{rule_id}: pre-label state mismatch")
    if record["structural_context"] not in {"visible_prose", "markup_or_code", "uncertain"}:
        raise AuditError(f"{rule_id}: structural context mismatch")


def validate_inventory(records: list[Record], texts: dict[tuple[str, str], str]) -> dict[str, int]:
    documents = _document_index()
    seen_keys: set[tuple[str, str, str, int, int, str]] = set()
    seen_ids: set[str] = set()
    counts = {rule_id: 0 for rule_id in EXPECTED_INVENTORY_COUNTS}

    if records != sort_inventory_records(records):
        raise AuditError("inventory ordering mismatch")

    for record in records:
        _validate_record_schema(record)
        rule_id = _record_string(record, "rule_id")
        source_id = _record_string(record, "source_id")
        path = _record_string(record, "path")
        unit_kind = _record_string(record, "unit_kind")
        start = _record_integer(record, "start_offset")
        end = _record_integer(record, "end_offset")
        document = documents[(source_id, path)]
        text = texts[(source_id, path)]
        if not 0 <= start < end <= len(text):
            raise AuditError(f"{path}: invalid inventory span {start}:{end}")
        if _digest_text_slice(text, start, end) != record["slice_sha256"]:
            raise AuditError(f"{path}: slice round-trip mismatch")
        if offset_to_position(text, start) != (
            _record_integer(record, "start_line"),
            _record_integer(record, "start_column"),
        ):
            raise AuditError(f"{path}: start coordinate mismatch")
        if offset_to_position(text, end) != (
            _record_integer(record, "end_line"),
            _record_integer(record, "end_column"),
        ):
            raise AuditError(f"{path}: end coordinate mismatch")
        expected_id = _case_id(document, rule_id, start, end, unit_kind)
        if record["case_id"] != expected_id:
            raise AuditError(f"{path}: case ID mismatch")

        key = (rule_id, source_id, path, start, end, unit_kind)
        case_id = _record_string(record, "case_id")
        if key in seen_keys or case_id in seen_ids:
            raise AuditError(f"{path}: duplicate inventory unit")
        seen_keys.add(key)
        seen_ids.add(case_id)

        if rule_id == "STE-I9-LIST-001":
            lead_status = _record_string(record, "lead_in_status")
            lead_start = _record_integer(record, "lead_in_start_offset")
            lead_end = _record_integer(record, "lead_in_end_offset")
            lead_digest = _record_string(record, "lead_in_slice_sha256")
            if lead_status == "not_found":
                if (lead_start, lead_end, lead_digest) != (-1, -1, ""):
                    raise AuditError(f"{path}: invalid absent lead-in sentinel")
            else:
                if not 0 <= lead_start < lead_end <= len(text):
                    raise AuditError(f"{path}: invalid lead-in span")
                if _digest_text_slice(text, lead_start, lead_end) != lead_digest:
                    raise AuditError(f"{path}: lead-in round-trip mismatch")

        if rule_id == "STE-I9-SENT-001" and path in SENT001_EXCLUDED_PATHS:
            raise AuditError(f"{path}: excluded SENT-001 document emitted a unit")
        counts[rule_id] += 1

    if counts != EXPECTED_INVENTORY_COUNTS:
        raise AuditError(
            f"inventory-count mismatch: expected {EXPECTED_INVENTORY_COUNTS}, got {counts}"
        )
    if len(records) != 1_173:
        raise AuditError(f"inventory total mismatch: expected 1173, got {len(records)}")
    return counts


def build_inventory(roots: dict[str, Path]) -> tuple[list[Record], bytes, dict[str, int]]:
    records: list[Record] = []
    texts: dict[tuple[str, str], str] = {}
    for document in DOCUMENTS:
        text = (roots[document.source_id] / document.path).read_text(encoding="utf-8")
        texts[(document.source_id, document.path)] = text
        records.extend(extract_document_records(text, document))
    records = sort_inventory_records(records)
    counts = validate_inventory(records, texts)
    return records, canonical_inventory_bytes(records), counts


def _write_atomic(path: Path, payload: bytes) -> None:
    temporary_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            temporary_name = handle.name
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except OSError:
        if temporary_name:
            with suppress(OSError):
                Path(temporary_name).unlink(missing_ok=True)
        raise


def _visible_blocks(lines: list[str], structural: list[bool]) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    current: list[str] = []
    kind = ""

    def flush() -> None:
        nonlocal current, kind
        if current:
            cleaned = _clean_inline(" ".join(current)).strip()
            if re.search(r"\w", cleaned):
                blocks.append((cleaned, kind))
        current = []
        kind = ""

    for index, raw_line in enumerate(lines):
        line = raw_line.rstrip("\r\n")
        if structural[index] or not line.strip():
            flush()
            continue

        list_match = _LIST_MARKER.match(line)
        if list_match:
            flush()
            kind = "list"
            current.append(list_match.group("body"))
            continue

        quote_match = _BLOCKQUOTE.match(line)
        if quote_match:
            if kind != "quote":
                flush()
                kind = "quote"
            current.append(quote_match.group(1))
            continue

        indentation = len(line) - len(line.lstrip(" "))
        if kind == "list" and indentation > 0:
            current.append(line.strip())
            continue

        if kind != "prose":
            flush()
            kind = "prose"
        current.append(line.strip())

    flush()
    return blocks


def _count_list_runs(lines: list[str], structural: list[bool]) -> int:
    active: dict[tuple[int, str], int] = {}
    runs = 0

    for index, raw_line in enumerate(lines):
        line = raw_line.rstrip("\r\n")
        if structural[index] or _BLOCKQUOTE.match(line):
            active.clear()
            continue
        if not line.strip():
            continue

        marker = _LIST_MARKER.match(line)
        if marker:
            indent = len(marker.group(1))
            family = "ordered" if marker.group("marker")[0].isdigit() else "bullet"
            for key in tuple(active):
                if key[0] > indent or (key[0] == indent and key[1] != family):
                    del active[key]
            key = (indent, family)
            active[key] = active.get(key, 0) + 1
            if active[key] == 2:
                runs += 1
            continue

        indentation = len(line) - len(line.lstrip(" "))
        for key in tuple(active):
            if indentation <= key[0]:
                del active[key]

    return runs


def scan_text(text: str, *, text_type: str) -> ScanCounts:
    if text_type not in {"procedural", "descriptive"}:
        raise ValueError(f"unsupported text type: {text_type}")

    lines = text.splitlines(keepends=True)
    structural = _structural_mask(lines)
    blocks = _visible_blocks(lines, structural)
    complete = 0
    incomplete = 0
    paragraphs = 0

    for block, kind in blocks:
        terminals = list(_TERMINAL.finditer(block))
        complete += len(terminals)
        tail_start = terminals[-1].end() if terminals else 0
        tail = block[tail_start:].strip(" \t\r\n\"'’”)]")
        if re.search(r"\w", tail):
            incomplete += 1
        if text_type == "descriptive" and kind == "prose":
            paragraphs += 1

    return ScanCounts(
        sentence_complete=complete,
        sentence_incomplete=incomplete,
        paragraphs=paragraphs,
        punctuation=text.count(";"),
        list_runs=_count_list_runs(lines, structural),
    )


def audit_snapshots(roots: dict[str, Path]) -> tuple[list[tuple[str, str, str]], int]:
    audit_rows: list[tuple[str, str, str]] = []
    for source_id, source in SOURCES.items():
        root = roots[source_id]
        if _git(root, "rev-parse", "HEAD") != source.commit:
            raise AuditError(f"{source_id}: commit mismatch")
        license_digest = verify_digest(
            (root / "LICENSE").read_bytes(), source.license_sha256, "LICENSE"
        )
        audit_rows.append(("SOURCE", source_id, f"commit={source.commit} license={license_digest}"))

    for frame in FRAMES:
        actual_tree = _git(roots[frame.source_id], "rev-parse", f"HEAD:{frame.path}")
        if actual_tree != frame.tree:
            detail = f"expected {frame.tree}, got {actual_tree}"
            raise AuditError(f"{frame.source_id}:{frame.path}: tree mismatch: {detail}")
        audit_rows.append(("TREE", frame.source_id, f"{frame.path} {actual_tree}"))

    words = 0
    manifest_lines: list[str] = []
    for document in DOCUMENTS:
        source = SOURCES[document.source_id]
        if not document.path.startswith(source.path_prefix):
            raise AuditError(f"{document.source_id}:{document.path}: invalid path prefix")
        actual_key = selection_key(SEED, document.path)
        if actual_key != document.key:
            raise AuditError(f"{document.source_id}:{document.path}: selection key mismatch")
        data = (roots[document.source_id] / document.path).read_bytes()
        actual_digest = verify_digest(data, document.sha256, document.path)
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as error:
            raise AuditError(f"{document.source_id}:{document.path}: not UTF-8") from error
        file_words = len(text.split())
        words += file_words
        manifest_lines.append(
            f"{document.source_id}\t{document.path}\t{actual_key}\t{actual_digest}\n"
        )
        audit_rows.append(
            (
                "FILE",
                document.source_id,
                f"{document.path} key={actual_key} sha256={actual_digest} words={file_words}",
            )
        )

    if words != EXPECTED_WORDS:
        raise AuditError(f"word-count mismatch: expected {EXPECTED_WORDS}, got {words}")
    manifest = "".join(manifest_lines).encode("utf-8")
    manifest_digest = verify_digest(manifest, EXPECTED_MANIFEST_SHA256, "manifest")
    audit_rows.append(("TOTAL", "all", f"words={words} manifest_sha256={manifest_digest}"))
    return audit_rows, words


def aggregate_rule_counts(rows: list[tuple[Document, ScanCounts]]) -> dict[str, int]:
    return {
        "STE-I9-SENT-001": sum(
            counts.sentence_units
            for document, counts in rows
            if document.text_type == "procedural" and document.path not in SENT001_EXCLUDED_PATHS
        ),
        "STE-I9-SENT-002": sum(
            counts.sentence_units
            for document, counts in rows
            if document.text_type == "descriptive"
        ),
        "STE-I9-PARA-001": sum(
            counts.paragraphs for document, counts in rows if document.text_type == "descriptive"
        ),
        "STE-I9-PUNCT-001": sum(counts.punctuation for _, counts in rows),
        "STE-I9-LIST-001": sum(counts.list_runs for _, counts in rows),
    }


def count_documents(
    roots: dict[str, Path],
) -> tuple[list[tuple[Document, ScanCounts]], dict[str, int]]:
    rows: list[tuple[Document, ScanCounts]] = []
    for document in DOCUMENTS:
        text = (roots[document.source_id] / document.path).read_text(encoding="utf-8")
        counts = scan_text(text, text_type=document.text_type)
        rows.append((document, counts))
    return rows, aggregate_rule_counts(rows)


def render_report(
    audit_rows: list[tuple[str, str, str]],
    count_rows: list[tuple[Document, ScanCounts]],
    rule_counts: dict[str, int],
) -> str:
    lines = ["AUDIT"]
    lines.extend("\t".join(row) for row in audit_rows)
    lines.append("COUNT_BY_FILE")
    lines.append(
        "source_id\ttext_type\tpath\tcomplete\tincomplete\tparagraphs\tsemicolons\tlist_runs"
    )
    for document, counts in count_rows:
        lines.append(
            "\t".join(
                (
                    document.source_id,
                    document.text_type,
                    document.path,
                    str(counts.sentence_complete),
                    str(counts.sentence_incomplete),
                    str(counts.paragraphs),
                    str(counts.punctuation),
                    str(counts.list_runs),
                )
            )
        )
    lines.append("TRANCHE_EXCLUSIONS")
    lines.append("rule_id\tpath\treason")
    for path in sorted(SENT001_EXCLUDED_PATHS):
        lines.append(f"STE-I9-SENT-001\t{path}\thighest-selection-key-after-cap")
    lines.append("COUNT_BY_RULE")
    lines.append("rule_id\tunits\tcap\tstatus")
    for rule_id, cap in CAPS.items():
        count = rule_counts[rule_id]
        status = "OK" if count <= cap else "EXCEEDED"
        lines.append(f"{rule_id}\t{count}\t{cap}\t{status}")
    return "\n".join(lines) + "\n"


def parse_args(arguments: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--count-only", action="store_true")
    mode.add_argument("--emit-inventory", action="store_true")
    parser.add_argument("--dapr-root", type=Path, default=Path(SOURCES["dapr"].default_root))
    parser.add_argument("--otel-root", type=Path, default=Path(SOURCES["otel"].default_root))
    parser.add_argument("--expected-output-sha256")
    return parser.parse_args(arguments)


def main(arguments: list[str] | None = None) -> int:
    options = parse_args(arguments)
    roots = {"dapr": options.dapr_root.resolve(), "otel": options.otel_root.resolve()}
    try:
        audit_rows, _ = audit_snapshots(roots)
        if options.count_only:
            if options.expected_output_sha256:
                raise AuditError("--expected-output-sha256 requires --emit-inventory")
            count_rows, rule_counts = count_documents(roots)
            print(render_report(audit_rows, count_rows, rule_counts), end="")
            return 0

        _, payload_a, counts_a = build_inventory(roots)
        _, payload_b, counts_b = build_inventory(roots)
        if payload_a != payload_b or counts_a != counts_b:
            raise AuditError("duplicate inventory generation is not deterministic")
        digest = hashlib.sha256(payload_a).hexdigest()
        if options.expected_output_sha256 and digest != options.expected_output_sha256:
            raise AuditError(
                "inventory output digest mismatch: "
                f"expected {options.expected_output_sha256}, got {digest}"
            )
        _write_atomic(INVENTORY_A, payload_a)
        _write_atomic(INVENTORY_B, payload_b)
    except (AuditError, OSError) as error:
        print(f"ABORT\t{error}", file=sys.stderr)
        return 2
    print("INVENTORY\tpending-review")
    for rule_id in EXPECTED_INVENTORY_COUNTS:
        print(f"COUNT\t{rule_id}\t{counts_a[rule_id]}")
    print(f"TOTAL\t{sum(counts_a.values())}")
    print(f"SHA256\t{digest}")
    print(f"PATH\t{INVENTORY_A}")
    print(f"PATH\t{INVENTORY_B}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
