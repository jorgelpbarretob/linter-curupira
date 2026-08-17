#!/usr/bin/env python3
"""Screening: modelos pequenos deixam residual no braço controle?

Testa cada candidato com a MESMA tarefa do case-007 (que inclui a exigência
"sem ponto e vírgula em prosa"), via OpenRouter chat completions, sem o
harness de agente. Se o modelo deixa residual mesmo instruído, ele é bom
candidato para o estudo pareado: o preflight teria o que corrigir.

Uso: python3 tools/curupira/screen_small_models.py
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CASE = REPO / "cases/case-007"
ENV_FILE = Path.home() / ".hermes/.env"
OUT = REPO / "artifacts/hermes-case-study/screen-small-models"
RULE = "CURUPIRA-PT-PONT-001"

MODELS = [
    "qwen/qwen3.8-27b",
    "meta/muse-glimmer-30b",
    "nvidia/nemotron-3.5-lightning:free",
    "poolside/laguna-xs-2.1:free",
    "liquid/lfm-2.5-2.6b:free",
    "google/gemma-4-26b-a4b-it:free",
    "mistralai/mistral-medium-3-5",
]


def load_key() -> str:
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("OPENROUTER_API_KEY ausente")


def lint_text(text: str) -> dict:
    with tempfile.NamedTemporaryFile(
        "w", suffix=".md", delete=False, encoding="utf-8"
    ) as fh:
        fh.write(text)
        path = fh.name
    try:
        proc = subprocess.run(
            ["curupira", "lint", path, "--enable-rule", RULE, "--format", "json"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        try:
            payload = json.loads(proc.stdout or "{}")
        except json.JSONDecodeError:
            payload = {}
        diags = payload.get("diagnostics") or []
        return {"exit_code": proc.returncode, "findings_n": len(diags)}
    finally:
        os.unlink(path)


def run_model(model: str, prompt: str, key: str) -> dict:
    body = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4096,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"model": model, "error": str(exc)[:200]}
    wall = round(time.time() - t0, 1)
    if not data.get("choices"):
        return {"model": model, "error": str(data.get("error"))[:200], "wall_s": wall}
    msg = data["choices"][0].get("message") or {}
    content = msg.get("content") or ""
    usage = data.get("usage") or {}
    return {
        "model": model,
        "content": content,
        "usage": {
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "reasoning_tokens": (usage.get("completion_tokens_details") or {}).get(
                "reasoning_tokens"
            ),
            "cost_usd": usage.get("cost"),
        },
        "wall_s": wall,
    }


def main() -> int:
    key = load_key()
    task = (CASE / "task.md").read_text(encoding="utf-8")
    input_text = (CASE / "inputs/procedimento.md").read_text(encoding="utf-8")
    prompt = f"""Você está reescrevendo um procedimento técnico pt-BR para um operador de fábrica.

Tarefa:
{task}

Texto atual do artefato:
{input_text}

Entregue APENAS o texto final reescrito do artefato, sem comentários."""

    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for model in MODELS:
        r = run_model(model, prompt, key)
        if "error" in r:
            print(f"{model:42} ERRO: {r['error']}")
            results.append(r)
            continue
        lint = lint_text(r["content"])
        semis = r["content"].count(";")
        (OUT / f"{model.replace('/', '__').replace(':', '_')}.md").write_text(
            r["content"], encoding="utf-8"
        )
        u = r["usage"]
        print(
            f"{model:42} findings={lint['findings_n']} semis={semis} "
            f"tok_out={u.get('completion_tokens')} cost=${u.get('cost_usd')} "
            f"wall={r['wall_s']}s"
        )
        results.append({**r, "lint": lint, "semicolon_count": semis})
    (OUT / "screen-results.json").write_text(
        json.dumps(
            [
                {k: v for k, v in r.items() if k != "content"}
                | {"chars": len(r.get("content") or "")}
                for r in results
            ],
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
