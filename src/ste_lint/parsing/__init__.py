"""Lossless source adapters for the formats supported by the MVP."""

from ste_lint.parsing.core import (
    MAX_DOCUMENT_CHARS,
    DocumentTooLargeError,
    UnsupportedFormatError,
    parse_document,
    parse_text,
)
from ste_lint.parsing.markdown import parse_markdown

__all__ = [
    "MAX_DOCUMENT_CHARS",
    "DocumentTooLargeError",
    "UnsupportedFormatError",
    "parse_document",
    "parse_markdown",
    "parse_text",
]
