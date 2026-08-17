#!/usr/bin/env python3
"""Analisa o piloto de variância do estudo Hermes × Curupira.

Lê artifacts/hermes-case-study/pilot-variance/pilot-runs.json e responde:
1. A captura de tokens funcionou? (usage completo em todas as execuções)
2. A variância intra-tarefa justifica 3 execuções na grade completa?
3. Sinal preliminar de direção: tokens e legibilidade, controle vs tratamento.

Saída: texto + JSON de resumo. Nada de teste de hipótese: n=3 por célula é
só piloto. Reporta mediana e dispersão, conforme protocolo.
"""

from __future__ import annotations

import argparse
import json
import statistics as st
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASE = REPO / "artifacts/hermes-case-study/pilot-variance"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, default=BASE / "pilot-runs.json")
    ap.add_argument("--output", type=Path, default=BASE / "pilot-summary.json")
    args = ap.parse_args()

    runs = json.loads(args.input.read_text(encoding="utf-8"))
    cells: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in runs:
        cells[(r["case_id"], r["condition"])].append(r)

    # 1) qualidade da captura
    missing_usage = [
        f"{r['case_id']}/{r['condition']}/{r['run_id']}"
        for r in runs
        if not (r.get("usage") or {}).get("input_tokens")
    ]
    missing_artifact = [
        f"{r['case_id']}/{r['condition']}/{r['run_id']}"
        for r in runs
        if not r.get("artifact_present")
    ]

    # 2) variância intra-tarefa por condição e métrica
    metrics = ["input_tokens", "output_tokens", "total_tokens", "api_calls", "wall_seconds"]
    var_by_condition: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for (_case_id, cond), group in cells.items():
        for m in metrics:
            if m == "wall_seconds":
                vals = [float(g.get("wall_seconds") or 0) for g in group]
            else:
                vals = [float((g.get("usage") or {}).get(m) or 0) for g in group]
            if len(vals) >= 2:
                mean = st.mean(vals)
                cv = (st.stdev(vals) / mean * 100) if mean else 0.0
                var_by_condition[cond][m].append(round(cv, 1))

    # 3) direção preliminar por caso: mediana controle vs mediana tratamento
    prelim: list[dict] = []
    for case_id in sorted({c for c, _ in cells}):
        ctrl = cells.get((case_id, "control"), [])
        trat = cells.get((case_id, "curupira"), [])
        if not ctrl or not trat:
            continue

        def med(group: list[dict], m: str) -> float:
            if m == "wall_seconds":
                vals = [float(g.get("wall_seconds") or 0) for g in group]
            elif m in ("residual_findings_n", "chars", "avg_sentence_words"):
                vals = []
                for g in group:
                    if m == "residual_findings_n":
                        v = (g.get("residual_lint") or {}).get("findings_n")
                    else:
                        v = (g.get("readability") or {}).get(m)
                    if v is not None:
                        vals.append(float(v))
            else:
                vals = [float((g.get("usage") or {}).get(m) or 0) for g in group]
            return round(st.median(vals), 2) if vals else 0.0

        row = {"case_id": case_id, "n_control": len(ctrl), "n_curupira": len(trat)}
        for m in metrics + ["residual_findings_n", "chars", "avg_sentence_words"]:
            row[f"ctrl_{m}"] = med(ctrl, m)
            row[f"trat_{m}"] = med(trat, m)
        prelim.append(row)

    summary = {
        "schema_version": "hermes-case-study-pilot-summary/v1",
        "runs_total": len(runs),
        "capture": {
            "missing_usage": missing_usage,
            "missing_artifact": missing_artifact,
            "ok": not missing_usage and not missing_artifact,
        },
        "intra_task_cv_pct": {
            cond: {m: round(st.mean(v), 1) if v else None for m, v in mm.items()}
            for cond, mm in var_by_condition.items()
        },
        "preliminary_direction": prelim,
    }
    args.output.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
