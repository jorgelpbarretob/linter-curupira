#!/usr/bin/env python3
"""Build 5-dimension A/B report SoT (executor, panel, gate, quality, integrity)."""
from __future__ import annotations

import argparse
import json
import statistics as st
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

BRT = timezone(timedelta(hours=-3))


def med(xs):
    return st.median(xs) if xs else None


def mean(xs):
    return round(st.mean(xs), 2) if xs else None


def anomaly_session(tok: dict, source: str) -> list[dict]:
    flags = []
    tin = int(tok.get("input_tokens") or 0)
    tout = int(tok.get("output_tokens") or 0)
    tot = int(tok.get("total_tokens") or 0)
    if source == "sessiondb" and tot > 0 and tot < 5000 and tin < 3000:
        flags.append(
            {
                "code": "session_tokens_suspiciously_low",
                "evidence": f"total={tot} input={tin} source={source}",
            }
        )
    if tot > 0 and tin + tout > 0 and tot > 3 * (tin + tout):
        flags.append(
            {
                "code": "total_much_greater_than_in_plus_out",
                "evidence": f"total={tot} in+out={tin+tout} (cache/reasoning likely)",
            }
        )
    if tin == 0 and tout == 0 and tot == 0:
        flags.append({"code": "tokens_all_zero", "evidence": source})
    if not tok.get("model"):
        flags.append({"code": "model_missing", "evidence": source})
    return flags


def from_pilot(path: Path) -> dict:
    rows = json.loads(path.read_text(encoding="utf-8"))
    by = {}
    for r in rows:
        by.setdefault((r["case_id"], r["run_id"]), {})[r["condition"]] = r

    pairs = []
    integrity_all = []
    for (case_id, run_id), arms in sorted(by.items()):
        if "control" not in arms or "curupira" not in arms:
            integrity_all.append(
                {
                    "case_id": case_id,
                    "run_id": run_id,
                    "code": "missing_arm",
                    "evidence": list(arms),
                }
            )
            continue
        c, t = arms["control"], arms["curupira"]
        cu, tu = c.get("usage") or {}, t.get("usage") or {}
        source = "usage-file"
        flags = []
        flags += [
            {**f, "arm": "control", "case_id": case_id, "run_id": run_id}
            for f in anomaly_session(cu, source)
        ]
        flags += [
            {**f, "arm": "curupira", "case_id": case_id, "run_id": run_id}
            for f in anomaly_session(tu, source)
        ]
        # gate: treatment residual + skill path implies lint may be via skill; check residual only if no lint flag
        treat_residual = int((t.get("residual_lint") or {}).get("findings_n") or 0)
        ctrl_residual = int((c.get("residual_lint") or {}).get("findings_n") or 0)
        lint_invoked = True if t.get("condition") == "curupira" else False
        # pilot used skill preload; mark integrity
        flags.append(
            {
                "code": "treatment_was_skill_preload_not_cli_min",
                "case_id": case_id,
                "run_id": run_id,
                "evidence": "pilot-variance used --skills curupira-preflight",
            }
        )
        integrity_all.extend(flags)
        pair = {
            "case_id": case_id,
            "run_id": run_id,
            "executor": {
                "model": cu.get("model") or tu.get("model"),
                "provider_note": "athena bailian qwen3.8-max",
                "token_source": source,
                "control": {
                    "input_tokens": cu.get("input_tokens"),
                    "output_tokens": cu.get("output_tokens"),
                    "total_tokens": cu.get("total_tokens"),
                    "reasoning_tokens": cu.get("reasoning_tokens"),
                    "cache_read_tokens": cu.get("cache_read_tokens"),
                    "api_calls": cu.get("api_calls"),
                    "session_id": cu.get("session_id"),
                    "wall_s": c.get("wall_seconds"),
                },
                "treatment": {
                    "input_tokens": tu.get("input_tokens"),
                    "output_tokens": tu.get("output_tokens"),
                    "total_tokens": tu.get("total_tokens"),
                    "reasoning_tokens": tu.get("reasoning_tokens"),
                    "cache_read_tokens": tu.get("cache_read_tokens"),
                    "api_calls": tu.get("api_calls"),
                    "session_id": tu.get("session_id"),
                    "wall_s": t.get("wall_seconds"),
                },
                "delta_treatment_minus_control": {
                    "input_tokens": int(tu.get("input_tokens") or 0)
                    - int(cu.get("input_tokens") or 0),
                    "output_tokens": int(tu.get("output_tokens") or 0)
                    - int(cu.get("output_tokens") or 0),
                    "total_tokens": int(tu.get("total_tokens") or 0)
                    - int(cu.get("total_tokens") or 0),
                },
            },
            "gate": {
                "treatment_lint_invoked": lint_invoked,
                "treatment_residual_zero": treat_residual == 0,
                "control_residual_n": ctrl_residual,
                "treatment_residual_n": treat_residual,
                "operational_pass": bool(lint_invoked and treat_residual == 0),
                "note": "pilot treatment=skill; lint invocation assumed via skill, not CLI-min evidence",
            },
            "quality_auto": {
                "control": c.get("readability"),
                "treatment": t.get("readability"),
            },
            "integrity_flags": flags,
        }
        pairs.append(pair)

    # aggregates
    d_in = [p["executor"]["delta_treatment_minus_control"]["input_tokens"] for p in pairs]
    d_out = [p["executor"]["delta_treatment_minus_control"]["output_tokens"] for p in pairs]
    d_tot = [p["executor"]["delta_treatment_minus_control"]["total_tokens"] for p in pairs]
    return {
        "schema_version": "hermes-case-study-report-5d/v1",
        "report_id": "pilot-variance-athena-qwen3.8-max",
        "generated_at": datetime.now(BRT).isoformat(),
        "models": {
            "executor": "qwen3.8-max",
            "executor_route": "athena bailian / hermes -z --usage-file",
            "panel": None,
        },
        "dimensions_present": [
            "executor_session",
            "panel_reviewer",
            "operational_gate",
            "quality_blind",
            "integrity",
        ],
        "pairs": pairs,
        "aggregate": {
            "n_pairs": len(pairs),
            "median_delta_input": med(d_in),
            "median_delta_output": med(d_out),
            "median_delta_total": med(d_tot),
            "mean_delta_input": mean(d_in),
            "mean_delta_output": mean(d_out),
            "mean_delta_total": mean(d_tot),
            "gate_pass_n": sum(1 for p in pairs if p["gate"]["operational_pass"]),
            "integrity_flag_codes": dict(Counter(f["code"] for f in integrity_all)),
        },
        "panel": {
            "status": "not_in_this_source",
            "reviewers": {},
            "totals": {},
            "note": "Attach panel JSON via --panel",
        },
        "quality_blind": {"status": "not_in_this_source"},
        "integrity": {
            "policy": "anomalies marked, never silently dropped",
            "flags": integrity_all,
        },
    }


