#!/usr/bin/env python3
"""Semantic rubric scoring (countable, blind) with Kimi + Maritaca.

Counts residual semantic findings per blind artifact on 4 fixed categories:
ambiguous-reference, implicit-agent, multiple-actions, terminology.

Scores stay blind until all artifacts are scored; then unblind via the
KEY file and aggregate per condition.

Usage:
  python3 tools/curupira/semantic_rubric.py [--limit 1] [--reviewers kimi,maritaca]
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

RUBRIC = """\
Você é revisor cego de documentação técnica pt-BR. NÃO tente adivinhar qual \
sistema gerou o texto. Avalie SOMENTE o artefato fornecido.

Conte ocorrências de 4 categorias. Cada ocorrência distinta conta uma vez.

1. ambiguous-reference: pronome ou referência com mais de um antecedente possível \
("o painel", "deste", "ele" sem antecedente único no contexto).
2. implicit-agent: ação imperativa sem agente definido quando o agente importa \
para executar ("desligar a bomba" sem dizer quem: operador, sistema, automático).
3. multiple-actions: sentença ou passo único que empilha 2 ou mais ações obrigatórias \
(risco de executar pela metade).
4. terminology: jargão técnico sem qualificador necessário para executar \
(válvula/registro/bomba/sensor/tolerância sem tipo, faixa ou fonte).

Regras:
- Para cada achado, cite "excerpt": trecho LITERAL copiado do artefato (sem alterar palavras).
- severity: "major" se pode causar erro operacional ou decisão errada; "minor" se só incômodo de leitura.
- Zero achados em uma categoria é válido. Preferência de estilo NÃO conta achado.
- Não conte o que o próprio texto resolve no contexto.
- Não invente trechos. Se não tem certeza do trecho, não reporte o achado.

Responda começando com { e terminando com }. Nenhuma palavra fora do JSON.
Sem raciocínio, sem plano, sem texto antes ou depois.

