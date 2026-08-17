"""Hermes output gate backed by the local Curupira wrapper."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


def _format_findings(event: dict[str, Any]) -> str:
    findings = []
    for file_result in event.get("files") or []:
        path = file_result.get("path") or "document"
        for diagnostic in file_result.get("diagnostics") or []:
            location = diagnostic.get("location") or {}
            line = location.get("start_line") or "?"
            column = location.get("start_column")
            span = f"{path}:{line}" + (f":{column}" if column else "")
            rule = diagnostic.get("rule_id") or "curupira"
            message = diagnostic.get("message") or "diagnostic reported"
            findings.append(f"- {span}: {rule}: {message}")
    return "\n".join(findings) or "- Review the Curupira diagnostics."


def _format_operational_errors(event: dict[str, Any]) -> str:
    errors = []
    for error in event.get("operational_errors") or []:
        code = error.get("code") or "curupira_error"
        message = error.get("message") or "operational preflight error"
        errors.append(f"- {code}: {message}")
    return "\n".join(errors) or "- Curupira did not return an operational error detail."


def build_output_gate(
    dispatch_tool: Callable[[str, dict[str, Any]], str],
) -> Callable[..., dict[str, str] | None]:
    """Build the ``pre_verify`` callback for the registered plugin scope."""

    def pre_verify(*, changed_paths: list[str], attempt: int = 0, **_: object):
        try:
            raw_event = dispatch_tool("curupira_lint", {"paths": list(changed_paths)})
        except Exception:
            logger.exception("Curupira output-gate dispatch failed")
            return {
                "action": "block_completion",
                "message": "Curupira output gate failed: tool dispatch error.",
            }
        try:
            event = json.loads(raw_event)
            expected_exit_codes = {
                "passed": 0,
                "needs_review": 1,
                "blocked": 2,
                "not_applicable": 0,
            }
            if (
                not isinstance(event, dict)
                or event.get("event") != "preflight_completed"
                or event.get("status") not in expected_exit_codes
                or event.get("exit_code") != expected_exit_codes.get(event.get("status"))
                or not isinstance(event.get("files"), list)
                or not isinstance(event.get("operational_errors"), list)
            ):
                raise ValueError("invalid preflight event")
        except (json.JSONDecodeError, TypeError, ValueError):
            logger.error("Curupira output gate received an invalid preflight event")
            return {
                "action": "block_completion",
                "message": "Curupira output gate failed: invalid preflight event.",
            }
        logger.info("Curupira output-gate event: %s", raw_event)
        if event.get("status") in {"passed", "not_applicable"}:
            return None
        if event.get("status") == "needs_review" and attempt == 0:
            return {
                "action": "continue",
                "message": (
                    "Correct the Curupira diagnostics, then finish again.\n"
                    + _format_findings(event)
                ),
            }
        if event.get("status") == "needs_review":
            return {
                "action": "block_completion",
                "message": (
                    "Curupira encontrou diagnóstico residual após a correção.\n"
                    + _format_findings(event)
                ),
            }
        if event.get("status") == "blocked":
            return {
                "action": "block_completion",
                "message": (
                    "Curupira terminou com erro operacional.\n" + _format_operational_errors(event)
                ),
            }
        return {
            "action": "block_completion",
            "message": "Curupira preflight did not pass.",
        }

    return pre_verify
