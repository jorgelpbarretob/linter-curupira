"""Contrato local e adapter preview para análise linguística pt-BR."""

from hermes_lint.linguistics.contracts import (
    LinguisticAnalysis,
    LinguisticContractError,
    LinguisticSentence,
    LocalLinguisticBackend,
    SurfaceToken,
    SyntacticWord,
    analysis_to_dict,
)
from hermes_lint.linguistics.spacy_backend import (
    NlpSetupError,
    SpacyPreviewBackend,
    adapt_spacy_document,
    load_preview_backend,
)

__all__ = [
    "LinguisticAnalysis",
    "LinguisticContractError",
    "LinguisticSentence",
    "LocalLinguisticBackend",
    "NlpSetupError",
    "SpacyPreviewBackend",
    "SurfaceToken",
    "SyntacticWord",
    "adapt_spacy_document",
    "analysis_to_dict",
    "load_preview_backend",
]
