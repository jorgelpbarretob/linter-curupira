#!/usr/bin/env python3
"""Battery control vs default CLI-min for case study."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# case_id -> (input_rel, artifact_name)
CASE_SPECS = {
    "case-001": ("inputs/procedimento.md", "procedimento.md"),
    "case-002": ("inputs/insumos.md", "procedimento-recuperacao.md"),
    "case-003": ("inputs/instrucao.md", "instrucao.md"),
    "case-004": ("inputs/runbook.md", "runbook.md"),
    "case-005": ("inputs/notas.txt", "procedimento.md"),
    "case-006": ("inputs/log-sanitizado.txt", "mitigacao.md"),
    "case-007": ("inputs/procedimento.md", "procedimento.md"),
    "case-008": ("inputs/notas.md", "mitigacao.md"),
    "case-009": ("inputs/notas-lab.md", "pop.md"),
    "case-010": ("inputs/runbook.md", "runbook.md"),
    "case-011": ("inputs/procedimento.md", "procedimento.md"),
    "case-012": ("inputs/notas.md", "acao.md"),
    "case-013": ("inputs/runbook.md", "runbook.md"),
    "case-014": ("inputs/rascunho.md", "pop.md"),
    "case-015": ("inputs/runbook-envase.md", "runbook-envase.md"),
    "case-016": ("inputs/timeline-incidente.md", "mitigacao-parada.md"),
}

DEFAULT_CASES = [
    "case-001", "case-003", "case-004", "case-007", "case-008", "case-009",
    "case-010", "case-011", "case-012", "case-013", "case-014",
]


def run(case_id: str, run_id: str, cond: str, input_rel: str, art: str) -> dict:
    cmd = [
        sys.executable,
        str(REPO / "tools/curupira/run_case_arm.py"),
        "--case-id",
        case_id,
        "--run-id",
        run_id,
        "--condition",
        cond,
        "--input-rel",
        input_rel,
        "--artifact-name",
        art,
    ]
    print("RUN", " ".join(cmd), flush=True)
    p = subprocess.run(cmd, cwd=str(REPO), text=True, capture_output=True)
    sys.stdout.write(p.stdout)
    sys.stderr.write(p.stderr)
    if p.returncode != 0:
        raise SystemExit(p.returncode)
    return json.loads(p.stdout.strip().splitlines()[-1])


def main() -> int:
    run_id = sys.argv[1] if len(sys.argv) > 1 else "run-cli-default"
    cases = DEFAULT_CASES
    if "--cases" in sys.argv:
        i = sys.argv.index("--cases")
        cases = [c.strip() for c in sys.argv[i + 1].split(",") if c.strip()]
    unknown = [c for c in cases if c not in CASE_SPECS]
    if unknown:
        raise SystemExit(f"unknown cases: {unknown}")
    results = []
    for case_id in cases:
        input_rel, art = CASE_SPECS[case_id]
        for cond in ("control", "cli"):
            results.append(run(case_id, run_id, cond, input_rel, art))
    out = REPO / "artifacts/hermes-case-study/v1" / f"battery-{run_id}-raw.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("WROTE", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
