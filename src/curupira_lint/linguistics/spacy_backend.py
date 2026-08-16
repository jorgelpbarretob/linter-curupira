"""Adapter local e lazy do candidato spaCy pt-BR em status preview."""

from __future__ import annotations

import hashlib
import importlib
import importlib.metadata
from typing import Any, Final

from curupira_lint.linguistics.contracts import (
    LinguisticAnalysis,
    LinguisticContractError,
    LinguisticSentence,
    SurfaceToken,
    SyntacticWord,
)

SPACY_VERSION: Final = "3.8.15"
MODEL_NAME: Final = "pt_core_news_sm"
MODEL_VERSION: Final = "3.8.0"
MODEL_SHA256: Final = "c304fa04db3af73cd08a250feacf560506e15a2ec2469bd1b09f06847f6b455c"
PIPE_NAMES: Final = ("tok2vec", "morphologizer", "parser", "lemmatizer", "attribute_ruler")
CONFIGURATION_SHA256: Final = hashlib.sha256(
    b"spacy=3.8.15;model=pt_core_news_sm==3.8.0;"
    b"pipes=tok2vec,morphologizer,parser,lemmatizer,attribute_ruler;exclude=ner;device=cpu"
).hexdigest()


class NlpSetupError(RuntimeError):
    """Indica ausência ou divergência da instalação NLP opcional."""


class SpacyPreviewBackend:
    def __init__(self, pipeline: Any) -> None:
        self._pipeline = pipeline

    def analyze(self, text: str) -> LinguisticAnalysis:
        return adapt_spacy_document(text, self._pipeline(text))


def load_preview_backend() -> SpacyPreviewBackend:
    """Carrega somente artefatos locais e recusa versões/configuração divergentes."""
    try:
        spacy_module = importlib.import_module("spacy")
        model_module = importlib.import_module(MODEL_NAME)
        model_version = importlib.metadata.version(MODEL_NAME)
    except (ImportError, importlib.metadata.PackageNotFoundError) as error:
        raise NlpSetupError(
            'NLP preview ausente; instale com `pip install "curupira-lint[nlp]"`'
        ) from error
    if getattr(spacy_module, "__version__", None) != SPACY_VERSION:
        raise NlpSetupError(f"spaCy deve ser {SPACY_VERSION}")
    if model_version != MODEL_VERSION:
        raise NlpSetupError(f"{MODEL_NAME} deve ser {MODEL_VERSION}")
    try:
        spacy_module.require_cpu()
        pipeline = model_module.load(exclude=["ner"])
    except (OSError, ValueError) as error:
        raise NlpSetupError(
            f"não foi possível carregar {MODEL_NAME} localmente: {error}"
        ) from error
    if tuple(pipeline.pipe_names) != PIPE_NAMES:
        raise NlpSetupError("componentes do pipeline spaCy divergem da configuração preview")
    return SpacyPreviewBackend(pipeline)


def adapt_spacy_document(text: str, doc: Any) -> LinguisticAnalysis:
    """Projeta um Doc do SDK em tipos Curupira com invariantes verificadas."""
    if doc.text != text:
        raise LinguisticContractError("backend alterou o texto exato recebido")
    sdk_tokens = [token for token in doc if not token.is_space]
    if not sdk_tokens:
        return _analysis(text, (), (), ())
    token_index = {token.i: index for index, token in enumerate(sdk_tokens)}
    surface_tokens = tuple(
        SurfaceToken(token.text, token.idx, token.idx + len(token.text)) for token in sdk_tokens
    )
    sentence_index_by_token: dict[int, int] = {}
    sentences: list[LinguisticSentence] = []
    first_word = 0
    expected_surface = 0
    for sdk_sentence in doc.sents:
        members = [token for token in sdk_sentence if not token.is_space]
        if not members:
            continue
        first_surface = token_index[members[0].i]
        past_last_surface = token_index[members[-1].i] + 1
        if first_surface != expected_surface or past_last_surface - first_surface != len(members):
            raise LinguisticContractError("tokens de sentença não formam partição contígua")
        sentence_index = len(sentences)
        for token in members:
            if token.i in sentence_index_by_token:
                raise LinguisticContractError("token pertence a mais de uma sentença")
            sentence_index_by_token[token.i] = sentence_index
        sentences.append(
            LinguisticSentence(
                members[0].idx,
                members[-1].idx + len(members[-1].text),
                first_surface,
                past_last_surface,
                first_word,
                first_word + len(members),
            )
        )
        first_word += len(members)
        expected_surface = past_last_surface
    if expected_surface != len(sdk_tokens):
        raise LinguisticContractError(
            "sentenças não cobrem todos os tokens: "
            f"cobertos={expected_surface}, emitidos={len(sdk_tokens)}"
        )
    words: list[SyntacticWord] = []
    for token in sdk_tokens:
        is_root = token.dep_ == "ROOT"
        if is_root and token.head.i != token.i:
            raise LinguisticContractError("raiz deve usar auto-head no SDK")
        if not is_root and token.head.i == token.i:
            raise LinguisticContractError("palavra não raiz não pode usar auto-head no SDK")
        if not is_root and token.head.i not in token_index:
            raise LinguisticContractError("head não corresponde a palavra emitida")
        words.append(
            SyntacticWord(
                surface_token_index=token_index[token.i],
                lemma=token.lemma_,
                upos=token.pos_,
                xpos=token.tag_ or None,
                features=tuple(sorted(token.morph.to_dict().items())),
                dependency="root" if is_root else token.dep_,
                head_word_index=None if is_root else token_index[token.head.i],
                sentence_index=sentence_index_by_token[token.i],
            )
        )
    return _analysis(text, surface_tokens, tuple(words), tuple(sentences))


def _analysis(
    text: str,
    surface_tokens: tuple[SurfaceToken, ...],
    words: tuple[SyntacticWord, ...],
    sentences: tuple[LinguisticSentence, ...],
) -> LinguisticAnalysis:
    return LinguisticAnalysis(
        text=text,
        surface_tokens=surface_tokens,
        words=words,
        sentences=sentences,
        backend="spaCy",
        backend_version=SPACY_VERSION,
        model=MODEL_NAME,
        model_version=MODEL_VERSION,
        model_sha256=MODEL_SHA256,
        configuration_sha256=CONFIGURATION_SHA256,
    )