Responda APENAS JSON válido:
{
  "findings": [
    {"category": "ambiguous-reference", "severity": "minor",
     "excerpt": "trecho literal", "rationale": "até 120 chars"}
  ],
  "findings_total": 0
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
                line = line[len("export "):]
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
                line = line[len("export "):]
            k, _, v = line.partition("=")
            k = k.strip()
            if k.startswith("MARITACA"):
                put(k, v)


def post_chat(url: str, api_key: str, payload: dict, timeout: int = 240) -> dict:
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
    """Keep findings whose excerpt is verbatim in the artifact; dedupe."""
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


def call_reviewer(name: str, artifact: str, case_id: str, label: str) -> dict:
    user = (
        f"Caso {case_id} artefato {label}.\n\n"
        f"ARTEFATO:\n```markdown\n{artifact}\n```\n\n"
        "Responda APENAS o objeto JSON. Sem raciocínio, sem texto antes ou depois."
    )
    if name == "kimi":
        base = (os.environ.get("KIMI_BASE_URL") or "https://api.kimi.com/coding/v1").rstrip("/")
        payload = {
            "model": "kimi-k2.7",
            "messages": [{"role": "system", "content": RUBRIC}, {"role": "user", "content": user}],
            "max_tokens": 1500,
            "temperature": 1,  # required by Kimi coding API
        }
        body = post_chat(base + "/chat/completions", os.environ["KIMI_API_KEY"], payload)
    else:
        payload = {
            "model": "sabia-4-thinking",
            "messages": [{"role": "system", "content": RUBRIC}, {"role": "user", "content": user}],
            "max_tokens": 1500,
            "temperature": 0,
        }
        body = post_chat("https://chat.maritaca.ai/api/chat/completions", os.environ["MARITACA_API_KEY"], payload)
    content = message_text(body)
    obj = extract_json(content)
    raw = obj.get("findings")
    if not isinstance(raw, list):
        raw = []
    valid, rejected = validate_findings(raw, artifact)
    return {
        "provider": name,
        "model_returned": body.get("model") or "",
        "usage": usage_of(body),
        "finish_reason": ((body.get("choices") or [{}])[0].get("finish_reason")),
        "findings": valid,
        "invalid_rejected": rejected,
        "summary": summarize(valid),
        "claimed_total": int(obj.get("findings_total") or -1),
        "raw_text": content[:2500],
    }


def spearman(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3 or n != len(ys):
        return None

    def ranks(v: list[float]) -> list[float]:
        order = sorted(range(n), key=lambda i: v[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    dx = sum((r - mx) ** 2 for r in rx) ** 0.5
    dy = sum((r - my) ** 2 for r in ry) ** 0.5
    if dx == 0 or dy == 0:
        return None
    return round(num / (dx * dy), 3)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--blind-dir", type=Path, default=Path("artifacts/hermes-case-study/v2/blind"))
    ap.add_argument("--limit", type=int, default=0, help="0=all cases")
    ap.add_argument("--reviewers", default="kimi,maritaca")
    ap.add_argument(
        "--resume",
        action="store_true",
        help="load existing scores file and re-run only reviewer calls missing or in error",
    )
    args = ap.parse_args()
    load_env()
    reviewers = [r.strip() for r in args.reviewers.split(",") if r.strip() in {"kimi", "maritaca"}]
    if not reviewers:
        raise SystemExit("no valid reviewers")

    key = json.loads((args.blind_dir / "KEY-DO-NOT-SHARE-until-scores.json").read_text())
    items = key["items"]
    if args.limit:
        items = items[: args.limit]

    prev: dict[str, dict] = {}
    out_path = args.blind_dir / "semantic-rubric-scores.json"
    if args.resume and out_path.is_file():
        try:
            old = json.loads(out_path.read_text(encoding="utf-8"))
            for row in old.get("cases") or []:
                prev[row["case_id"]] = row
        except Exception:
            prev = {}

    totals = {r: {"calls": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0} for r in reviewers}
    cases = []
    for it in items:
        case = it["case_id"]
        mapping = it["label_to_condition"]
        prev_row = prev.get(case) or {}
        prev_labels = prev_row.get("labels") or {}
        row = {"case_id": case, "label_to_condition": mapping, "labels": {}}
        for lab in ["A", "B"]:
            path = args.blind_dir / f"{case}-{lab}.md"
            text = path.read_text(encoding="utf-8")
            prev_lab = prev_labels.get(lab) or {}
            prev_reviews = prev_lab.get("reviews") or {}
            lab_out = {"reviews": {}}
            for name in reviewers:
                prev_rev = prev_reviews.get(name) or {}
                if "summary" in prev_rev and "findings" in prev_rev:
                    lab_out["reviews"][name] = prev_rev
                    u = prev_rev.get("usage") or {}
                    totals[name]["calls"] += 1
                    for k in ("input_tokens", "output_tokens", "total_tokens"):
                        totals[name][k] += int(u.get(k) or 0)
                    print(f"{case} {lab} {name}: KEPT total={prev_rev['summary']['findings_total']}", flush=True)
                    continue
                last_err = None
                for attempt in (1, 2):
                    try:
                        rev = call_reviewer(name, text, case, lab)
                        lab_out["reviews"][name] = rev
                        u = rev["usage"]
                        totals[name]["calls"] += 1
                        for k in ("input_tokens", "output_tokens", "total_tokens"):
                            totals[name][k] += u[k]
                        s = rev["summary"]
                        print(
                            f"{case} {lab} {name}: total={s['findings_total']} "
                            f"major={s['findings_major']} invalid={len(rev['invalid_rejected'])} "
                            f"tok={u['total_tokens']}",
                            flush=True,
                        )
                        last_err = None
                        break
                    except Exception as e:
                        last_err = e
                        print(f"{case} {lab} {name}: attempt {attempt} ERROR {e}", flush=True)
                if last_err is not None:
                    lab_out["reviews"][name] = {"error": str(last_err)[:400]}
            row["labels"][lab] = lab_out
        cases.append(row)

    # ---- unblind aggregation (scores already saved above) ----
    per_condition = {r: {"control": [], "cli": []} for r in reviewers}
    prefs = {r: [] for r in reviewers}
    pair_totals = {r: {"x": [], "y": []} for r in reviewers}  # (control_total, cli_total) per artifact pair

    for row in cases:
        m = row["label_to_condition"]
        for r in reviewers:
            cond_scores = {}
            for lab in ["A", "B"]:
                rev = row["labels"][lab]["reviews"].get(r) or {}
                cond_scores[m[lab]] = rev.get("summary") if "summary" in rev else None
            c, t = cond_scores.get("control"), cond_scores.get("cli")
            if c and t:
                per_condition[r]["control"].append(c["findings_total"])
                per_condition[r]["cli"].append(t["findings_total"])
                pair_totals[r]["x"].append(float(c["findings_total"]))
                pair_totals[r]["y"].append(float(t["findings_total"]))
                if t["findings_total"] < c["findings_total"]:
                    pref = "cli"
                elif c["findings_total"] < t["findings_total"]:
                    pref = "control"
                else:
                    pref = "tie"
                prefs[r].append({
                    "case_id": row["case_id"],
                    "findings_control": c["findings_total"],
                    "findings_cli": t["findings_total"],
                    "major_control": c["findings_major"],
                    "major_cli": t["findings_major"],
                    "preferred": pref,
                })
            else:
                prefs[r].append({"case_id": row["case_id"], "preferred": "n/a"})

    agreement = {}
    for r in reviewers:
        xs, ys = pair_totals[r]["x"], pair_totals[r]["y"]
        n = len(xs)
        sign_same = sum(1 for i in range(n) if (xs[i] > 0) == (ys[i] > 0))
        agreement[r] = {
            "n_artifacts_paired": n,
            "spearman_control_vs_cli_totals": spearman(xs, ys),
            "sign_agreement_any_finding": f"{sign_same}/{n}" if n else None,
        }

    # inter-reviewer agreement: per-artifact totals across all artifacts
    artifact_totals: dict[str, dict[str, int | None]] = {}
    for row in cases:
        for lab in ["A", "B"]:
            art_key = f"{row['case_id']}-{lab}"
            artifact_totals.setdefault(art_key, {})
            for r in reviewers:
                rev = row["labels"][lab]["reviews"].get(r) or {}
                s = rev.get("summary")
                artifact_totals[art_key][r] = s["findings_total"] if s else None
    if len(reviewers) >= 2:
        r1, r2 = reviewers[0], reviewers[1]
        xs2, ys2 = [], []
        for art_key in sorted(artifact_totals):
            v1, v2 = artifact_totals[art_key][r1], artifact_totals[art_key][r2]
            if v1 is not None and v2 is not None:
                xs2.append(float(v1))
                ys2.append(float(v2))
        agreement["inter_reviewer"] = {
            "reviewers": [r1, r2],
            "n_artifacts": len(xs2),
            "spearman": spearman(xs2, ys2),
        }

    payload = {
        "schema_version": "semantic-rubric-kimi-maritaca/v1",
        "rubric_doc": "docs/hermes-case-study/semantic-rubric-v2.md",
        "run_id": key.get("run_id") or "run-v2-01",
        "scored_at": datetime.now(BRT).isoformat(),
        "categories": CATEGORIES,
        "panel_usage_totals": totals,
        "cases": cases,
        "per_condition_mean_findings": {
            r: {
                cond: round(sum(v) / len(v), 2) if v else None
                for cond, v in per_condition[r].items()
            }
            for r in reviewers
        },
        "preferences": prefs,
        "reviewer_agreement": agreement,
    }
    out = args.blind_dir / "semantic-rubric-scores.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("WROTE", out)
    print("PANEL_TOKENS", json.dumps(totals, ensure_ascii=False))
    for r in reviewers:
        agg = {p["preferred"] for p in prefs[r]}
        counts = {p["preferred"]: sum(1 for x in prefs[r] if x["preferred"] == p["preferred"]) for p in prefs[r]}
        print(f"PREF[{r}] {counts} (set={sorted(agg)})")
    print("AGREEMENT", json.dumps(agreement, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
