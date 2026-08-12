"""Operational errors for optional NLP capabilities."""


class NlpSetupError(RuntimeError):
    """Raised when an explicitly enabled NLP capability is unavailable."""
