#!/usr/bin/env python3
"""Helpers for semantic-rubric-v1: derive S, accept_class, preference."""
from __future__ import annotations

from typing import Any


def clamp_ci(v: Any) -> int:
    try:
        n = int(v)
    except (TypeError, ValueError):
        raise ValueError(f"Ci must be int 0..2, got {v!r}")
    if n not in (0, 1, 2):
        raise ValueError(f"Ci must be 0..2, got {n}")
    return n


def score_artifact(
    *,
    C1: int,
    C2: int,
    C3: int,
    C4: int,
    critical_block: bool = False,
) -> dict:
    c1, c2, c3, c4 = map(clamp_ci, (C1, C2, C3, C4))
    s = c1 + c2 + c3 + c4
    if critical_block:
        accept = "bloqueado"
    elif s <= 4 or 0 in (c1, c2, c3, c4):
        accept = "rejeitado_retrabalho_maior"
    elif s <= 6:
        accept = "aceito_retrabalho_menor"
    else:
        accept = "aceito"
    # compat clarity
    if s <= 1:
        clarity = 1
    elif s <= 3:
        clarity = 2
    elif s == 4:
        clarity = 3
    elif s <= 6:
        clarity = 4
    else:
        clarity = 5
    return {
        "C1_executability": c1,
        "C2_fidelity_coverage": c2,
        "C3_structure_scan": c3,
        "C4_ambiguity": c4,
        "S": s,
        "critical_block": bool(critical_block),
        "accept_class": accept,
        "clarity_1to5_compat": clarity,
    }


def prefer_pair(score_a: dict, score_b: dict) -> dict:
    """Blind preference using semantic-rubric-v1 rules."""
    ba = bool(score_a.get("critical_block"))
    bb = bool(score_b.get("critical_block"))
    if ba and not bb:
        return {
            "preferred_label": "B",
            "tie_break_rule": "block_A",
            "S_A": score_a["S"],
            "S_B": score_b["S"],
            "critical_block_A": ba,
            "critical_block_B": bb,
        }
    if bb and not ba:
        return {
            "preferred_label": "A",
            "tie_break_rule": "block_B",
            "S_A": score_a["S"],
            "S_B": score_b["S"],
            "critical_block_A": ba,
            "critical_block_B": bb,
        }

    sa, sb = int(score_a["S"]), int(score_b["S"])
    if sa > sb:
        rule, pref = "higher_S", "A"
    elif sb > sa:
        rule, pref = "higher_S", "B"
    else:
        zeros_a = sum(
            1
            for k in (
                "C1_executability",
                "C2_fidelity_coverage",
                "C3_structure_scan",
                "C4_ambiguity",
            )
            if int(score_a[k]) == 0
        )
        zeros_b = sum(
            1
            for k in (
                "C1_executability",
                "C2_fidelity_coverage",
                "C3_structure_scan",
                "C4_ambiguity",
            )
            if int(score_b[k]) == 0
        )
        if zeros_a < zeros_b:
            rule, pref = "fewer_zero_Ci", "A"
        elif zeros_b < zeros_a:
            rule, pref = "fewer_zero_Ci", "B"
        else:
            for key, name in (
                ("C1_executability", "C1"),
                ("C2_fidelity_coverage", "C2"),
                ("C4_ambiguity", "C4"),
                ("C3_structure_scan", "C3"),
            ):
                if int(score_a[key]) > int(score_b[key]):
                    rule, pref = f"higher_{name}", "A"
                    break
                if int(score_b[key]) > int(score_a[key]):
                    rule, pref = f"higher_{name}", "B"
                    break
            else:
                rule, pref = "tie", "tie"

    return {
        "preferred_label": pref,
        "tie_break_rule": rule,
        "S_A": sa,
        "S_B": sb,
        "critical_block_A": ba,
        "critical_block_B": bb,
    }


if __name__ == "__main__":
    # quick self-check anchors
    low = score_artifact(C1=0, C2=0, C3=0, C4=0, critical_block=True)
    mid = score_artifact(C1=2, C2=2, C3=2, C4=1)
    high = score_artifact(C1=2, C2=2, C3=2, C4=2)
    assert low["accept_class"] == "bloqueado" and low["S"] == 0
    assert mid["S"] == 7 and mid["accept_class"] == "aceito"
    assert high["S"] == 8 and high["accept_class"] == "aceito"
    p = prefer_pair(mid, high)
    assert p["preferred_label"] == "B" and p["tie_break_rule"] == "higher_S"
    print("semantic_rubric_score self-check OK", low, mid, high, p)
