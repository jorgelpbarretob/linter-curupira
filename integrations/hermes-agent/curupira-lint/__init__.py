"""Hermes Agent plugin registration for the Curupira preflight."""

from .gate import build_output_gate
from .schemas import CURUPIRA_LINT
from .tools import handle_curupira_lint


def register(context: object) -> None:
    """Register the local Curupira wrapper as an opt-in Hermes tool."""
    context.register_tool(  # type: ignore[attr-defined]
        name="curupira_lint",
        toolset="curupira",
        schema=CURUPIRA_LINT,
        handler=handle_curupira_lint,
    )
    context.register_hook(  # type: ignore[attr-defined]
        "pre_verify",
        build_output_gate(context.dispatch_tool),  # type: ignore[attr-defined]
    )
