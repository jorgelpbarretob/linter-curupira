#!/usr/bin/env python3
"""Render the countable semantic rubric results as a markdown report.

Usage:
  python3 tools/curupira/report_semantic_rubric.py \
    [--scores artifacts/hermes-case-study/v2/blind/semantic-rubric-scores.json] \
    [--out docs/hermes-case-study/semantic-rubric-results.md]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--scores",
        type=Path,
        default=Path("artifacts/hermes-case-study/v2/blind/semantic-rubric-scores.json"),
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("docs/hermes-case-study/semantic-rubric-results.md"),
    )
    args = ap.parse_args()
    sem = json.loads(args.scores.read_text(encoding="utf-8"))
    reviewers = list((sem.get("panel_usage_totals") or {}).keys())

    lines: list[str] = []
    lines.append("# Rubrica semântica contável — resultados " + str(sem.get("run_id") or ""))
    lines.append("")
    lines.append(f"Schema: `{sem.get('schema_version')}` · Scored at: {sem.get('scored_at')}")
    lines.append(f"Rubrica: `{sem.get('rubric_doc')}`")
    lines.append("")

    # panel tokens
    lines.append("## Tokens do painel (revisores)")
    lines.append("")
    lines.append("| Revisor | calls | in | out | total |")
    lines.append("|---|---|---|---|---|")
    for r in reviewers:
        u = sem["panel_usage_totals"][r]
        lines.append(
            f"| {r} | {u['calls']} | {u['input_tokens']} | {u['output_tokens']} | "
            f"**{u['total_tokens']}** |"
        )
    lines.append("")

    # per-case findings table
    lines.append("## Achados por caso (unblind)")
    lines.append("")
    hdr = "| Case | " + " | ".join(f"{r} C | {r} CLI" for r in reviewers) + " | " + " | ".join(f"{r} pref" for r in reviewers) + " |"
    sep = "|---|" + "---|" * (2 * len(reviewers) + len(reviewers))
    lines.append(hdr)
    lines.append(sep)
    pref_by_case: dict[str, dict[str, str]] = {}
    for r in reviewers:
        for p in sem.get("preferences", {}).get(r, []):
            pref_by_case.setdefault(p["case_id"], {})[r] = p["preferred"]
    for row in sem.get("cases", []):
        case = row["case_id"]
        m = row["label_to_condition"]
        cond: dict[str, dict] = {}
        for lab in ["A", "B"]:
            lab_out = row["labels"].get(lab, {})
            cond[m[lab]] = lab_out
        c_lab, t_lab = cond.get("control", {}), cond.get("cli", {})

        def total_of(lab_out: dict, rev: str) -> str:
            rv = (lab_out.get("reviews") or {}).get(rev) or {}
            s = rv.get("summary")
            return str(s["findings_total"]) if s else "n/a"

        cells = []
        for r in reviewers:
            cells.append(total_of(c_lab, r))
            cells.append(total_of(t_lab, r))
        prefs = [pref_by_case.get(case, {}).get(r, "n/a") for r in reviewers]
        lines.append(f"| {case} | " + " | ".join(cells) + " | " + " | ".join(prefs) + " |")
    lines.append("")
    lines.append("`C` = control, `CLI` = tratamento. Achado sem score = `n/a`.")
    lines.append("")

    # aggregate
    lines.append("## Agregado por condição")
    lines.append("")
    lines.append("| Revisor | média control | média cli | Spearman | sign agree |")
    lines.append("|---|---|---|---|---|")
    means = sem.get("per_condition_mean_findings") or {}
    agr = sem.get("reviewer_agreement") or {}
    for r in reviewers:
        mm = means.get(r, {})
        aa = agr.get(r, {})
        sp = aa.get("spearman_control_vs_cli_totals")
        lines.append(
            f"| {r} | {mm.get('control')} | {mm.get('cli')} | "
            f"{sp if sp is not None else 'n/a'} | {aa.get('sign_agreement_any_finding') or 'n/a'} |"
        )
    lines.append("")

    # preference counts
    lines.append("## Preferência semântica")
    lines.append("")
    for r in reviewers:
        items = sem.get("preferences", {}).get(r, [])
        counts: dict[str, int] = {}
        for p in items:
            counts[p["preferred"]] = counts.get(p["preferred"], 0) + 1
        ordered = " · ".join(f"{k} {v}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1]))
        lines.append(f"- **{r}:** {ordered}")
    lines.append("")

    # integrity: invalid findings rejected + errors
    lines.append("## Integridade")
    lines.append("")
    n_invalid = n_err = 0
    for row in sem.get("cases", []):
        for lab, lab_out in (row.get("labels") or {}).items():
            for rev, rv in (lab_out.get("reviews") or {}).items():
                if "error" in rv:
                    n_err += 1
                    lines.append(f"- `semantic_reviewer_error`: {row['case_id']} {lab} {rev}: {str(rv['error'])[:120]}")
                n = len(rv.get("invalid_rejected") or [])
                if n:
                    n_invalid += n
                    lines.append(f"- `semantic_invalid_findings_rejected`: {row['case_id']} {lab} {rev}: {n} achados sem trecho verificável")
    if n_invalid == 0 and n_err == 0:
        lines.append("- Sem flags. Todos os achados tinham trecho literal verificável.")
    lines.append("")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("WROTE", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
