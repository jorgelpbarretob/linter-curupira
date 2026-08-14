"""Adapters lossless de TXT e Markdown reutilizados pelo Hermes."""

from hermes_lint.parsing.core import (
    MAX_DOCUMENT_CHARS,
    DocumentTooLargeError,
    UnsupportedFormatError,
    parse_document,
    parse_text,
)
from hermes_lint.parsing.markdown import parse_markdown

__all__ = [
    "MAX_DOCUMENT_CHARS",
    "DocumentTooLargeError",
    "UnsupportedFormatError",
    "parse_document",
    "parse_markdown",
    "parse_text",
]
