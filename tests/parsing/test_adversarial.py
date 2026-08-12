import random

import pytest

from ste_lint.parsing import MAX_DOCUMENT_CHARS, DocumentTooLargeError, parse_markdown


def test_bounded_adversarial_markdown_does_not_crash_or_lose_text() -> None:
    randomizer = random.Random(20260812)
    alphabet = "abc XYZ\r\n`*_#[]()<>|;:.!?β"

    for _ in range(1_000):
        text = "".join(randomizer.choice(alphabet) for _ in range(randomizer.randrange(257)))
        document = parse_markdown("adversarial.md", text)
        assert "".join(token.text for token in document.tokens) == text


def test_document_size_limit_fails_before_parsing() -> None:
    with pytest.raises(DocumentTooLargeError, match="maximum"):
        parse_markdown("too-large.md", "x" * (MAX_DOCUMENT_CHARS + 1))
