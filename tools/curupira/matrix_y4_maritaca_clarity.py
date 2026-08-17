#!/usr/bin/env python3
"""Matrix Y4 semantic layer: blind Maritaca clarity + semantic findings.

Scores all artifacts of the locked Y matrix (control x cli, 3 smoke cases)
with sabia-4-thinking. One call per artifact returns clarity 1-5, accept
class, critical errors AND countable semantic findings (4 categories).

Artifacts are blinded first; the KEY file is written for later unblind.
Reviewer tokens are always logged (5D policy).

Usage:
  python3 tools/curupira/matrix_y4_maritaca_clarity.py [--limit 0] [--resume]
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

PROMPT = """\
Você é revisor cego de documentação técnica pt-BR. NÃO tente adivinhar qual \
sistema ou modelo gerou o texto. Avalie SOMENTE o artefato fornecido.

Parte 1 — clareza e aceite.
Escala de clareza 1-5:
1 incompreensível; 2 ambíguo crítico; 3 usável com esforço; \
4 claro p/ operador experiente; 5 claro e direto.
Classes de aceite: aceito | aceito_retrabalho_menor | \
rejeitado_retrabalho_maior | bloqueado.
Erro crítico = fato técnico perigoso/errado ou requisito obrigatório faltante grave.

Parte 2 — achados semânticos. Conte ocorrências de 4 categorias; \
cada ocorrência distinta conta uma vez.
1. ambiguous-reference: pronome ou referência com mais de um antecedente possível.
2. implicit-agent: ação imperativa sem agente definido quando o agente importa.
3. multiple-actions: sentença ou passo único que empilha 2 ou mais ações obrigatórias.
4. terminology: jargão técnico sem qualificador necessário para executar.

Regras:
- Para cada achado, cite "excerpt": trecho LITERAL copiado do artefato.
- severity: "major" se pode causar erro operacional; "minor" se só incômodo de leitura.
- Zero achados é válido. Preferência de estilo NÃO conta achado.
- Não conte o que o próprio texto resolve no contexto. Não invente trechos.

Responda começando com { e terminando com }. Nenhuma palavra fora do JSON.
Sem raciocínio, sem plano, sem texto antes ou depois.

