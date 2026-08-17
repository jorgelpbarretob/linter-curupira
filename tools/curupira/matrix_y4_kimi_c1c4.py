#!/usr/bin/env python3
"""Matrix Y4 second reviewer: blind Kimi 2.7 with rubric C1-C4.

Scores the same 24 blinded artifacts (M01..M24) already scored by Maritaca,
using the C1-C4 semantic rubric v1 (docs/hermes-case-study/semantic-rubric-v1.md)
plus clarity_1to5 and countable findings, so Kimi-Maritaca agreement is computable.

accept_class and S are derived deterministically from the rubric rules;
the model's own claimed values are kept for integrity.

Usage:
  python3 tools/curupira/matrix_y4_kimi_c1c4.py [--limit 0] [--resume]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

BRT = timezone(timedelta(hours=-3))
CATEGORIES = ["ambiguous-reference", "implicit-agent", "multiple-actions", "terminology"]
SEVERITIES = ["major", "minor"]
ALLOWED_CLASS = {"aceito", "aceito_retrabalho_menor", "rejeitado_retrabalho_maior", "bloqueado"}

PROMPT = """\
Você é revisor cego de documentação técnica pt-BR. NÃO tente adivinhar qual \
sistema ou modelo gerou o texto. Avalie SOMENTE o artefato fornecido.

Rubrica semântica v1. Quatro categorias, cada Ci em {0,1,2}.

C1 Executabilidade: o leitor consegue fazer a tarefa na ordem certa?
0 falha material (ação crítica ausente, ordem perigosa, passo impossível).
1 a sequência existe mas exige inferência frequente.
2 cada passo é acionável (verbo + objeto + condição quando preciso).

C2 Fidelidade e cobertura: cobre o pedido e preserva fatos/tags/limites dados?
0 requisito obrigatório ausente ou fato inventado material.
1 cobre o núcleo com omissão menor não crítica.
2 checklist obrigatório completo e fiel às fontes do caso.

C3 Estrutura e escaneabilidade: o formato ajuda leitura rápida?
0 bloco denso sem ordem útil.
1 lista/seções com ruído ou misturas.
2 títulos/passos/listas permitem scan em segundos.

C4 Ambiguidade residual: quanto o operador ainda precisa adivinhar?
0 ambiguidade crítica (quem, o quê, quando parar, o que é proibido).
1 vaguidões menores ("se necessário", "conforme local") sem risco alto.
2 critérios de parada, proibições e referências explícitos o bastante.

critical_block = true só se erro técnico crítico (risco de segurança/processo) \
ou requisito obrigatório ausente. Conte só o que o texto permite verificar. \
Não invente contexto de planta.

Achados semânticos: liste ocorrências das categorias ambiguous-reference, \
implicit-agent, multiple-actions, terminology. Cada achado exige "excerpt" \
LITERAL copiado do artefato. Zero achados é válido. Preferência de estilo não conta.

Responda começando com { e terminando com }. Nenhuma palavra fora do JSON. \
Sem raciocínio, sem plano, sem texto antes ou depois.

