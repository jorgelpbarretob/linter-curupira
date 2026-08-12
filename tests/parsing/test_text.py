import pytest

from ste_lint.domain import RegionKind
from ste_lint.parsing import UnsupportedFormatError, parse_document, parse_text


@pytest.mark.parametrize(
    "text",
    [
        "",
        "One sentence.\nSecond sentence.\n",
        "One sentence.\r\nSecond sentence.\r\n",
        "Café β uses Unicode.\n",
    ],
)
def test_text_parser_is_lossless(text: str) -> None:
    document = parse_text("manual.txt", text)

    assert document.text == text
    assert "".join(token.text for token in document.tokens) == text
    region_text = "".join(
        document.text[region.span.start_offset : region.span.end_offset]
        for region in document.regions
    )
    assert region_text == text
    assert all(region.kind is RegionKind.LINTABLE for region in document.regions)


def test_text_parser_produces_minimal_sentence_spans() -> None:
    document = parse_text("manual.txt", "Open the valve.\r\nThe café is ready?")

    assert [sentence.text(document) for sentence in document.sentences] == [
        "Open the valve.",
        "The café is ready?",
    ]
    assert all(sentence.is_complete for sentence in document.sentences)


@pytest.mark.parametrize("name", ["manual.pdf", "manual.docx", "manual.html"])
def test_unsupported_document_formats_fail_explicitly(name: str) -> None:
    with pytest.raises(UnsupportedFormatError, match="not supported"):
        parse_document(name, "Synthetic text.")


@pytest.mark.parametrize("name", ["manual.txt", "manual.md", "manual.markdown"])
def test_supported_extension_dispatch(name: str) -> None:
    document = parse_document(name, "Synthetic text.")

    assert document.uri == name
