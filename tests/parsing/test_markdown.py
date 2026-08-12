import pytest

from ste_lint.domain import Document, RegionKind
from ste_lint.parsing import parse_markdown


def kind_at(document_text: str, document: Document, needle: str, offset: int = 0) -> RegionKind:
    index = document_text.index(needle) + offset
    return document.kind_at(index)


def test_markdown_parser_is_lossless_and_classifies_markup() -> None:
    text = (
        "---\r\n"
        "title: Synthetic\r\n"
        "---\r\n"
        "# Ignored heading\r\n"
        "Inspect the `mode=safe;retry=2` value and open the "
        "[service page](https://example.invalid/check;a=1).\r\n"
        "The <span>visible text</span> remains lintable.\r\n"
        "```text\r\n"
        "ignored; code\r\n"
        "```\r\n"
        "| Name | Value |\r\n"
        "| --- | --- |\r\n"
        "| pump | ready |\r\n"
        "- Inspect the pump.\r\n"
    )

    document = parse_markdown("manual.md", text)

    assert document.text == text
    assert "".join(token.text for token in document.tokens) == text
    assert kind_at(text, document, "title: Synthetic") is RegionKind.IGNORED
    assert kind_at(text, document, "Ignored heading") is RegionKind.IGNORED
    assert kind_at(text, document, "mode=safe") is RegionKind.IGNORED
    assert kind_at(text, document, "service page") is RegionKind.LINTABLE
    assert kind_at(text, document, "https://") is RegionKind.IGNORED
    assert kind_at(text, document, "<span>") is RegionKind.IGNORED
    assert kind_at(text, document, "visible text") is RegionKind.LINTABLE
    assert kind_at(text, document, "ignored; code") is RegionKind.IGNORED
    assert kind_at(text, document, "pump | ready") is RegionKind.IGNORED
    assert kind_at(text, document, "- Inspect", 0) is RegionKind.IGNORED
    assert kind_at(text, document, "Inspect the pump") is RegionKind.LINTABLE


def test_inline_code_and_link_destination_do_not_enter_lintable_text() -> None:
    text = "Use `alpha;beta` and read [the guide](private/path;v=2)."
    document = parse_markdown("manual.md", text)

    lintable = document.lintable_text
    assert "alpha;beta" not in lintable
    assert "private/path" not in lintable
    assert "the guide" in lintable


def test_unclosed_fence_is_ignored_to_end_of_document() -> None:
    text = "Before.\n```text\nsynthetic; code\nstill code"
    document = parse_markdown("manual.md", text)

    assert kind_at(text, document, "Before") is RegionKind.LINTABLE
    assert kind_at(text, document, "synthetic") is RegionKind.IGNORED
    assert kind_at(text, document, "still code") is RegionKind.IGNORED


def test_markdown_sentences_use_only_lintable_parts() -> None:
    text = "Open the `private` valve. The [public label](private-target) is visible."
    document = parse_markdown("manual.md", text)

    assert [sentence.text(document) for sentence in document.sentences] == [
        "Open the  valve.",
        "The public label is visible.",
    ]


def test_inline_markup_inside_list_and_quote_keeps_only_visible_prose() -> None:
    text = "- Open the `private` valve.\n> Read [the public label](private-target).\n"
    document = parse_markdown("manual.md", text)

    assert kind_at(text, document, "-") is RegionKind.IGNORED
    assert kind_at(text, document, "private") is RegionKind.IGNORED
    assert kind_at(text, document, ">") is RegionKind.IGNORED
    assert kind_at(text, document, "public label") is RegionKind.LINTABLE
    assert kind_at(text, document, "private-target") is RegionKind.IGNORED


@pytest.mark.parametrize(
    ("text", "ignored", "lintable"),
    [
        ("# Heading\n", "Heading", None),
        ("    code only\n", "code only", None),
        ("[ref]: https://example.invalid\n", "https://", None),
        ("Use <https://example.invalid>.\n", "https://", "Use"),
        ("See ![private alt](private.png).\n", "private alt", "See"),
        ("The <em>visible</em> text.\n", "<em>", "visible"),
    ],
)
def test_supported_markdown_constructs_are_classified_conservatively(
    text: str, ignored: str, lintable: str | None
) -> None:
    document = parse_markdown("manual.md", text)

    assert kind_at(text, document, ignored) is RegionKind.IGNORED
    if lintable is not None:
        assert kind_at(text, document, lintable) is RegionKind.LINTABLE


@pytest.mark.parametrize(
    "text",
    [
        "A bracket [ remains prose.\n",
        "A link [label](without a close remains prose.\n",
        "A less-than sign 2 < 3 remains prose.\n",
    ],
)
def test_incomplete_or_plain_punctuation_is_not_treated_as_markup(text: str) -> None:
    document = parse_markdown("manual.md", text)

    assert document.lintable_text == text
