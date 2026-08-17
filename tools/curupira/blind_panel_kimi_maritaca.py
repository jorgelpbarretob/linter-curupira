#!/usr/bin/env python3
"""Blind panel review with Kimi 2.7 + Maritaca, always logging tokens.

Usage:
  python3 tools/curupira/blind_panel_kimi_maritaca.py \
    --blind-dir artifacts/hermes-case-study/v2/blind \
    --battery-summary artifacts/hermes-case-study/v2/battery-run-v2-01-summary.json
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

RUBRIC = """Você é revisor cego de documentação técnica pt-BR.
NÃO tente adivinhar qual sistema gerou o texto.
Avalie SOMENTE o artefato fornecido.

Escala de clareza 1-5:
1 incompreensível; 2 ambíguo crítico; 3 usável com esforço; 4 claro p/ operador experiente; 5 claro e direto.

Classes de aceite:
- aceito
- aceito_retrabalho_menor
- rejeitado_retrabalho_maior
- bloqueado

Erro crítico = fato técnico perigoso/errado ou requisito obrigatório faltante grave.

Responda APENAS JSON válido:
{
  "clarity_1to5": 1,
  "accept_class": "aceito",
  "critical_errors": 0,
  "notes": "até 240 chars"
}
"""


def load_env() -> None:
    def put(k: str, v: str) -> None:
        v = v.strip().strip('"').strip("'")
        if k and v:
            os.environ[k] = v

    env_path = Path.home() / ".hermes" / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line or line.lstrip().startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[len("export ") :]
            k, _, v = line.partition("=")
            k = k.strip()
            if k in {"KIMI_API_KEY", "KIMI_BASE_URL"}:
                put(k, v)
    mpath = Path.home() / ".config/hermes/maritaca.env"
    if mpath.is_file():
        for line in mpath.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line or line.lstrip().startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[len("export ") :]
            k, _, v = line.partition("=")
            k = k.strip()
            if k.startswith("MARITACA"):
                put(k, v)


def post_chat(url: str, api_key: str, payload: dict, timeout: int = 180) -> dict:
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
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError(f"no json in model output: {text[:200]}")
    obj = json.loads(m.group(0))
    if not isinstance(obj, dict):
        raise ValueError("json root not object")
    return obj


def normalize_score(obj: dict) -> dict:
    clarity = int(obj.get("clarity_1to5") or 0)
    clarity = max(1, min(5, clarity))
    cls = str(obj.get("accept_class") or "rejeitado_retrabalho_maior")
    allowed = {
        "aceito",
        "aceito_retrabalho_menor",
        "rejeitado_retrabalho_maior",
        "bloqueado",
    }
    if cls not in allowed:
        cls = "rejeitado_retrabalho_maior"
    crit = int(obj.get("critical_errors") or 0)
    notes = str(obj.get("notes") or "")[:240]
    return {
        "clarity_1to5": clarity,
        "accept_class": cls,
        "critical_errors": crit,
        "notes": notes,
    }


def usage_from_openai_shape(body: dict) -> dict:
    u = body.get("usage") or {}
    # OpenAI-like
    tin = u.get("prompt_tokens")
    tout = u.get("completion_tokens")
    tot = u.get("total_tokens")
    if tin is None and "input_tokens" in u:
        tin = u.get("input_tokens")
        tout = u.get("output_tokens")
        tot = u.get("total_tokens")
    return {
        "input_tokens": int(tin or 0),
        "output_tokens": int(tout or 0),
        "total_tokens": int(tot or ((tin or 0) + (tout or 0))),
        "raw_keys": sorted(u.keys()),
    }


def message_text(body: dict) -> str:
    msg = ((body.get("choices") or [{}])[0].get("message") or {})
    content = (msg.get("content") or "").strip()
    if content:
        return content
    reasoning = (msg.get("reasoning_content") or "").strip()
    return reasoning


def call_kimi(artifact: str, case_id: str, label: str) -> dict:
    base = (os.environ.get("KIMI_BASE_URL") or "https://api.kimi.com/coding/v1").rstrip("/")
    key = os.environ["KIMI_API_KEY"]
    model = "kimi-k2.7"
    user = (
        f"Caso {case_id} artefato {label}.\n\n"
        f"ARTEFATO:\n```markdown\n{artifact}\n```\n\n"
        "Return ONLY the JSON object. No prose."
    )
    t0 = time.time()
    body = post_chat(
        base + "/chat/completions",
        key,
        {
            "model": model,
            "messages": [
                {"role": "system", "content": RUBRIC},
                {"role": "user", "content": user},
            ],
            "max_tokens": 1200,
            "temperature": 1,  # required by Kimi coding API
        },
    )
    wall = round(time.time() - t0, 2)
    content = message_text(body)
    score = normalize_score(extract_json(content))
    return {
        "provider": "kimi",
        "model_requested": model,
        "model_returned": body.get("model") or model,
        "wall_s": wall,
        "usage": usage_from_openai_shape(body),
        "score": score,
        "raw_text": content[:2000],
        "finish_reason": ((body.get("choices") or [{}])[0].get("finish_reason")),
    }


def call_maritaca(artifact: str, case_id: str, label: str) -> dict:
    key = os.environ["MARITACA_API_KEY"].strip().strip('"').strip("'")
    # panel model for rigorous review
    model = "sabia-4-thinking"
    url = "https://chat.maritaca.ai/api/chat/completions"
    user = (
        f"Caso {case_id} artefato {label}.\n\n"
        f"ARTEFATO:\n```markdown\n{artifact}\n```\n\n"
        "Return ONLY the JSON object. No prose."
    )
    t0 = time.time()
    body = post_chat(
        url,
        key,
        {
            "model": model,
            "messages": [
                {"role": "system", "content": RUBRIC},
                {"role": "user", "content": user},
            ],
            "max_tokens": 1200,
            "temperature": 0,
        },
        timeout=240,
    )
    wall = round(time.time() - t0, 2)
    content = message_text(body)
    score = normalize_score(extract_json(content))
    return {
        "provider": "maritaca",
        "model_requested": model,
        "model_returned": body.get("model") or model,
        "wall_s": wall,
        "usage": usage_from_openai_shape(body),
        "score": score,
        "raw_text": content[:2500],
        "finish_reason": ((body.get("choices") or [{}])[0].get("finish_reason")),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--blind-dir",
        type=Path,
        default=Path("artifacts/hermes-case-study/v2/blind"),
    )
    ap.add_argument(
        "--battery-summary",
        type=Path,
        default=Path("artifacts/hermes-case-study/v2/battery-run-v2-01-summary.json"),
    )
    ap.add_argument("--limit", type=int, default=0, help="0=all cases")
    args = ap.parse_args()
    load_env()

    key = json.loads((args.blind_dir / "KEY-DO-NOT-SHARE-until-scores.json").read_text())
    items = key["items"]
    if args.limit:
        items = items[: args.limit]

    battery = {}
    if args.battery_summary.is_file():
        b = json.loads(args.battery_summary.read_text())
        battery = {p["case_id"]: p for p in b.get("pairs") or []}

    results = []
    totals = {
        "kimi": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "calls": 0},
        "maritaca": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "calls": 0},
    }

    for it in items:
        case = it["case_id"]
        mapping = it["label_to_condition"]  # A/B -> control/cli
        case_row = {
            "case_id": case,
            "label_to_condition": mapping,
            "labels": {},
            "ab_session_tokens": None,
        }
        if case in battery:
            bp = battery[case]
            case_row["ab_session_tokens"] = {
                "control": {
                    "input_tokens": bp.get("input_control"),
                    "output_tokens": bp.get("output_control"),
                    "total_tokens": bp.get("tokens_control"),
                },
                "cli": {
                    "input_tokens": bp.get("input_cli"),
                    "output_tokens": bp.get("output_cli"),
                    "total_tokens": bp.get("tokens_cli"),
                },
                "delta_cli_minus_control": {
                    "input_tokens": bp.get("delta_input"),
                    "output_tokens": bp.get("delta_output"),
                    "total_tokens": bp.get("delta_tokens"),
                },
            }

        for lab in ["A", "B"]:
            path = args.blind_dir / f"{case}-{lab}.md"
            text = path.read_text(encoding="utf-8")
            lab_out = {"label": lab, "condition": mapping[lab], "reviews": {}}
            for name, fn in [("kimi", call_kimi), ("maritaca", call_maritaca)]:
                try:
                    rev = fn(text, case, lab)
                    lab_out["reviews"][name] = rev
                    u = rev["usage"]
                    totals[name]["input_tokens"] += u["input_tokens"]
                    totals[name]["output_tokens"] += u["output_tokens"]
                    totals[name]["total_tokens"] += u["total_tokens"]
                    totals[name]["calls"] += 1
                    print(
                        f"{case} {lab} {name}: clarity={rev['score']['clarity_1to5']} "
                        f"class={rev['score']['accept_class']} "
                        f"tok={u['input_tokens']}/{u['output_tokens']}/{u['total_tokens']}",
                        flush=True,
                    )
                except Exception as e:
                    lab_out["reviews"][name] = {"error": str(e)[:400]}
                    print(f"{case} {lab} {name}: ERROR {e}", flush=True)
            case_row["labels"][lab] = lab_out
        results.append(case_row)

    # unblind preference per reviewer
    def pref_for(reviewer: str) -> list[dict]:
        out = []
        for row in results:
            m = row["label_to_condition"]
            scores = {}
            for lab in ["A", "B"]:
                rev = row["labels"][lab]["reviews"].get(reviewer) or {}
                if "score" not in rev:
                    scores[lab] = None
                    continue
                scores[lab] = rev["score"]
            if not scores["A"] or not scores["B"]:
                out.append({"case_id": row["case_id"], "preferred": "n/a", "reviewer": reviewer})
                continue
            order = {
                "aceito": 0,
                "aceito_retrabalho_menor": 1,
                "rejeitado_retrabalho_maior": 2,
                "bloqueado": 3,
            }

            def rank(lab: str):
                s = scores[lab]
                return (order.get(s["accept_class"], 9), -int(s["clarity_1to5"]), int(s["critical_errors"]))

            if rank("A") < rank("B"):
                pref_lab = "A"
            elif rank("B") < rank("A"):
                pref_lab = "B"
            else:
                pref_lab = "tie"
            pref_cond = "tie" if pref_lab == "tie" else m[pref_lab]
            out.append(
                {
                    "case_id": row["case_id"],
                    "reviewer": reviewer,
                    "preferred_label": pref_lab,
                    "preferred_condition": pref_cond,
                    "clarity_control": scores["A" if m["A"] == "control" else "B"]["clarity_1to5"],
                    "clarity_cli": scores["A" if m["A"] == "cli" else "B"]["clarity_1to5"],
                    "class_control": scores["A" if m["A"] == "control" else "B"]["accept_class"],
                    "class_cli": scores["A" if m["A"] == "cli" else "B"]["accept_class"],
                    "ab_session_tokens": row.get("ab_session_tokens"),
                }
            )
        return out

    payload = {
        "schema_version": "blind-panel-kimi-maritaca/v1",
        "run_id": key.get("run_id") or "run-v2-01",
        "scored_at": datetime.now(BRT).isoformat(),
        "models": {
            "kimi": "kimi-k2.7",
            "maritaca": "sabia-4-thinking",
        },
        "token_policy": "Always include reviewer call tokens and A/B session tokens side-by-side.",
        "panel_usage_totals": totals,
        "cases": results,
        "unblind_preferences": {
            "kimi": pref_for("kimi"),
            "maritaca": pref_for("maritaca"),
        },
    }

    out = args.blind_dir / "scores-panel-kimi-maritaca.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("WROTE", out)
    print("PANEL_TOKENS", json.dumps(totals, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
