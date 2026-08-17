#!/usr/bin/env python3
"""Blind panel with Athena models: qwen/qwen3.8-27b (OpenRouter cloud) + qwen3.8-max (Bailian).

Always logs reviewer tokens. Cloud only for OSS small model.
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
Avalie SOMENTE o artefato.

Escala clareza 1-5: 1 incompreensível; 2 ambíguo crítico; 3 usável com esforço; 4 claro p/ operador experiente; 5 claro e direto.
Classes: aceito | aceito_retrabalho_menor | rejeitado_retrabalho_maior | bloqueado
Erro crítico = fato perigoso/errado ou requisito obrigatório faltante.

Responda APENAS JSON:
{"clarity_1to5":4,"accept_class":"aceito","critical_errors":0,"notes":"até 240 chars","preferred_if_pair":null}
"""


def load_keys() -> dict:
    env = {}
    paths = [
        Path.home() / ".hermes/profiles/athena/.env",
        Path.home() / ".hermes/.env",
        Path.home() / ".config/hermes/maritaca.env",
    ]
    for p in paths:
        if not p.is_file():
            continue
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line or line.lstrip().startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[7:]
            k, _, v = line.partition("=")
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k and v and k not in env:
                env[k] = v
    return env


def post_chat(url: str, api_key: str, payload: dict, timeout: int = 180) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "HTTP-Referer": "https://hermes.local/curupira-study",
            "X-Title": "curupira-blind-panel-athena",
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
    # tolerate truncated JSON-ish endings from small models
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        candidate = m.group(0)
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            # try close truncated string/object
            fixed = candidate
            if fixed.count('"') % 2 == 1:
                fixed += '"'
            if fixed.count("{") > fixed.count("}"):
                fixed += "}" * (fixed.count("{") - fixed.count("}"))
            try:
                obj = json.loads(fixed)
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                pass
    # last resort: find first {clarity_1to5... pattern pieces
    clarity = re.search(r'"clarity_1to5"\s*:\s*(\d+)', text)
    cls = re.search(r'"accept_class"\s*:\s*"([^"]+)"', text)
    crit = re.search(r'"critical_errors"\s*:\s*(\d+)', text)
    notes = re.search(r'"notes"\s*:\s*"([^"]*)', text)
    if clarity and cls:
        return {
            "clarity_1to5": int(clarity.group(1)),
            "accept_class": cls.group(1),
            "critical_errors": int(crit.group(1)) if crit else 0,
            "notes": (notes.group(1) if notes else "")[:240],
        }
    raise ValueError(f"no json: {text[:180]}")


def normalize_score(obj: dict) -> dict:
    clarity = max(1, min(5, int(obj.get("clarity_1to5") or 0)))
    cls = str(obj.get("accept_class") or "rejeitado_retrabalho_maior")
    allowed = {
        "aceito",
        "aceito_retrabalho_menor",
        "rejeitado_retrabalho_maior",
        "bloqueado",
    }
    if cls not in allowed:
        cls = "rejeitado_retrabalho_maior"
    return {
        "clarity_1to5": clarity,
        "accept_class": cls,
        "critical_errors": int(obj.get("critical_errors") or 0),
        "notes": str(obj.get("notes") or "")[:240],
    }


def usage_of(body: dict) -> dict:
    u = body.get("usage") or {}
    tin = u.get("prompt_tokens", u.get("input_tokens"))
    tout = u.get("completion_tokens", u.get("output_tokens"))
    tot = u.get("total_tokens")
    details = u.get("completion_tokens_details") or {}
    return {
        "input_tokens": int(tin or 0),
        "output_tokens": int(tout or 0),
        "total_tokens": int(tot or ((tin or 0) + (tout or 0))),
        "reasoning_tokens": int(details.get("reasoning_tokens") or u.get("reasoning_tokens") or 0),
        "cost_usd": u.get("cost"),
    }


def message_text(body: dict) -> str:
    msg = ((body.get("choices") or [{}])[0].get("message") or {})
    content = (msg.get("content") or "").strip()
    if content:
        return content
    return (msg.get("reasoning") or msg.get("reasoning_content") or "").strip()


def call_openrouter_qwen27(env: dict, artifact: str, case_id: str, label: str) -> dict:
    key = env["OPENROUTER_API_KEY"]
    model = "qwen/qwen3.8-27b"
    # Single user message reduces empty-content reasoning traps on small Qwen.
    user = (
        RUBRIC
        + f"\n\nCaso {case_id} artefato {label}.\n\nARTEFATO:\n```markdown\n{artifact}\n```\n\n"
        + "Output ONLY one JSON object. No markdown fence."
    )
    t0 = time.time()
    body = post_chat(
        "https://openrouter.ai/api/v1/chat/completions",
        key,
        {
            "model": model,
            "messages": [
                {"role": "user", "content": user},
            ],
            "max_tokens": 1200,
            "temperature": 0.1,
        },
        timeout=180,
    )
    wall = round(time.time() - t0, 2)
    content = message_text(body)
    usage = usage_of(body)
    try:
        score = normalize_score(extract_json(content))
    except Exception as e:
        raise RuntimeError(f"{e} | usage={usage} | raw={content[:120]}") from e
    return {
        "provider": "openrouter",
        "model_requested": model,
        "model_returned": body.get("model") or model,
        "wall_s": wall,
        "usage": usage,
        "score": score,
        "raw_text": content[:1500],
        "route": "cloud",
    }


