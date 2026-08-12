import importlib
import importlib.metadata
from collections.abc import Mapping
from dataclasses import dataclass

import pytest

from ste_lint.engine import NlpConfiguration
from ste_lint.nlp import NlpSetupError
from ste_lint.nlp.spacy_backend import SpacyNlpBackend, load_spacy_backend


@dataclass(frozen=True)
class FakeHead:
    i: int


@dataclass(frozen=True)
class FakeToken:
    text: str
    idx: int
    lemma_: str
    pos_: str
    tag_: str
    dep_: str
    head: FakeHead


class FakeModel:
    def __init__(self, tokens: tuple[FakeToken, ...]) -> None:
        self.tokens = tokens

    def __call__(self, text: str) -> tuple[FakeToken, ...]:
        del text
        return self.tokens


class FakeLoadedModel(FakeModel):
    def __init__(
        self,
        *,
        pipe_names: list[str] | None = None,
        meta: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(())
        self.pipe_names = pipe_names or ["tagger", "parser"]
        self.meta = meta or {
            "lang": "en",
            "name": "core_web_sm",
            "version": "3.8.0",
            "license": "MIT",
            "spacy_version": ">=3.8.0,<3.9.0",
        }


@dataclass(frozen=True)
class FakePackage:
    model: FakeLoadedModel

    def load(self, **overrides: object) -> FakeLoadedModel:
        assert overrides == {"exclude": ["ner"]}
        return self.model


def patch_pinned_distributions(monkeypatch: pytest.MonkeyPatch) -> None:
    versions = {"spacy": "3.8.15", "en-core-web-sm": "3.8.0"}
    monkeypatch.setattr(importlib.metadata, "version", versions.__getitem__)


def test_adapter_converts_sdk_tokens_to_immutable_contracts() -> None:
    model = FakeModel(
        (
            FakeToken("Open", 0, "open", "VERB", "VB", "ROOT", FakeHead(0)),
            FakeToken("valve", 5, "valve", "NOUN", "NN", "dobj", FakeHead(0)),
            FakeToken(".", 10, ".", "PUNCT", ".", "punct", FakeHead(0)),
        )
    )
    backend = SpacyNlpBackend(model)  # type: ignore[arg-type]

    analysis = backend.analyze("Open valve.")

    assert analysis.backend == "spacy"
    assert analysis.backend_version == "3.8.15"
    assert analysis.model == "en_core_web_sm"
    assert analysis.model_version == "3.8.0"
    assert analysis.tokens[1].head_index == 0


def test_adapter_rejects_token_text_that_does_not_match_source() -> None:
    backend = SpacyNlpBackend(
        FakeModel((FakeToken("Wrong", 0, "wrong", "VERB", "VB", "ROOT", FakeHead(0)),))
    )  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="source text"):
        backend.analyze("Open.")


def test_loader_rejects_missing_optional_install(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing_distribution(name: str) -> str:
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(importlib.metadata, "version", missing_distribution)

    with pytest.raises(NlpSetupError, match="uv sync --extra nlp --group nlp-model"):
        load_spacy_backend(NlpConfiguration())


@pytest.mark.parametrize(
    ("distribution", "version", "message"),
    [
        ("spacy", "3.8.14", "spaCy 3.8.15 is required"),
        ("en-core-web-sm", "3.7.0", "en_core_web_sm 3.8.0 is required"),
    ],
)
def test_loader_rejects_unpinned_distribution_versions(
    monkeypatch: pytest.MonkeyPatch,
    distribution: str,
    version: str,
    message: str,
) -> None:
    versions = {"spacy": "3.8.15", "en-core-web-sm": "3.8.0"}
    versions[distribution] = version
    monkeypatch.setattr(importlib.metadata, "version", versions.__getitem__)

    with pytest.raises(NlpSetupError, match=message):
        load_spacy_backend(NlpConfiguration())


def test_loader_rejects_missing_required_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_pinned_distributions(monkeypatch)
    package = FakePackage(FakeLoadedModel(pipe_names=["tagger"]))
    monkeypatch.setattr(importlib, "import_module", lambda name: package)

    with pytest.raises(NlpSetupError, match="tagger and parser"):
        load_spacy_backend(NlpConfiguration())


def test_loader_wraps_model_import_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_pinned_distributions(monkeypatch)

    def fail_import(name: str) -> object:
        raise ImportError(name)

    monkeypatch.setattr(importlib, "import_module", fail_import)

    with pytest.raises(NlpSetupError, match="could not be loaded"):
        load_spacy_backend(NlpConfiguration())


@pytest.mark.parametrize("field", ["lang", "name", "version", "license", "spacy_version"])
def test_loader_rejects_divergent_model_metadata(
    monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    patch_pinned_distributions(monkeypatch)
    metadata = dict(FakeLoadedModel().meta)
    metadata[field] = "divergent"
    package = FakePackage(FakeLoadedModel(meta=metadata))
    monkeypatch.setattr(importlib, "import_module", lambda name: package)

    with pytest.raises(NlpSetupError, match="metadata does not match ADR-014"):
        load_spacy_backend(NlpConfiguration())
