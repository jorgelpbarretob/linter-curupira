from dataclasses import replace

import pytest

from ste_lint.nlp import NlpAnalysis, NlpToken


def token(
    text: str,
    start: int,
    *,
    dependency: str = "ROOT",
    head_index: int = 0,
) -> NlpToken:
    return NlpToken(
        text=text,
        start_offset=start,
        end_offset=start + len(text),
        lemma=text.casefold(),
        pos="VERB",
        tag="VB",
        dependency=dependency,
        head_index=head_index,
    )


def analysis(*tokens: NlpToken) -> NlpAnalysis:
    return NlpAnalysis(
        text="Open valve.",
        tokens=tokens,
        backend="spacy",
        backend_version="3.8.15",
        model="en_core_web_sm",
        model_version="3.8.0",
    )


def test_analysis_accepts_exact_ordered_source_offsets() -> None:
    value = analysis(
        token("Open", 0),
        token("valve", 5, dependency="dobj"),
        replace(token(".", 10, dependency="punct"), pos="PUNCT", tag="."),
    )

    assert value.tokens[1].text == "valve"


@pytest.mark.parametrize(
    ("tokens", "message"),
    [
        ((token("Wrong", 0),), "source text"),
        ((token("valve", 5), token("Open", 0)), "ordered"),
        ((token("Open", 0, head_index=4),), "head index"),
    ],
)
def test_analysis_rejects_misalignment_and_invalid_heads(
    tokens: tuple[NlpToken, ...], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        analysis(*tokens)


def test_token_rejects_empty_parser_attributes() -> None:
    with pytest.raises(ValueError, match="parser attributes"):
        replace(token("Open", 0), lemma="")