Responda APENAS JSON válido:
{
  "C1_executability": 2,
  "C2_fidelity_coverage": 2,
  "C3_structure_scan": 2,
  "C4_ambiguity": 1,
  "critical_block": false,
  "clarity_1to5": 4,
  "findings": [
    {"category": "implicit-agent", "severity": "minor",
     "excerpt": "trecho literal", "rationale": "até 120 chars"}
  ],
  "justification": "1 frase até 240 chars"
}
"""


def load_env() -> None:
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line or line.lstrip().startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[len("export "):]
            k, _, v = line.partition("=")
            k = k.strip()
            if k in {"KIMI_API_KEY", "KIMI_BASE_URL"}:
                v = v.strip().strip('"').strip("'")
                if v:
                    os.environ[k] = v


def post_chat(url: str, api_key: str, payload: dict, timeout: int = 300) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:800]
        raise RuntimeError(f"HTTP {e.code}: {body}") from e


def message_text(body: dict) -> str:
    msg = ((body.get("choices") or [{}])[0].get("message") or {})
    content = (msg.get("content") or "").strip()
    if content:
        return content
    return (msg.get("reasoning_content") or "").strip()


def usage_of(body: dict) -> dict:
    u = body.get("usage") or {}
    tin = u.get("prompt_tokens") or u.get("input_tokens")
    tout = u.get("completion_tokens") or u.get("output_tokens")
    tot = u.get("total_tokens")
    return {
        "input_tokens": int(tin or 0),
        "output_tokens": int(tout or 0),
        "total_tokens": int(tot or ((tin or 0) + (tout or 0))),
    }


def norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def balanced_candidates(text: str) -> list[str]:
    """All balanced {...} substrings, longest first."""
    out = []
    starts = [i for i, ch in enumerate(text) if ch == "{"]
    for s in starts:
        depth = 0
        in_str = False
        esc = False
        for i in range(s, len(text)):
            ch = text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    out.append(text[s:i + 1])
                    break
    out.sort(key=len, reverse=True)
    return out


def extract_json(text: str) -> dict:
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass
    for cand in balanced_candidates(text):
        try:
            obj = json.loads(cand)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue
    raise ValueError(f"no json in model output: {text[:200]}")


def validate_findings(raw: list, artifact_text: str) -> tuple[list, list]:
    art_norm = norm_ws(artifact_text)
    valid, rejected = [], []
    seen = set()
    for f in raw:
        if not isinstance(f, dict):
            rejected.append({"reason": "not-object", "item": str(f)[:120]})
            continue
        cat = str(f.get("category") or "")
        if cat not in CATEGORIES:
            rejected.append({"reason": f"bad-category:{cat}", "item": json.dumps(f, ensure_ascii=False)[:200]})
            continue
        sev = str(f.get("severity") or "")
        if sev not in SEVERITIES:
            sev = "minor"
        excerpt = norm_ws(str(f.get("excerpt") or ""))
        if not excerpt or excerpt not in art_norm:
            rejected.append({"reason": "excerpt-not-found", "category": cat, "excerpt": excerpt[:160]})
            continue
        key = (cat, excerpt)
        if key in seen:
            rejected.append({"reason": "duplicate", "category": cat, "excerpt": excerpt[:80]})
            continue
        seen.add(key)
        valid.append({
            "category": cat,
            "severity": sev,
            "excerpt": excerpt,
            "rationale": str(f.get("rationale") or "")[:160],
        })
    return valid, rejected


def summarize(findings: list) -> dict:
    by_cat = {c: 0 for c in CATEGORIES}
    major = minor = 0
    for f in findings:
        by_cat[f["category"]] += 1
        if f["severity"] == "major":
            major += 1
        else:
            minor += 1
    return {
        "findings_total": len(findings),
        "findings_major": major,
        "findings_minor": minor,
        "by_category": by_cat,
    }


def derive_accept(c1: int, c2: int, c3: int, c4: int, s: int, block: bool) -> str:
    if block:
        return "bloqueado"
    if s <= 4 or 0 in (c1, c2, c3, c4):
        return "rejeitado_retrabalho_maior"
    if s in (5, 6):
        return "aceito_retrabalho_menor"
    return "aceito"


def score_artifact(artifact: str, label: str) -> dict:
    base = (os.environ.get("KIMI_BASE_URL") or "https://api.kimi.com/coding/v1").rstrip("/")
    key = os.environ["KIMI_API_KEY"]
    user = (
        f"Artefato {label}.\n\n"
        f"ARTEFATO:\n```markdown\n{artifact}\n```\n\n"
        "Return ONLY the JSON object. No prose."
    )
    payload = {
        "model": "kimi-k2.7",
        "messages": [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": user},
        ],
        "max_tokens": 4000,
        "temperature": 1,  # required by Kimi coding API
    }
    t0 = time.time()
    body = post_chat(base + "/chat/completions", key, payload)
    wall = round(time.time() - t0, 2)
    content = message_text(body)
    obj = extract_json(content)

    def ci(name: str) -> int:
        v = int(obj.get(name) or 0)
        return max(0, min(2, v))

    c1, c2, c3, c4 = ci("C1_executability"), ci("C2_fidelity_coverage"), ci("C3_structure_scan"), ci("C4_ambiguity")
    s = c1 + c2 + c3 + c4
    block = bool(obj.get("critical_block"))
    clarity = int(obj.get("clarity_1to5") or 0)
    clarity = max(1, min(5, clarity))
    claimed_class = str(obj.get("accept_class") or "")
    derived_class = derive_accept(c1, c2, c3, c4, s, block)

    raw = obj.get("findings")
    if not isinstance(raw, list):
        raw = []
    valid, rejected = validate_findings(raw, artifact)
    return {
        "reviewer": "kimi",
        "model_requested": "kimi-k2.7",
        "model_returned": body.get("model") or "",
        "wall_s": wall,
        "usage": usage_of(body),
        "finish_reason": ((body.get("choices") or [{}])[0].get("finish_reason")),
        "C1_executability": c1,
        "C2_fidelity_coverage": c2,
        "C3_structure_scan": c3,
        "C4_ambiguity": c4,
        "S": s,
        "critical_block": block,
        "accept_class": derived_class,
        "accept_class_claimed": claimed_class if claimed_class in ALLOWED_CLASS else None,
        "clarity_1to5": clarity,
        "justification": str(obj.get("justification") or "")[:240],
        "findings": valid,
        "invalid_rejected": rejected,
        "summary": summarize(valid),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--blind-dir", type=Path, default=Path("artifacts/hermes-case-study/matrix-y4-smoke/blind-clarity"))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()
    load_env()

    key = json.loads((args.blind_dir / "KEY-DO-NOT-SHARE-until-scores.json").read_text(encoding="utf-8"))
    items = key["items"]
    if args.limit:
        items = items[: args.limit]

    out_path = args.blind_dir / "kimi-c1c4-scores.json"
    prev: dict[str, dict] = {}
    if args.resume and out_path.is_file():
        old = json.loads(out_path.read_text(encoding="utf-8"))
        prev = {e["label"]: e for e in old.get("scores") or []}

    totals = {"calls": 0, "ok": 0, "retries": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    scores = []
    for it in items:
        label = it["label"]
        prev_e = prev.get(label) or {}
        keep = (
            "S" in prev_e
            and "error" not in prev_e
            and prev_e.get("finish_reason") != "length"
            and str(prev_e.get("justification") or "").strip() != ""
        )
        if keep:
            e = prev_e
            scores.append(e)
            u = e.get("usage") or {}
            totals["calls"] += 1
            totals["ok"] += 1
            for k in ("input_tokens", "output_tokens", "total_tokens"):
                totals[k] += int(u.get(k) or 0)
            print(f"{label}: KEPT S={e['S']} class={e['accept_class']}", flush=True)
            continue
        text = (args.blind_dir / f"{label}.md").read_text(encoding="utf-8")
        entry = {"label": label, "case_id": it["case_id"]}
        last_err = None
        for attempt in (1, 2, 3):
            try:
                res = score_artifact(text, label)
                entry.update(res)
                entry["attempts"] = attempt
                u = res["usage"]
                totals["calls"] += 1
                totals["ok"] += 1
                totals["retries"] += attempt - 1
                for k in ("input_tokens", "output_tokens", "total_tokens"):
                    totals[k] += u[k]
                print(
                    f"{label}: C={res['C1_executability']}{res['C2_fidelity_coverage']}"
                    f"{res['C3_structure_scan']}{res['C4_ambiguity']} S={res['S']} "
                    f"class={res['accept_class']} clarity={res['clarity_1to5']} "
                    f"findings={res['summary']['findings_total']} "
                    f"tok={u['total_tokens']} wall={res['wall_s']}s att={attempt}",
                    flush=True,
                )
                last_err = None
                break
            except Exception as e:
                last_err = e
                print(f"{label}: attempt {attempt} ERROR {e}", flush=True)
        if last_err is not None:
            entry["error"] = str(last_err)[:400]
            entry["attempts"] = 3
        scores.append(entry)
        out_path.write_text(json.dumps({
            "schema_version": "matrix-y4-kimi-c1c4/v1",
            "run_id": key.get("run_id"),
            "scored_at": datetime.now(BRT).isoformat(),
            "panel_usage_totals": totals,
            "scores": scores,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # final write: full state after the loop (checkpoint writes inside the loop
    # can leave kept entries that follow the last execution out of the file)
    out_path.write_text(json.dumps({
        "schema_version": "matrix-y4-kimi-c1c4/v1",
        "run_id": key.get("run_id"),
        "scored_at": datetime.now(BRT).isoformat(),
        "panel_usage_totals": totals,
        "scores": scores,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("WROTE", out_path)
    print("PANEL_TOKENS", json.dumps(totals, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
