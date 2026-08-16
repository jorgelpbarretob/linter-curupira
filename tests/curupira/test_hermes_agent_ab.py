import json
from pathlib import Path

from tools.curupira.hermes_agent_ab import build_comparison


def _write_run(
    root: Path,
    name: str,
    *,
    total_tokens: int,
    api_calls: int,
    elapsed_seconds: float,
    residual_findings: int,
) -> Path:
    path = root / f"{name}.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "curupira-hermes-agent-run/v1",
                "condition": name,
                "hermes_agent_version": "0.20.1",
                "usage": {
                    "input_tokens": total_tokens - 100,
                    "output_tokens": 100,
                    "total_tokens": total_tokens,
                    "api_calls": api_calls,
                    "model": "test-model",
                    "provider": "test-provider",
                },
                "elapsed_seconds": elapsed_seconds,
                "residual_findings": residual_findings,
            }
        ),
        encoding="utf-8",
    )
    return path


def test_comparison_uses_provider_tokens_and_reports_tradeoffs(tmp_path: Path) -> None:
    baseline = _write_run(
        tmp_path,
        "baseline",
        total_tokens=1_000,
        api_calls=1,
        elapsed_seconds=10.0,
        residual_findings=2,
    )
    treatment = _write_run(
        tmp_path,
        "curupira",
        total_tokens=1_200,
        api_calls=2,
        elapsed_seconds=12.0,
        residual_findings=0,
    )

    comparison = build_comparison(baseline, treatment)

    assert comparison["deltas"] == {
        "total_tokens": 200,
        "api_calls": 1,
        "elapsed_seconds": 2.0,
        "residual_findings": -2,
    }
    assert comparison["interpretation"] == {
        "token_reduction_observed": False,
        "residual_finding_reduction_observed": True,
    }