def call_bailian_qwen_max(env: dict, artifact: str, case_id: str, label: str) -> dict:
    key = env["BAILIAN_TOKEN_PLAN_API_KEY"]
    model = "qwen3.8-max"
    url = "https://token-plan.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1/chat/completions"
    user = f"Caso {case_id} artefato {label}.\n\nARTEFATO:\n```markdown\n{artifact}\n```\n\nJSON only."
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
            "max_tokens": 800,
            "temperature": 0.2,
        },
        timeout=180,
    )
    wall = round(time.time() - t0, 2)
    content = message_text(body)
    score = normalize_score(extract_json(content))
    return {
        "provider": "bailian",
        "model_requested": model,
        "model_returned": body.get("model") or model,
        "wall_s": wall,
        "usage": usage_of(body),
        "score": score,
        "raw_text": content[:1500],
        "route": "cloud",
    }


def pref_for(cases: list, reviewer: str) -> list:
    out = []
    order = {
        "aceito": 0,
        "aceito_retrabalho_menor": 1,
        "rejeitado_retrabalho_maior": 2,
        "bloqueado": 3,
    }
    for row in cases:
        m = row["label_to_condition"]
        scores = {}
        rt = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        ok = True
        for lab in ["A", "B"]:
            rev = row["labels"][lab]["reviews"].get(reviewer) or {}
            if "score" not in rev:
                ok = False
            else:
                scores[lab] = rev["score"]
            u = rev.get("usage") or {}
            rt["input_tokens"] += int(u.get("input_tokens") or 0)
            rt["output_tokens"] += int(u.get("output_tokens") or 0)
            rt["total_tokens"] += int(u.get("total_tokens") or 0)
        if not ok:
            out.append(
                {
                    "case_id": row["case_id"],
                    "preferred_condition": "n/a",
                    "reviewer": reviewer,
                    "reviewer_tokens": rt,
                    "ab_session_tokens": row.get("ab_session_tokens"),
                }
            )
            continue

        def rank(lab: str):
            s = scores[lab]
            return (
                order.get(s["accept_class"], 9),
                -int(s["clarity_1to5"]),
                int(s["critical_errors"]),
            )

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
                "notes_control": scores["A" if m["A"] == "control" else "B"].get("notes"),
                "notes_cli": scores["A" if m["A"] == "cli" else "B"].get("notes"),
                "reviewer_tokens": rt,
                "ab_session_tokens": row.get("ab_session_tokens"),
            }
        )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--blind-dir", type=Path, default=Path("artifacts/hermes-case-study/v2/blind"))
    ap.add_argument(
        "--battery-summary",
        type=Path,
        default=Path("artifacts/hermes-case-study/v2/battery-run-v2-01-summary.json"),
    )
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("artifacts/hermes-case-study/v2/blind/scores-panel-athena-qwen.json"),
    )
    args = ap.parse_args()
    env = load_keys()
    for req in ["OPENROUTER_API_KEY", "BAILIAN_TOKEN_PLAN_API_KEY"]:
        if req not in env:
            raise SystemExit(f"missing {req}")

    key = json.loads((args.blind_dir / "KEY-DO-NOT-SHARE-until-scores.json").read_text())
    items = key["items"]
    if args.limit:
        items = items[: args.limit]

    battery = {}
    if args.battery_summary.is_file():
        b = json.loads(args.battery_summary.read_text())
        battery = {p["case_id"]: p for p in b.get("pairs") or []}

    totals = {
        "qwen3.8-27b": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "calls": 0, "errors": 0},
        "qwen3.8-max": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "calls": 0, "errors": 0},
    }
    results = []
    callers = {
        "qwen3.8-27b": call_openrouter_qwen27,
        "qwen3.8-max": call_bailian_qwen_max,
    }

    for it in items:
        case = it["case_id"]
        mapping = it["label_to_condition"]
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
                "token_source": "sessiondb",
                "integrity_note": "v2 battery sessiondb; may be anomalous on some cases",
            }
        for lab in ["A", "B"]:
            text = (args.blind_dir / f"{case}-{lab}.md").read_text(encoding="utf-8")
            lab_out = {"label": lab, "condition": mapping[lab], "reviews": {}}
            for name, fn in callers.items():
                try:
                    rev = fn(env, text, case, lab)
                    lab_out["reviews"][name] = rev
                    u = rev["usage"]
                    totals[name]["input_tokens"] += u["input_tokens"]
                    totals[name]["output_tokens"] += u["output_tokens"]
                    totals[name]["total_tokens"] += u["total_tokens"]
                    totals[name]["calls"] += 1
                    print(
                        f"{case} {lab} {name}: {rev['score']['clarity_1to5']}/{rev['score']['accept_class']} "
                        f"tok={u['input_tokens']}/{u['output_tokens']}/{u['total_tokens']}",
                        flush=True,
                    )
                except Exception as e:
                    lab_out["reviews"][name] = {"error": str(e)[:400]}
                    totals[name]["errors"] += 1
                    print(f"{case} {lab} {name}: ERROR {e}", flush=True)
                    time.sleep(1)
            case_row["labels"][lab] = lab_out
        results.append(case_row)

    payload = {
        "schema_version": "blind-panel-athena-qwen/v1",
        "run_id": key.get("run_id") or "run-v2-01",
        "scored_at": datetime.now(BRT).isoformat(),
        "models": {
            "qwen3.8-27b": "qwen/qwen3.8-27b@openrouter-cloud",
            "qwen3.8-max": "qwen3.8-max@bailian-cloud",
        },
        "token_policy": "Always include reviewer call tokens and A/B session tokens side-by-side.",
        "cloud_only_oss": True,
        "panel_usage_totals": totals,
        "cases": results,
        "unblind_preferences": {
            "qwen3.8-27b": pref_for(results, "qwen3.8-27b"),
            "qwen3.8-max": pref_for(results, "qwen3.8-max"),
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("WROTE", args.out)
    print("PANEL_TOKENS", json.dumps(totals, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
