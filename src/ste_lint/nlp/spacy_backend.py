"""Lazy, pinned spaCy adapter; importing this module does not import spaCy."""

from __future__ import annotations

import importlib
import importlib.metadata
from collections.abc import Iterable, Mapping
from typing import Protocol, cast

from ste_lint.engine.configuration import NlpConfiguration
from ste_lint.nlp.contracts import NlpAnalysis, NlpToken
from ste_lint.nlp.errors import NlpSetupError

SPACY_VERSION = "3.8.15"
MODEL_PACKAGE = "en_core_web_sm"
MODEL_DISTRIBUTION = "en-core-web-sm"
MODEL_VERSION = "3.8.0"


class _Head(Protocol):
    i: int


class _SdkToken(Protocol):
    text: str
    idx: int
    lemma_: str
    pos_: str
    tag_: str
    dep_: str
    head: _Head


class _LanguageModel(Protocol):
    pipe_names: list[str]
    meta: Mapping[str, object]

    def __call__(self, text: str) -> Iterable[_SdkToken]: ...


class _ModelPackage(Protocol):
    def load(self, **overrides: object) -> _LanguageModel: ...


class SpacyNlpBackend:
    """Convert a loaded spaCy model to the immutable project contract."""

    def __init__(self, model: _LanguageModel) -> None:
        self._model = model

    def analyze(self, text: str) -> NlpAnalysis:
        sdk_tokens = tuple(self._model(text))
        tokens = tuple(
            NlpToken(
                text=token.text,
                start_offset=token.idx,
                end_offset=token.idx + len(token.text),
                lemma=token.lemma_,
                pos=token.pos_,
                tag=token.tag_,
                dependency=token.dep_,
                head_index=token.head.i,
            )
            for token in sdk_tokens
        )
        return NlpAnalysis(
            text=text,
            tokens=tokens,
            backend="spacy",
            backend_version=SPACY_VERSION,
            model=MODEL_PACKAGE,
            model_version=MODEL_VERSION,
        )


def load_spacy_backend(configuration: NlpConfiguration) -> SpacyNlpBackend:
    """Load only the exact backend and model accepted by ADR-014."""

    if configuration != NlpConfiguration():
        raise NlpSetupError("NLP configuration does not match the accepted pinned backend")
    try:
        spacy_version = importlib.metadata.version("spacy")
        model_version = importlib.metadata.version(MODEL_DISTRIBUTION)
    except importlib.metadata.PackageNotFoundError as error:
        raise NlpSetupError(
            "NLP support is not installed; run 'uv sync --extra nlp --group nlp-model'"
        ) from error
    if spacy_version != SPACY_VERSION:
        raise NlpSetupError(f"spaCy {SPACY_VERSION} is required, found {spacy_version}")
    if model_version != MODEL_VERSION:
        raise NlpSetupError(f"{MODEL_PACKAGE} {MODEL_VERSION} is required, found {model_version}")
    try:
        package = cast(_ModelPackage, importlib.import_module(MODEL_PACKAGE))
        model = package.load(exclude=["ner"])
    except (ImportError, OSError, ValueError) as error:
        raise NlpSetupError("the pinned NLP model could not be loaded") from error
    if not {"tagger", "parser"}.issubset(model.pipe_names):
        raise NlpSetupError("the NLP model must provide tagger and parser pipelines")
    expected_metadata = {
        "lang": "en",
        "name": "core_web_sm",
        "version": MODEL_VERSION,
        "license": "MIT",
        "spacy_version": ">=3.8.0,<3.9.0",
    }
    if any(model.meta.get(key) != value for key, value in expected_metadata.items()):
        raise NlpSetupError("the loaded NLP model metadata does not match ADR-014")
    return SpacyNlpBackend(model)
