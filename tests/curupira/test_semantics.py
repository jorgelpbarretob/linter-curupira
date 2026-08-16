import pytest

from curupira_lint.semantics import (
    SemanticContractError,
    SemanticSetupError,
    review_with_sabiazinho,
)
from curupira_lint.semantics.maritaca_backend import MARITACA_RESPONSES_URL


def test_sabiazinho_observations_are_anchored_locally() -> None:
    text = "Depois disso, reinicie o serviço."

    def transport(_request: dict[str, object], _api_key: str) -> dict[str, object]:
        return {
            "id": "response-test",
            "model": "sabiazinho-4-2026-01-06",
            "usage": {"input_tokens": 20, "output_tokens": 10, "total_tokens": 30},
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": (
                                '{"observations":[{"category":"ambiguous-reference",'
                                '"excerpt":"Depois disso","rationale":"O referente não é '
                                'explícito.","confidence":"high"}]}'
                            ),
                        }
                    ],
                }
            ],
        }

    result = review_with_sabiazinho(text, api_key="test-key", transport=transport)

    assert result["engine"]["provider"] == "maritaca"
    assert result["engine"]["model_requested"] == "sabiazinho-4-2026-01-06"
    assert result["observations"][0]["start_offset"] == 0
    assert result["observations"][0]["end_offset"] == 12
    assert result["usage"]["total_tokens"] == 30


def test_sabiazinho_rejects_an_unanchored_observation() -> None:
    def transport(_request: dict[str, object], _api_key: str) -> dict[str, object]:
        return {
            "model": "sabiazinho-4-2026-01-06",
            "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": (
                                '{"observations":[{"category":"other",'
                                '"excerpt":"trecho inventado","rationale":"teste",'
                                '"confidence":"low"}]}'
                            ),
                        }
                    ],
                }
            ],
        }

    with pytest.raises(SemanticContractError, match="trecho não ocorre exatamente uma vez"):
        review_with_sabiazinho("Texto real.", api_key="test-key", transport=transport)


def test_sabiazinho_rejects_a_repeated_excerpt() -> None:
    def transport(_request: dict[str, object], _api_key: str) -> dict[str, object]:
        return {
            "model": "sabiazinho-4-2026-01-06",
            "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": (
                                '{"observations":[{"category":"other",'
                                '"excerpt":"Repita.","rationale":"teste",'
                                '"confidence":"low"}]}'
                            ),
                        }
                    ],
                }
            ],
        }

    with pytest.raises(SemanticContractError, match="trecho não ocorre exatamente uma vez"):
        review_with_sabiazinho("Repita. Repita.", api_key="test-key", transport=transport)


def test_sabiazinho_rejects_a_whitespace_only_api_key() -> None:
    with pytest.raises(SemanticSetupError, match="MARITACA_API_KEY ausente"):
        review_with_sabiazinho("Texto.", api_key=" \t ")


def test_sabiazinho_uses_an_https_endpoint_and_injected_transport() -> None:
    captured: dict[str, object] = {}

    def transport(request: dict[str, object], api_key: str) -> dict[str, object]:
        captured.update(request=request, api_key=api_key)
        return {
            "model": "sabiazinho-4-2026-01-06",
            "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": '{"observations":[]}'}],
                }
            ],
        }

    review_with_sabiazinho("Texto.", api_key="test-key", transport=transport)

    assert MARITACA_RESPONSES_URL.startswith("https://")
    assert captured["api_key"] == "test-key"
    assert captured["request"]["store"] is False


def _semantic_response(observations: list[dict[str, object]]) -> dict[str, object]:
    import json

    return {
        "model": "sabiazinho-4-2026-01-06",
        "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
        "output": [
            {
                "type": "message",
                "content": [
                    {
                        "type": "output_text",
                        "text": json.dumps({"observations": observations}),
                    }
                ],
            }
        ],
    }


def test_sabiazinho_rejects_extra_observation_properties() -> None:
    observation: dict[str, object] = {
        "category": "other",
        "excerpt": "Texto.",
        "rationale": "teste",
        "confidence": "low",
        "unexpected": True,
    }

    with pytest.raises(SemanticContractError, match="campos inválidos"):
        review_with_sabiazinho(
            "Texto.",
            api_key="test-key",
            transport=lambda _request, _key: _semantic_response([observation]),
        )


def test_sabiazinho_rejects_more_than_twenty_observations() -> None:
    observations = [
        {
            "category": "other",
            "excerpt": f"Trecho {index}.",
            "rationale": "teste",
            "confidence": "low",
        }
        for index in range(21)
    ]
    text = " ".join(str(item["excerpt"]) for item in observations)

    with pytest.raises(SemanticContractError, match="observations inválido"):
        review_with_sabiazinho(
            text,
            api_key="test-key",
            transport=lambda _request, _key: _semantic_response(observations),
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [("category", "invented"), ("confidence", "certain")],
)
def test_sabiazinho_rejects_values_outside_contract_enums(field: str, value: str) -> None:
    observation = {
        "category": "other",
        "excerpt": "Texto.",
        "rationale": "teste",
        "confidence": "low",
    }
    observation[field] = value

    with pytest.raises(SemanticContractError, match="categoria ou confiança inválida"):
        review_with_sabiazinho(
            "Texto.",
            api_key="test-key",
            transport=lambda _request, _key: _semantic_response([observation]),
        )
