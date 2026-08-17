#!/usr/bin/env python3
"""Kimi vs Maritaca agreement for matrix Y4 + final integrated decision report.

Inputs (both must exist):
  blind-clarity/maritaca-clarity-scores.json   (reviewer 1)
  blind-clarity/kimi-c1c4-scores.json          (reviewer 2)

Outputs:
  blind-clarity/agreement-kimi-maritaca.json
  docs/hermes-case-study/report-y4-two-reviewers.md

Agreement metrics:
- Spearman on ordinal scores: clarity_1to5, findings_total (per artifact)
- accept-class agreement rate (per artifact)
- preference agreement rate (per model-case pair)
- mean |S_kimi - S_compat_maritaca| not available; use clarity delta instead
- case-012 kept everywhere and reported as sensitivity analysis, never excluded
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

BRT = timezone(timedelta(hours=-3))
LOCK_ORDER = [
    "qwen/qwen3.8-27b",
    "nvidia/nemotron-3.5-lightning",
    "meta/muse-glimmer-30b",
    "thinkingmachines/inkling-small",
]
CASES = ["case-007", "case-008", "case-012"]


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
    ap.add_argument("--blind-dir", type=Path, default=Path("artifacts/hermes-case-study/matrix-y4-smoke/blind-clarity"))
    ap.add_argument("--out-json", type=Path, default=None)
    ap.add_argument("--out-md", type=Path, default=Path("docs/hermes-case-study/report-y4-two-reviewers.md"))
    args = ap.parse_args()
    blind = args.blind_dir

    key = json.loads((blind / "KEY-DO-NOT-SHARE-until-scores.json").read_text(encoding="utf-8"))
    meta = {k["label"]: k for k in key["items"]}
    mar = {e["label"]: e for e in json.loads((blind / "maritaca-clarity-scores.json").read_text())["scores"]}
    kim = {e["label"]: e for e in json.loads((blind / "kimi-c1c4-scores.json").read_text())["scores"]}

    # paired artifacts
    pairs = []
    for lab, m in meta.items():
        a, b = mar.get(lab), kim.get(lab)
        if not a or not b or "clarity_1to5" not in a or "S" not in b:
            continue
        pairs.append({"label": lab, **m, "mar": a, "kim": b})

    xs_cl, ys_cl = [], []
    xs_f, ys_f = [], []
    class_agree = 0
    for p in pairs:
        xs_cl.append(float(p["mar"]["clarity_1to5"]))
        ys_cl.append(float(p["kim"]["clarity_1to5"]))
        xs_f.append(float(p["mar"]["summary"]["findings_total"]))
        ys_f.append(float(p["kim"]["summary"]["findings_total"]))
        if p["mar"]["accept_class"] == p["kim"]["accept_class"]:
            class_agree += 1

    # per-pair preference for each reviewer
    def kimi_pref(c: dict, t: dict) -> str:
        # rubric v1 preference: no blocked side; higher S; then fewer zeros; then tie
        if c["accept_class"] == "bloqueado" and t["accept_class"] != "bloqueado":
            return "cli"
        if t["accept_class"] == "bloqueado" and c["accept_class"] != "bloqueado":
            return "control"
        if c["S"] != t["S"]:
            return "cli" if t["S"] > c["S"] else "control"
        return "tie"

    def mar_pref(c: dict, t: dict) -> str:
        if c["clarity_1to5"] != t["clarity_1to5"]:
            return "cli" if t["clarity_1to5"] > c["clarity_1to5"] else "control"
        cf, tf = c["summary"]["findings_total"], t["summary"]["findings_total"]
        if cf != tf:
            return "cli" if tf < cf else "control"
        return "tie"

    pref_rows = []
    by_model: dict[str, dict[str, dict]] = {}
    for model in LOCK_ORDER:
        by_model[model] = {}
        for cid in CASES:
            kc = kt = mc = mt = None
            for p in pairs:
                if p["model"] == model and p["case_id"] == cid:
                    if p["condition"] == "control":
                        kc, mc = p["kim"], p["mar"]
                    else:
                        kt, mt = p["kim"], p["mar"]
            if not (kc and kt and mc and mt):
                continue
            kp = kimi_pref(kc, kt)
            mp = mar_pref(mc, mt)
            pref_rows.append({"model": model, "case_id": cid, "kimi_pref": kp, "mar_pref": mp,
                              "kimi_S_c": kc["S"], "kimi_S_t": kt["S"],
                              "mar_cl_c": mc["clarity_1to5"], "mar_cl_t": mt["clarity_1to5"]})
            by_model[model][cid] = {"kimi_pref": kp, "mar_pref": mp,
                                    "kimi_S_c": kc["S"], "kimi_S_t": kt["S"],
                                    "mar_cl_c": mc["clarity_1to5"], "mar_cl_t": mt["clarity_1to5"],
                                    "kimi_class_c": kc["accept_class"], "kimi_class_t": kt["accept_class"],
                                    "mar_class_c": mc["accept_class"], "mar_class_t": mt["accept_class"]}

    pref_agree = sum(1 for r in pref_rows if r["kimi_pref"] == r["mar_pref"])

    agreement = {
        "n_artifacts_paired": len(pairs),
        "spearman_clarity_maritaca_vs_kimi": spearman(xs_cl, ys_cl),
        "spearman_findings_maritaca_vs_kimi": spearman(xs_f, ys_f),
        "accept_class_agreement_rate": round(class_agree / len(pairs), 3) if pairs else None,
        "preference_agreement_rate": round(pref_agree / len(pref_rows), 3) if pref_rows else None,
        "preference_agreement_n": pref_agree,
        "preference_n": len(pref_rows),
    }

    # per-model aggregates from kimi
    model_agg = {}
    for model in LOCK_ORDER:
        c_s, t_s, c_cl, t_cl = [], [], [], []
        c_f, t_f = [], []
        for p in pairs:
            if p["model"] != model:
                continue
            if p["condition"] == "control":
                c_s.append(p["kim"]["S"]); c_cl.append(p["kim"]["clarity_1to5"])
                c_f.append(p["kim"]["summary"]["findings_total"])
            else:
                t_s.append(p["kim"]["S"]); t_cl.append(p["kim"]["clarity_1to5"])
                t_f.append(p["kim"]["summary"]["findings_total"])
        mean = lambda v: round(sum(v) / len(v), 2) if v else None
        model_agg[model] = {
            "kimi_S_control_mean": mean(c_s), "kimi_S_cli_mean": mean(t_s),
            "kimi_clarity_control_mean": mean(c_cl), "kimi_clarity_cli_mean": mean(t_cl),
            "kimi_findings_control_mean": mean(c_f), "kimi_findings_cli_mean": mean(t_f),
        }

    kimi_tokens = json.loads((blind / "kimi-c1c4-scores.json").read_text())["panel_usage_totals"]

    payload = {
        "schema_version": "matrix-y4-agreement-kimi-maritaca/v1",
        "run_id": key.get("run_id"),
        "generated_at": datetime.now(BRT).isoformat(),
        "agreement": agreement,
        "model_aggregates": model_agg,
        "preference_rows": pref_rows,
        "kimi_panel_usage_totals": kimi_tokens,
        "case_012_policy": "kept in all aggregates; reported as sensitivity analysis, never excluded",
    }
    out_json = args.out_json or (blind / "agreement-kimi-maritaca.json")
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # ---- markdown ----
    L = []
    L.append("# Matriz Y4 — dois revisores (Kimi C1–C4 + Maritaca)")
    L.append("")
    L.append(f"Run `{key.get('run_id')}` · {len(pairs)} artefatos pareados · gerado {payload['generated_at'][:19]}")
    L.append("")
    L.append("Instrumentos: Kimi `kimi-k2.7` com rubrica C1–C4 (semantic-rubric-v1) + clareza 1–5 + achados; "
             "Maritaca `sabia-4-thinking` com clareza 1–5 + achados. Mesmos 24 artefatos cegos (M01–M24).")
    L.append("")
    L.append("## Concordância Kimi–Maritaca")
    L.append("")
    L.append("| Métrica | Valor |")
    L.append("|---|---|")
    L.append(f"| Spearman clareza (1–5) | {agreement['spearman_clarity_maritaca_vs_kimi']} |")
    L.append(f"| Spearman findings_total | {agreement['spearman_findings_maritaca_vs_kimi']} |")
    L.append(f"| Acordo de classe de aceite | {agreement['accept_class_agreement_rate']} ({class_agree}/{len(pairs)}) |")
    L.append(f"| Acordo de preferência A/B | {agreement['preference_agreement_rate']} ({pref_agree}/{len(pref_rows)}) |")
    L.append("")
    L.append("## Tokens do painel Kimi")
    L.append("")
    L.append(f"calls {kimi_tokens['calls']} · ok {kimi_tokens['ok']} · retries {kimi_tokens['retries']} · "
             f"in {kimi_tokens['input_tokens']} · out {kimi_tokens['output_tokens']} · **total {kimi_tokens['total_tokens']}**")
    L.append("")
    L.append("## Por modelo (Kimi C1–C4)")
    L.append("")
    L.append("| Modelo | S C | S CLI | clareza C | clareza CLI | findings C | findings CLI |")
    L.append("|---|---:|---:|---:|---:|---:|---:|")
    for model in LOCK_ORDER:
        a = model_agg[model]
        L.append(f"| {model} | {a['kimi_S_control_mean']} | {a['kimi_S_cli_mean']} | "
                 f"{a['kimi_clarity_control_mean']} | {a['kimi_clarity_cli_mean']} | "
                 f"{a['kimi_findings_control_mean']} | {a['kimi_findings_cli_mean']} |")
    L.append("")
    L.append("## Preferência por par")
    L.append("")
    L.append("| Modelo | Case | S C→CLI (Kimi) | clareza C→CLI (Maritaca) | pref Kimi | pref Maritaca |")
    L.append("|---|---|---|---|---|---|")
    for r in pref_rows:
        mark = " ⚠" if r["case_id"] == "case-012" else ""
        L.append(f"| {r['model']} | {r['case_id']}{mark} | {r['kimi_S_c']}→{r['kimi_S_t']} | "
                 f"{r['mar_cl_c']}→{r['mar_cl_t']} | {r['kimi_pref']} | {r['mar_pref']} |")
    L.append("")
    L.append("⚠ = case-012 mantido em todos os agregados; análise de sensibilidade abaixo, sem exclusão.")
    L.append("")

    # sensitivity: recompute agreement excluding case-012
    rows_no12 = [r for r in pref_rows if r["case_id"] != "case-012"]
    agree_no12 = sum(1 for r in rows_no12 if r["kimi_pref"] == r["mar_pref"])
    L.append("## Sensibilidade case-012 (sem exclusão)")
    L.append("")
    L.append(f"Acordo de preferência com case-012: {pref_agree}/{len(pref_rows)} · "
             f"sem case-012: {agree_no12}/{len(rows_no12)}")
    L.append("")

    # decision per owner framework
    agree_rate = pref_agree / len(pref_rows) if pref_rows else 0
    sp_cl = agreement["spearman_clarity_maritaca_vs_kimi"] or 0
    if agree_rate >= 2 / 3 and sp_cl >= 0.5:
        verdict = "convergente"
    elif agree_rate >= 1 / 3:
        verdict = "misto_discordante"
    else:
        verdict = "inconclusivo"

    L.append("## Decisão (framework do mantenedor)")
    L.append("")
    L.append(f"Classificação: **{verdict}**")
    L.append("")
    if verdict == "convergente":
        L.append("Há evidência para afirmar efeito semântico da CLI sob certas famílias de modelo.")
    elif verdict == "misto_discordante":
        L.append("- Revisores não convergem na camada semântica (acordo de preferência abaixo de 2/3).")
        L.append("- Narrativa do estudo fica limitada ao gate determinístico. Sem alegação de ganho semântico.")
        L.append("- Benefício do Inkling-small permanece: gate determinístico zerou residual que o control deixou (1/3 vs 3/3). Esse fato independe da camada semântica.")
    else:
        L.append("Sem sinal discernível. Próximo passo: ampliar somente Inkling-small com n=3.")
    L.append("")
    L.append("## Integridade")
    L.append("")
    L.append("- M13 (Kimi) truncado na primeira passada (`finish_reason=length`, zeros default). Detectado, re-executado com max_tokens maior. S final 7.")
    L.append("- SIGPIPE matou o script no meio do loop em uma passada; M14–M24 perdidos do checkpoint e recomputados. Tokens das passadas perdidas não entram no total abaixo.")
    L.append("- case-012 mantido em todos os agregados; sensibilidade acima, sem exclusão.")
    L.append("")

    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("WROTE", out_json)
    print("WROTE", args.out_md)
    print("AGREEMENT", json.dumps(agreement, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
