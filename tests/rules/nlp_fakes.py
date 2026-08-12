from dataclasses import dataclass

from ste_lint.nlp import NlpAnalysis, NlpToken


@dataclass(frozen=True)
class FakeNlpBackend:
    value: NlpAnalysis

    def analyze(self, text: str) -> NlpAnalysis:
        if text != self.value.text:
            raise AssertionError(f"unexpected analyzed text: {text!r}")
        return self.value


def make_analysis(
    text: str,
    specifications: tuple[tuple[str, str, str, str, int], ...],
) -> NlpAnalysis:
    cursor = 0
    tokens: list[NlpToken] = []
    for token_text, pos, tag, dependency, head_index in specifications:
        start = text.index(token_text, cursor)
        end = start + len(token_text)
        tokens.append(
            NlpToken(
                text=token_text,
                start_offset=start,
                end_offset=end,
                lemma=token_text.casefold(),
                pos=pos,
                tag=tag,
                dependency=dependency,
                head_index=head_index,
            )
        )
        cursor = end
    return NlpAnalysis(
        text=text,
        tokens=tuple(tokens),
        backend="fake",
        backend_version="1",
        model="synthetic",
        model_version="1",
    )