def attach_panel(report: dict, panel_path: Path) -> None:
    panel = json.loads(panel_path.read_text(encoding="utf-8"))
    totals = panel.get("panel_usage_totals") or {}
    prefs = panel.get("unblind_preferences") or {}
    per_case = []
    # build per-case reviewer tokens if cases structure
    if panel.get("cases"):
        for row in panel["cases"]:
            cid = row["case_id"]
            entry = {"case_id": cid, "reviewers": {}, "ab_session_tokens": row.get("ab_session_tokens")}
            for lab in ["A", "B"]:
                for rev_name, rev in (row.get("labels", {}).get(lab, {}).get("reviews") or {}).items():
                    entry["reviewers"].setdefault(rev_name, {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "calls": 0, "errors": 0})
                    if "error" in rev and "usage" not in rev:
                        entry["reviewers"][rev_name]["errors"] += 1
                        continue
                    u = rev.get("usage") or {}
                    entry["reviewers"][rev_name]["input_tokens"] += int(u.get("input_tokens") or 0)
                    entry["reviewers"][rev_name]["output_tokens"] += int(u.get("output_tokens") or 0)
                    entry["reviewers"][rev_name]["total_tokens"] += int(u.get("total_tokens") or 0)
                    entry["reviewers"][rev_name]["calls"] += 1
            per_case.append(entry)
    pref_counts = {
        name: dict(Counter(p.get("preferred_condition") for p in items))
        for name, items in prefs.items()
    }
    report["panel"] = {
        "status": "attached",
        "path": str(panel_path),
        "models": panel.get("models"),
        "totals": totals,
        "preference_counts": pref_counts,
        "per_case": per_case,
        "unblind_preferences": prefs,
    }
    report["quality_blind"] = {
        "status": "attached_from_panel",
        "preference_counts": pref_counts,
        "source": str(panel_path),
    }
    report["models"]["panel"] = panel.get("models")
    # integrity: reviewer errors
    for row in panel.get("cases") or []:
        for lab in ["A", "B"]:
            for rev_name, rev in (row.get("labels", {}).get(lab, {}).get("reviews") or {}).items():
                if "error" in rev:
                    report["integrity"]["flags"].append(
                        {
                            "code": "reviewer_error",
                            "case_id": row["case_id"],
                            "label": lab,
                            "reviewer": rev_name,
                            "evidence": str(rev.get("error"))[:200],
                        }
                    )


