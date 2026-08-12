"""Executable deterministic rules admitted to the catalog."""

from ste_lint.rules.descriptive_paragraph import DescriptiveParagraphLengthRule
from ste_lint.rules.semicolon import SemicolonRule
from ste_lint.rules.sentence_length import (
    DescriptiveSentenceLengthRule,
    ProceduralSentenceLengthRule,
)
from ste_lint.rules.vertical_list_colon import VerticalListLeadInColonRule

__all__ = [
    "DescriptiveSentenceLengthRule",
    "DescriptiveParagraphLengthRule",
    "ProceduralSentenceLengthRule",
    "SemicolonRule",
    "VerticalListLeadInColonRule",
]
