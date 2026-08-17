#!/usr/bin/env python3
"""Esqueleto de orquestração de rodada do estudo Hermes×Curupira.

Não executa o agente sozinho. Valida pacote do caso, roda lint residual
em um artefato já produzido e registra um envelope JSON de rodada.

Uso:
  python3 tools/curupira/run_case_study_round.py \
    --case cases/case-001 \
    --condition control \
    --artifact path/to/final.md \
    --run-id case-001-run-01
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

RULE = "CURUPIRA-PT-PONT-001"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def lint(path: Path) -> dict:
    proc = subprocess.run(
        ["curupira", "lint", str(path), "--enable-rule", RULE, "--format", "json"],
        capture_output=True,
        text=True,
    )
    payload: dict = {}
    if proc.stdout.strip():
        try:
            loaded = json.loads(proc.stdout)
            if isinstance(loaded, dict):
                payload = loaded
        except json.JSONDecodeError:
            payload = {"raw": proc.stdout[:2000]}
    diags = payload.get("diagnostics") if isinstance(payload, dict) else []
    return {
        "exit_code": int(proc.returncode),
        "findings_n": len(diags) if isinstance(diags, list) else None,
        "diagnostics": diags if isinstance(diags, list) else [],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", type=Path, required=True)
    ap.add_argument("--condition", choices=["control", "curupira"], required=True)
    ap.add_argument("--artifact", type=Path, required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--out-root", type=Path, default=Path("artifacts/hermes-case-study/v1"))
    args = ap.parse_args()

    manifest_path = args.case / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not args.artifact.is_file():
        raise SystemExit(f"artifact missing: {args.artifact}")

    result = {
        "schema_version": "hermes-case-study-round/v1",
        "run_id": args.run_id,
        "case_id": manifest.get("case_id"),
        "condition": args.condition,
        "case_package_sha256": manifest.get("package_sha256"),
        "artifact_sha256": sha256_file(args.artifact),
        "ts": time.time(),
        "residual_lint": lint(args.artifact),
        "agent_metrics": {
            "tool_calls": None,
            "turns": None,
            "duration_s": None,
            "tokens": None,
            "note": "preencher a partir da sessão Hermes",
        },
        "acceptance_class": None,
        "notes": "",
    }
    out_dir = args.out_root / args.condition / args.run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "round.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / args.artifact.name).write_bytes(args.artifact.read_bytes())
    print(json.dumps({"wrote": str(out_path), "residual": result["residual_lint"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
