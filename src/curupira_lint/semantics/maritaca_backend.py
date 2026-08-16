"""Adapter opt-in para observações semânticas ancoradas do Sabiazinho 4."""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Callable
from typing import Any, Final, cast

MARITACA_RESPONSES_URL: Final = "https://chat.maritaca.ai/api/responses"
DEFAULT_MODEL: Final = "sabiazinho-4-2026-01-06"
MAX_SEMANTIC_CHARACTERS: Final = 80_000
_CATEGORIES: Final = {
    "ambiguous-reference",
    "implicit-agent",
    "multiple-actions",
    "terminology",
    "other",
}
_CONFIDENCES: Final = {"low", "medium", "high"}
Transport = Callable[[dict[str, object], str], dict[str, object]]


class SemanticContractError(ValueError):
    """Indica resposta semântica inválida ou não ancorada no texto exato."""


class SemanticSetupError(RuntimeError):
    """Indica configuração ausente para o backend semântico opt-in."""


def review_with_sabiazinho(
    text: str,
    *,
    api_key: str,
    model: str = DEFAULT_MODEL,
    transport: Transport | None = None,
) -> dict[str, object]:
    sanitized_api_key = api_key.strip()
    if not sanitized_api_key:
        raise SemanticSetupError("MARITACA_API_KEY ausente")
    if len(text) > MAX_SEMANTIC_CHARACTERS:
        raise SemanticContractError(
            f"revisão semântica aceita no máximo {MAX_SEMANTIC_CHARACTERS} caracteres"
        )
    request = _build_request(text, model)
    response = (transport or _post_json)(request, sanitized_api_key)
    payload = _extract_payload(response)
    observations = _anchor_observations(text, payload)
    usage = _require_object(response.get("usage"), "usage")
    return {
        "engine": {
            "provider": "maritaca",
            "model_requested": model,
            "model_returned": _require_string(response.get("model"), "model"),
        },
        "usage": {
            "input_tokens": _require_int(usage.get("input_tokens"), "input_tokens"),
            "output_tokens": _require_int(usage.get("output_tokens"), "output_tokens"),
            "total_tokens": _require_int(usage.get("total_tokens"), "total_tokens"),
        },
        "observations": observations,
    }


def _build_request(text: str, model: str) -> dict[str, object]:
    return {
        "model": model,
        "input": (
            "Analise o texto técnico pt-BR abaixo. Aponte somente problemas semânticos "
            "plausíveis nas categorias permitidas. Cada excerpt deve ser uma substring "
            "exata e única do texto. Não reescreva o documento nem emita regra normativa.\n\n"
            f"TEXTO:\n{text}"
        ),
        "instructions": (
            "Você é o motor semântico Curupira em preview. Use o documento somente para "
            "esta resposta, não o reproduza além dos excerpts exatos necessários e retorne "
            "somente JSON no schema."
        ),
        "max_output_tokens": 4_000,
        "store": False,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "curupira_semantic_review_v1",
                "strict": True,
                "schema": _response_schema(),
            }
        },
    }


def _response_schema() -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["observations"],
        "properties": {
            "observations": {
                "type": "array",
                "maxItems": 20,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["category", "excerpt", "rationale", "confidence"],
                    "properties": {
                        "category": {"enum": sorted(_CATEGORIES)},
                        "excerpt": {"type": "string", "minLength": 1},
                        "rationale": {"type": "string", "minLength": 1},
                        "confidence": {"enum": sorted(_CONFIDENCES)},
                    },
                },
            }
        },
    }


def _post_json(request_body: dict[str, object], api_key: str) -> dict[str, object]:
    request = urllib.request.Request(
        MARITACA_RESPONSES_URL,
        data=json.dumps(request_body, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        parsed = json.loads(response.read())
    return _require_object(parsed, "resposta")


def _extract_payload(response: dict[str, object]) -> dict[str, object]:
    output = response.get("output")
    if not isinstance(output, list):
        raise SemanticContractError("output ausente na resposta Maritaca")
    for block in output:
        if not isinstance(block, dict) or block.get("type") != "message":
            continue
        content = block.get("content")
        if not isinstance(content, list):
            continue
        for item in content:
            if isinstance(item, dict) and item.get("type") == "output_text":
                raw_text = _require_string(item.get("text"), "output_text.text")
                try:
                    return _require_object(json.loads(raw_text), "payload semântico")
                except json.JSONDecodeError as error:
                    raise SemanticContractError("JSON semântico inválido") from error
    raise SemanticContractError("output_text ausente na resposta Maritaca")


def _anchor_observations(text: str, payload: dict[str, object]) -> list[dict[str, object]]:
    if set(payload) != {"observations"}:
        raise SemanticContractError("payload semântico contém campos inválidos")
    raw_observations = payload.get("observations")
    if not isinstance(raw_observations, list) or len(raw_observations) > 20:
        raise SemanticContractError("observations inválido")
    anchored: list[dict[str, object]] = []
    for raw in raw_observations:
        observation = _require_object(raw, "observation")
        if set(observation) != {"category", "excerpt", "rationale", "confidence"}:
            raise SemanticContractError("observation contém campos inválidos")
        excerpt = _require_string(observation.get("excerpt"), "excerpt")
        if text.count(excerpt) != 1:
            raise SemanticContractError("trecho não ocorre exatamente uma vez no texto")
        category = _require_string(observation.get("category"), "category")
        confidence = _require_string(observation.get("confidence"), "confidence")
        if category not in _CATEGORIES or confidence not in _CONFIDENCES:
            raise SemanticContractError("categoria ou confiança inválida")
        start = text.index(excerpt)
        anchored.append(
            {
                "category": category,
                "excerpt": excerpt,
                "start_offset": start,
                "end_offset": start + len(excerpt),
                "rationale": _require_string(observation.get("rationale"), "rationale"),
                "confidence": confidence,
            }
        )
    return anchored


def _require_object(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SemanticContractError(f"{field} deve ser objeto")
    return cast(dict[str, Any], value)


def _require_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise SemanticContractError(f"{field} deve ser texto não vazio")
    return value


def _require_int(value: object, field: str) -> int:
    if not isinstance(value, int) or value < 0:
        raise SemanticContractError(f"{field} deve ser inteiro não negativo")
    return value
