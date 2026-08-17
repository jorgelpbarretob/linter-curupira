#!/usr/bin/env python3
"""Screening v2: modelos pequenos deixam residual SEM a instrução anti-semicolon?

Mesma tarefa do case-007, mas com o requisito "Sem ponto e vírgula em prosa"
removido da tarefa (simula autor que não conhece a regra). Modelos que deixam
residual são os bons candidatos para o estudo pareado: ali o preflight corrige.

Controla reasoning do qwen3.8-27b (effort low) para não torrar tokens em thinking.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ENV_FILE = Path.home() / ".hermes/.env"
OUT = REPO / "artifacts/hermes-case-study/screen-small-models-v2"
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


def semis_in_prose(text: str) -> int:
    no_fences = re.sub(r"```.*?```", "", text, flags=re.S)
    no_inline = re.sub(r"`[^`]*`", "", no_fences)
    return no_inline.count(";")


def run_model(model: str, prompt: str, key: str) -> dict:
    body: dict = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 8192,
    }
    if "qwen3.8" in model:
        body["reasoning"] = {"effort": "low"}
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
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
    ch = data["choices"][0]
    msg = ch.get("message") or {}
    content = msg.get("content") or ""
    usage = data.get("usage") or {}
    return {
        "model": model,
        "content": content,
        "finish_reason": ch.get("finish_reason"),
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
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=None)
    ap.add_argument("--case", default="case-007")
    ap.add_argument("--keep-instruction", action="store_true",
                    help="não remove a linha anti-semicolon da tarefa")
    args = ap.parse_args()
    models = args.models or MODELS
    case_dir = REPO / "cases" / args.case
    key = load_key()
    task = (case_dir / "task.md").read_text(encoding="utf-8")
    # remove o requisito anti-semicolon (linha com "Sem ponto e vírgula em prosa")
    task_lines = task.splitlines()
    if not args.keep_instruction:
        task_lines = [ln for ln in task_lines if "ponto e vírgula" not in ln.lower()]
    task_stripped = "\n".join(task_lines)
    input_rel = json.loads((case_dir / "manifest.json").read_text(encoding="utf-8")).get(
        "input_rel", "inputs/procedimento.md"
    )
    input_text = (case_dir / input_rel).read_text(encoding="utf-8")
    prompt = f"""Você está reescrevendo um procedimento técnico pt-BR para um operador de fábrica.

Tarefa:
{task_stripped}

Texto atual do artefato:
{input_text}

Entregue APENAS o texto final reescrito do artefato, sem comentários."""

    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for model in models:
        r = run_model(model, prompt, key)
        if "error" in r:
            print(f"{model:42} ERRO: {r['error']}")
            results.append(r)
            continue
        content = r["content"]
        lint = lint_text(content)
        semis = semis_in_prose(content)
        (OUT / f"{model.replace('/', '__').replace(':', '_')}.md").write_text(
            content, encoding="utf-8"
        )
        u = r["usage"]
        print(
            f"{model:42} findings={lint['findings_n']} semis_prosa={semis} "
            f"chars={len(content)} tok_out={u.get('completion_tokens')} "
            f"reason_tok={u.get('reasoning_tokens')} cost=${u.get('cost_usd')} "
            f"finish={r.get('finish_reason')} wall={r['wall_s']}s"
        )
        results.append(
            {k: v for k, v in r.items() if k != "content"}
            | {"lint": lint, "semis_in_prose": semis, "chars": len(content)}
        )
    out_file = OUT / "screen-results.json"
    prev: list = []
    if out_file.is_file():
        try:
            prev = json.loads(out_file.read_text(encoding="utf-8"))
            prev = [p for p in prev if p.get("model") not in models]
        except (json.JSONDecodeError, OSError):
            prev = []
    out_file.write_text(
        json.dumps(prev + results, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
