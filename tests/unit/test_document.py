import pytest

from ste_lint.domain import Document, RegionKind, TextRegion, TextSpan, Token


def test_document_rejects_regions_that_do_not_partition_text() -> None:
    with pytest.raises(ValueError, match="partition"):
        Document(
            uri="manual.txt",
            text="abcd",
            regions=(
                TextRegion(TextSpan(0, 2), RegionKind.LINTABLE, "prose"),
                TextRegion(TextSpan(3, 4), RegionKind.IGNORED, "markup"),
            ),
        )


def test_document_rejects_token_text_that_differs_from_source() -> None:
    with pytest.raises(ValueError, match="source text"):
        Document(
            uri="manual.txt",
            text="word",
            regions=(TextRegion(TextSpan(0, 4), RegionKind.LINTABLE, "prose"),),
            tokens=(Token(TextSpan(0, 4), "other", RegionKind.LINTABLE),),
        )


def test_location_uses_original_crlf_and_unicode_code_point_offsets() -> None:
    document = Document(uri="manual.txt", text="A\r\nβx\n")

    location = document.location(TextSpan(3, 4))

    assert location.start_line == 2
    assert location.start_column == 1
    assert location.end_line == 2
    assert location.end_column == 2