Responda APENAS JSON válido:
{
  "clarity_1to5": 1,
  "accept_class": "aceito",
  "critical_errors": 0,
  "notes": "até 240 chars",
  "findings": [
    {"category": "ambiguous-reference", "severity": "minor",
     "excerpt": "trecho literal", "rationale": "até 120 chars"}
  ],
  "findings_total": 0
}
"""


def load_env() -> None:
    mpath = Path.home() / ".config/hermes/maritaca.env"
    if mpath.is_file():
        for line in mpath.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line or line.lstrip().startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[len("export "):]
            k, _, v = line.partition("=")
            k = k.strip()
            if k.startswith("MARITACA"):
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


def score_artifact(artifact: str, label: str) -> dict:
    key = os.environ["MARITACA_API_KEY"].strip().strip('"').strip("'")
    user = (
        f"Artefato {label}.\n\n"
        f"ARTEFATO:\n```markdown\n{artifact}\n```\n\n"
        "Responda APENAS o objeto JSON. Sem raciocínio, sem texto antes ou depois."
    )
    payload = {
        "model": "sabia-4-thinking",
        "messages": [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": user},
        ],
        "max_tokens": 1600,
        "temperature": 0,
    }
    t0 = time.time()
    body = post_chat("https://chat.maritaca.ai/api/chat/completions", key, payload)
    wall = round(time.time() - t0, 2)
    content = message_text(body)
    obj = extract_json(content)

    clarity = int(obj.get("clarity_1to5") or 0)
    clarity = max(1, min(5, clarity))
    cls = str(obj.get("accept_class") or "rejeitado_retrabalho_maior")
    allowed = {"aceito", "aceito_retrabalho_menor", "rejeitado_retrabalho_maior", "bloqueado"}
    if cls not in allowed:
        cls = "rejeitado_retrabalho_maior"
    crit = int(obj.get("critical_errors") or 0)
    notes = str(obj.get("notes") or "")[:240]

    raw = obj.get("findings")
    if not isinstance(raw, list):
        raw = []
    valid, rejected = validate_findings(raw, artifact)
    return {
        "reviewer": "maritaca",
        "model_requested": "sabia-4-thinking",
        "model_returned": body.get("model") or "",
        "wall_s": wall,
        "usage": usage_of(body),
        "finish_reason": ((body.get("choices") or [{}])[0].get("finish_reason")),
        "clarity_1to5": clarity,
        "accept_class": cls,
        "critical_errors": crit,
        "notes": notes,
        "findings": valid,
        "invalid_rejected": rejected,
        "summary": summarize(valid),
        "claimed_total": int(obj.get("findings_total") or -1),
    }


def collect_items(smoke_dir: Path, lock_path: Path) -> list[dict]:
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    models = [y["model"] for y in lock["Y"]]
    items = []
    for model in models:
        slug = model.replace("/", "_").replace(":", "_")
        mdir = smoke_dir / slug
        if not mdir.is_dir():
            continue
        for cond in ["control", "cli"]:
            cdir = mdir / cond
            if not cdir.is_dir():
                continue
            for run in sorted(cdir.iterdir()):
                arts = sorted(run.glob("*.md"))
                if not arts:
                    continue
                items.append({
                    "model": model,
                    "condition": cond,
                    "case_id": run.parent.parent.name,  # placeholder; fixed below
                    "run_dir": str(run),
                    "artifact_path": str(arts[0]),
                })
    # fix case_id from run dir name (case-XXX-run-01)
    for it in items:
        name = Path(it["run_dir"]).name
        m = re.match(r"(case-\d+)", name)
        it["case_id"] = m.group(1) if m else name
    return items


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke-dir", type=Path, default=Path("artifacts/hermes-case-study/matrix-y4-smoke"))
    ap.add_argument("--lock", type=Path, default=Path("artifacts/hermes-case-study/matrix-y4-lock.json"))
    ap.add_argument("--blind-dir", type=Path, default=Path("artifacts/hermes-case-study/matrix-y4-smoke/blind-clarity"))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()
    load_env()

    items = collect_items(args.smoke_dir, args.lock)
    if args.limit:
        items = items[: args.limit]

    # blind labels: deterministic order -> M01..MNN
    args.blind_dir.mkdir(parents=True, exist_ok=True)
    key_path = args.blind_dir / "KEY-DO-NOT-SHARE-until-scores.json"
    if key_path.is_file():
        key = json.loads(key_path.read_text(encoding="utf-8"))
    else:
        key = {
            "schema_version": "matrix-y4-blind-key/v1",
            "run_id": "matrix-y4-clarity-run-01",
            "created_at": datetime.now(BRT).isoformat(),
            "items": [],
        }
        for i, it in enumerate(items, 1):
            label = f"M{i:02d}"
            text = Path(it["artifact_path"]).read_text(encoding="utf-8")
            (args.blind_dir / f"{label}.md").write_text(text, encoding="utf-8")
            key["items"].append({
                "label": label,
                "model": it["model"],
                "condition": it["condition"],
                "case_id": it["case_id"],
                "artifact_path": it["artifact_path"],
            })
        key_path.write_text(json.dumps(key, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("BLIND PACKAGE:", len(key["items"]), "artifacts ->", args.blind_dir)

    prev: dict[str, dict] = {}
    out_path = args.blind_dir / "maritaca-clarity-scores.json"
    if args.resume and out_path.is_file():
        old = json.loads(out_path.read_text(encoding="utf-8"))
        prev = {e["label"]: e for e in old.get("scores") or []}

    totals = {"calls": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    scores = []
    for it in key["items"]:
        label = it["label"]
        if label in prev and "clarity_1to5" in prev[label]:
            e = prev[label]
            scores.append(e)
            u = e.get("usage") or {}
            totals["calls"] += 1
            for k in ("input_tokens", "output_tokens", "total_tokens"):
                totals[k] += int(u.get(k) or 0)
            print(f"{label}: KEPT clarity={e['clarity_1to5']} findings={e['summary']['findings_total']}", flush=True)
            continue
        text = (args.blind_dir / f"{label}.md").read_text(encoding="utf-8")
        entry = {"label": label, "case_id": it["case_id"]}
        last_err = None
        for attempt in (1, 2):
            try:
                res = score_artifact(text, label)
                entry.update(res)
                u = res["usage"]
                totals["calls"] += 1
                for k in ("input_tokens", "output_tokens", "total_tokens"):
                    totals[k] += u[k]
                print(
                    f"{label}: clarity={res['clarity_1to5']} class={res['accept_class']} "
                    f"findings={res['summary']['findings_total']} invalid={len(res['invalid_rejected'])} "
                    f"tok={u['total_tokens']} wall={res['wall_s']}s",
                    flush=True,
                )
                last_err = None
                break
            except Exception as e:
                last_err = e
                print(f"{label}: attempt {attempt} ERROR {e}", flush=True)
        if last_err is not None:
            entry["error"] = str(last_err)[:400]
        scores.append(entry)
        # checkpoint after each artifact
        out_path.write_text(json.dumps({
            "schema_version": "matrix-y4-maritaca-clarity/v1",
            "run_id": key.get("run_id"),
            "scored_at": datetime.now(BRT).isoformat(),
            "panel_usage_totals": totals,
            "scores": scores,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # ---- unblind aggregation ----
    by_model: dict[str, dict[str, list[dict]]] = {}
    for it in key["items"]:
        entry = next((s for s in scores if s["label"] == it["label"]), None)
        if not entry or "clarity_1to5" not in entry:
            continue
        slot = by_model.setdefault(it["model"], {"control": [], "cli": []})
        slot[it["condition"]].append({
            "case_id": it["case_id"],
            "clarity": entry["clarity_1to5"],
            "accept_class": entry["accept_class"],
            "critical_errors": entry["critical_errors"],
            "findings_total": entry["summary"]["findings_total"],
            "findings_major": entry["summary"]["findings_major"],
            "by_category": entry["summary"]["by_category"],
            "usage": entry["usage"],
        })

    agg = {}
    for model, conds in sorted(by_model.items()):
        c_list, t_list = conds["control"], conds["cli"]
        prefs = []
        c_by = {x["case_id"]: x for x in c_list}
        t_by = {x["case_id"]: x for x in t_list}
        for cid in sorted(set(c_by) & set(t_by)):
            c, t = c_by[cid], t_by[cid]
            if c["clarity"] > t["clarity"]:
                pref = "control"
            elif t["clarity"] > c["clarity"]:
                pref = "cli"
            elif c["findings_total"] > t["findings_total"]:
                pref = "cli"
            elif t["findings_total"] > c["findings_total"]:
                pref = "control"
            else:
                pref = "tie"
            prefs.append({"case_id": cid, "preferred": pref,
                          "clarity_control": c["clarity"], "clarity_cli": t["clarity"],
                          "findings_control": c["findings_total"], "findings_cli": t["findings_total"]})
        pref_counts = {}
        for p in prefs:
            pref_counts[p["preferred"]] = pref_counts.get(p["preferred"], 0) + 1

        def mean(vals: list[float]) -> float | None:
            return round(sum(vals) / len(vals), 2) if vals else None

        agg[model] = {
            "n_pairs": len(prefs),
            "clarity_control_mean": mean([x["clarity"] for x in c_list]),
            "clarity_cli_mean": mean([x["clarity"] for x in t_list]),
            "findings_control_mean": mean([x["findings_total"] for x in c_list]),
            "findings_cli_mean": mean([x["findings_total"] for x in t_list]),
            "accept_control": [x["accept_class"] for x in c_list],
            "accept_cli": [x["accept_class"] for x in t_list],
            "preference_counts": pref_counts,
            "preferences": prefs,
        }

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    payload["scored_at"] = datetime.now(BRT).isoformat()
    payload["panel_usage_totals"] = totals
    payload["scores"] = scores
    payload["aggregate_by_model"] = agg
    payload["unblind"] = True
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("WROTE", out_path)
    print("PANEL_TOKENS", json.dumps(totals, ensure_ascii=False))
    for model, a in agg.items():
        print(f"{model}: clarity C={a['clarity_control_mean']} CLI={a['clarity_cli_mean']} | "
              f"findings C={a['findings_control_mean']} CLI={a['findings_cli_mean']} | pref={a['preference_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
