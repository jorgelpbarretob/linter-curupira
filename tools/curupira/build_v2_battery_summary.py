#!/usr/bin/env python3
"""Build v2 battery summary (control x cli-min) from raw arm metas + sessiondb.

Token source: Postgres sessiondb of the DEFAULT profile (db from
~/.hermes/.env HERMES_SESSIONDB_DSN), matched by session_id.
"""
from __future__ import annotations

import argparse
import json
import shutil
import statistics as st
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools/curupira"))
from score_readability import score_text  # noqa: E402

V1 = REPO / "artifacts/hermes-case-study/v1"
V2 = REPO / "artifacts/hermes-case-study/v2"


def default_profile_dsn() -> str:
    for line in (Path.home() / ".hermes/.env").read_text().splitlines():
        if line.startswith("HERMES_SESSIONDB_DSN="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("HERMES_SESSIONDB_DSN not found in ~/.hermes/.env")


def session_tokens(session_ids: list[str]) -> dict[str, dict]:
    if not session_ids:
        return {}
    ids = ",".join(f"'{s}'" for s in session_ids)
    sql = (
        "select id, model, input_tokens, output_tokens, tool_call_count,"
        " length(system_prompt) from sessions where id in (" + ids + ");"
    )
    p = subprocess.run(
        ["psql", default_profile_dsn(), "-A", "-t", "-F", "\t", "-c", sql],
        capture_output=True, text=True,
    )
    if p.returncode != 0:
        raise SystemExit(f"psql failed: {p.stderr}")
    out = {}
    for line in p.stdout.splitlines():
        sid, model, tin, tout, tools, spl = line.split("\t")
        out[sid] = {
            "model": model,
            "input": int(tin),
            "output": int(tout),
            "tools": int(tools),
            "system_prompt_len": int(spl),
        }
    return out


def read_winner(c: dict, t: dict) -> str:
    ck = (c["max_sentence_words"], -c["list_line_ratio"], c["chars"])
    tk = (t["max_sentence_words"], -t["list_line_ratio"], t["chars"])
    if ck == tk:
        return "tie"
    return "control" if ck < tk else "cli"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_id")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    run_id = args.run_id

    raw_path = V1 / f"battery-{run_id}-raw.json"
    arms = json.loads(raw_path.read_text(encoding="utf-8"))
    by: dict[str, dict[str, dict]] = {}
    for a in arms:
        by.setdefault(a["case_id"], {})[a["condition"]] = a

    sids = [a["session_id"] for a in arms if a.get("session_id")]
    tok = session_tokens(sids)

    blind_dir = V2 / "blind" / run_id
    blind_dir.mkdir(parents=True, exist_ok=True)

    pairs = []
    blind_items = []
    for idx, (case_id, conds) in enumerate(by.items()):
        c, t = conds["control"], conds["cli"]
        art_c = Path(c["artifact"])
        art_t = Path(t["artifact"])
        sc = score_text(art_c.read_text(encoding="utf-8"))
        stt = score_text(art_t.read_text(encoding="utf-8"))
        tc = tok.get(c.get("session_id") or "", {})
        tt = tok.get(t.get("session_id") or "", {})
        stdout_t = (art_t.parent / "stdout.txt").read_text(encoding="utf-8")
        lint_invoked = "lint" in stdout_t.lower()
        res_c = c["residual"]["findings_n"]
        res_t = t["residual"]["findings_n"]
        gate = bool(lint_invoked and res_t == 0 and c["residual"]["exit_code"] == 0)
        in_c, out_c = tc.get("input", 0), tc.get("output", 0)
        in_t, out_t = tt.get("input", 0), tt.get("output", 0)
        tot_c, tot_t = in_c + out_c, in_t + out_t
        winner_tok = (
            "tie" if tot_c == tot_t else ("control" if tot_c < tot_t else "cli")
        )
        pair = {
            "case_id": case_id,
            "operational_gate_pass": gate,
            "residual_control": res_c,
            "residual_cli": res_t,
            "cli_lint_invoked": lint_invoked,
            "model_control": tc.get("model"),
            "model_cli": tt.get("model"),
            "tokens_control": tot_c,
            "tokens_cli": tot_t,
            "delta_tokens": tot_t - tot_c,
            "input_control": in_c,
            "input_cli": in_t,
            "delta_input": in_t - in_c,
            "output_control": out_c,
            "output_cli": out_t,
            "delta_output": out_t - out_c,
            "system_prompt_len_control": tc.get("system_prompt_len"),
            "system_prompt_len_cli": tt.get("system_prompt_len"),
            "tools_control": tc.get("tools"),
            "tools_cli": tt.get("tools"),
            "wall_control": c["wall_s"],
            "wall_cli": t["wall_s"],
            "chars_control": sc["chars"],
            "chars_cli": stt["chars"],
            "max_sent_control": sc["max_sentence_words"],
            "max_sent_cli": stt["max_sentence_words"],
            "list_ratio_control": sc["list_line_ratio"],
            "list_ratio_cli": stt["list_line_ratio"],
            "winner_tokens": winner_tok,
            "winner_readability_auto": read_winner(sc, stt),
            "session_control": c.get("session_id"),
            "session_cli": t.get("session_id"),
            "artifact_control": str(art_c),
            "artifact_cli": str(art_t),
        }
        pairs.append(pair)

        # blind pack: alternate A/B assignment by case order
        a_cond = "control" if idx % 2 == 0 else "cli"
        b_cond = "cli" if a_cond == "control" else "control"
        src = {"control": art_c, "cli": art_t}
        fa = blind_dir / f"{case_id}-A.md"
        fb = blind_dir / f"{case_id}-B.md"
        shutil.copy2(src[a_cond], fa)
        shutil.copy2(src[b_cond], fb)
        blind_items.append({
            "case_id": case_id,
            "label_to_condition": {"A": a_cond, "B": b_cond},
            "files": {"A": str(fa), "B": str(fb)},
            "rubric_path": "docs/hermes-case-study/rubric-v1.md",
            "status": "awaiting_human_blind_review",
        })

    d_tok = [p["delta_tokens"] for p in pairs]
    d_in = [p["delta_input"] for p in pairs]
    d_out = [p["delta_output"] for p in pairs]

    def wins(key):
        w = {"control": 0, "cli": 0, "tie": 0}
        for p in pairs:
            w[p[key]] += 1
        return w

    summary = {
        "schema_version": "hermes-case-study-v2-battery/v1",
        "run_id": run_id,
        "protocol": "docs/hermes-case-study/protocol-v2.md",
        "v1_release_anchor": "v1-cli-default-2026-08-16",
        "default_treatment": "cli-min",
        "success_split": {
            "operational_gate": ["lint_executed", "residual_zero"],
            "quality_outcomes": ["readability", "accept", "rework", "tokens"],
        },
        "pairs": pairs,
        "aggregate": {
            "n_pairs": len(pairs),
            "residual_all_zero": all(
                p["residual_control"] == 0 and p["residual_cli"] == 0 for p in pairs
            ),
            "operational_gate_pass_n": sum(1 for p in pairs if p["operational_gate_pass"]),
            "mean_delta_tokens": round(st.mean(d_tok), 1) if d_tok else None,
            "median_delta_tokens": st.median(d_tok) if d_tok else None,
            "mean_delta_input": round(st.mean(d_in), 1) if d_in else None,
            "median_delta_input": st.median(d_in) if d_in else None,
            "mean_delta_output": round(st.mean(d_out), 1) if d_out else None,
            "median_delta_output": st.median(d_out) if d_out else None,
            "token_wins": wins("winner_tokens"),
            "read_wins": wins("winner_readability_auto"),
        },
        "blind_review": blind_items,
        "token_reporting_policy": (
            "Always include session input/output/total tokens and deltas in"
            " every A/B table."
        ),
        "panel_reviews": {"status": "awaiting_panel"},
    }

    # copy raw next to summary (v2 SoT), keeping v1 copy as runner output
    raw_v2 = V2 / f"battery-{run_id}-raw.json"
    shutil.copy2(raw_path, raw_v2)

    out = args.out or (V2 / f"battery-{run_id}-summary.json")
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    key = {
        "schema_version": "blind-key/v1",
        "run_id": run_id,
        "items": blind_items,
    }
    (blind_dir / "KEY-DO-NOT-SHARE-until-scores.json").write_text(
        json.dumps(key, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print("WROTE", out)
    print("WROTE", raw_v2)
    print("WROTE", blind_dir)
    print("aggregate", json.dumps(summary["aggregate"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