def attach_semantic(report: dict, semantic_path: Path) -> None:
    """Attach countable semantic rubric scores (blind panel)."""
    sem = json.loads(semantic_path.read_text(encoding="utf-8"))
    prefs = sem.get("preferences") or {}
    pref_counts = {
        name: dict(Counter(p.get("preferred") for p in items))
        for name, items in prefs.items()
    }
    report["semantic_rubric"] = {
        "status": "attached",
        "path": str(semantic_path),
        "schema_version": sem.get("schema_version"),
        "rubric_doc": sem.get("rubric_doc"),
        "categories": sem.get("categories"),
        "panel_usage_totals": sem.get("panel_usage_totals"),
        "per_condition_mean_findings": sem.get("per_condition_mean_findings"),
        "reviewer_agreement": sem.get("reviewer_agreement"),
        "preference_counts": pref_counts,
        "preferences": prefs,
    }
    qb = report.get("quality_blind") or {}
    if qb.get("status") == "not_in_this_source":
        report["quality_blind"] = {
            "status": "attached_from_semantic",
            "source": str(semantic_path),
            "preference_counts": pref_counts,
        }
    else:
        qb["semantic_rubric"] = "attached"
        qb["semantic_source"] = str(semantic_path)
        qb["semantic_preference_counts"] = pref_counts
    report["models"]["semantic_panel"] = {
        name: None for name in (sem.get("panel_usage_totals") or {})
    }
    # integrity: reviewer errors and rejected hallucinated findings
    for row in sem.get("cases") or []:
        for lab, lab_out in (row.get("labels") or {}).items():
            for rev_name, rev in (lab_out.get("reviews") or {}).items():
                if "error" in rev:
                    report["integrity"]["flags"].append({
                        "code": "semantic_reviewer_error",
                        "case_id": row["case_id"],
                        "label": lab,
                        "reviewer": rev_name,
                        "evidence": str(rev.get("error"))[:200],
                    })
                n_invalid = len(rev.get("invalid_rejected") or [])
                if n_invalid:
                    report["integrity"]["flags"].append({
                        "code": "semantic_invalid_findings_rejected",
                        "case_id": row["case_id"],
                        "label": lab,
                        "reviewer": rev_name,
                        "evidence": f"{n_invalid} findings lacked verbatim excerpt",
                    })


def attach_v2_battery(report: dict, battery_path: Path) -> None:
    """Optional second source note — does not replace pilot pairs."""
    b = json.loads(battery_path.read_text(encoding="utf-8"))
    flags = []
    for p in b.get("pairs") or []:
        for arm, tin, tout, tot in [
            ("control", p.get("input_control"), p.get("output_control"), p.get("tokens_control")),
            ("cli", p.get("input_cli"), p.get("output_cli"), p.get("tokens_cli")),
        ]:
            tok = {
                "input_tokens": tin or 0,
                "output_tokens": tout or 0,
                "total_tokens": tot or 0,
                "model": "grok-4.5",
            }
            for f in anomaly_session(tok, "sessiondb"):
                flags.append({**f, "case_id": p["case_id"], "arm": arm, "source_run": "run-v2-01"})
    report.setdefault("cross_sources", {})["v2_battery"] = {
        "path": str(battery_path),
        "n_pairs": b.get("aggregate", {}).get("n_pairs"),
        "median_delta_tokens": b.get("aggregate", {}).get("median_delta_tokens"),
        "token_source": "sessiondb",
        "integrity_flags": flags,
        "note": "v2 battery used grok-4.5 + chat -q; kept for comparison, not mixed into pilot medians",
    }
    report["integrity"]["flags"].extend(flags)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", type=Path, default=Path("artifacts/hermes-case-study/pilot-variance/pilot-runs.json"))
    ap.add_argument("--panel", type=Path, default=None)
    ap.add_argument(
        "--semantic",
        type=Path,
        default=Path("artifacts/hermes-case-study/v2/blind/semantic-rubric-scores.json"),
    )
    ap.add_argument("--v2-battery", type=Path, default=Path("artifacts/hermes-case-study/v2/battery-run-v2-01-summary.json"))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    report = from_pilot(args.pilot)
    if args.panel and args.panel.is_file():
        attach_panel(report, args.panel)
    if args.semantic and args.semantic.is_file():
        attach_semantic(report, args.semantic)
    if args.v2_battery and args.v2_battery.is_file():
        attach_v2_battery(report, args.v2_battery)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("WROTE", args.out)
    print("pairs", report["aggregate"]["n_pairs"])
    print("median_delta_in/out/tot", report["aggregate"]["median_delta_input"], report["aggregate"]["median_delta_output"], report["aggregate"]["median_delta_total"])
    print("integrity_codes", report["aggregate"]["integrity_flag_codes"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
