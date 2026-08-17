#!/usr/bin/env python3
"""Run one arm of Hermes×Curupira case study (control|curupira)."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from pathlib import Path

REPO = Path("/home/jorge/dev/linter-curupira")
BASE = REPO / "artifacts/hermes-case-study/v1"


def sh(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, capture_output=True, **kw)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case-id", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--condition", choices=["control", "curupira", "cli"], required=True)
    ap.add_argument("--input-rel", required=True, help="relative to case dir, e.g. inputs/x.md")
    ap.add_argument("--artifact-name", default="procedimento.md")
    ap.add_argument("--max-turns", type=int, default=30)
    args = ap.parse_args()

    case_dir = REPO / "cases" / args.case_id
    task = (case_dir / "task.md").read_text(encoding="utf-8")
    src_input = case_dir / args.input_rel
    if not src_input.is_file():
        raise SystemExit(f"missing input {src_input}")

    work = Path(f"/tmp/cs-ab/{args.case_id}-{args.run_id}-{args.condition}")
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    art = work / args.artifact_name
    shutil.copy2(src_input, art)
    shutil.copy2(case_dir / "task.md", work / "task.md")
    # helpful extras
    for name in ("expected-requirements.md", "acceptance-tests.md"):
        p = case_dir / name
        if p.is_file():
            shutil.copy2(p, work / name)

    out_dir = BASE / args.condition / f"{args.case_id}-{args.run_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.condition == "control":
        prompt = f"""Você é o braço CONTROLE do estudo {args.case_id} (sem Curupira).

Leia a tarefa completa abaixo e o arquivo de trabalho:
- tarefa: {work / 'task.md'}
- artefato a editar: {art}

{task}

Regras do braço controle:
- NÃO chame curupira nem skill de lint.
- NÃO envie documento a APIs.
- Preserve identificadores técnicos exigidos na tarefa.
- Priorize legibilidade para o usuário final e texto enxuto (menos tokens de leitura).
- Sobrescreva somente: {art}
- Ao terminar: imprima path, chars do arquivo e resumo de 1 linha.
"""
        skills: list[str] = []
    elif args.condition == "curupira":
        prompt = f"""/curupira-preflight

Você é o braço SKILL do estudo {args.case_id} (skill curupira-preflight pré-carregada).
Siga a skill curupira-preflight.

Arquivos:
- tarefa: {work / 'task.md'}
- artefato a editar: {art}

{task}

Regras do braço skill:
- Siga curupira-preflight.
- Antes de declarar pronto, rode exatamente:
  curupira lint {art} --enable-rule CURUPIRA-PT-PONT-001 --format json
- Exit 1 = incompleto: corrija e repita (máx 2 ciclos). Só sucesso com exit 0.
- Sem semantic-review / sem Maritaca.
- Preserve identificadores técnicos exigidos na tarefa.
- Otimize para o usuário: frases curtas, passos explícitos, sem muro de texto.
- Prefira enxugar prosa inútil (menos tokens de leitura) sem apagar fatos.
- Sobrescreva somente: {art}
- Ao terminar: path, exit do lint, chars do arquivo, resumo 1 linha.
"""
        skills = ["curupira-preflight"]
    else:  # cli — no skill dump
        prompt = f"""Você é o braço CLI do estudo {args.case_id}.
NÃO carregue skill. Use só o binário local curupira.

Arquivos:
- tarefa: {work / 'task.md'}
- artefato a editar: {art}

{task}

Regras do braço CLI (mínimas):
- Edite {art} para legibilidade: frases curtas, passos explícitos, sem muro de texto.
- Preserve identificadores técnicos exigidos na tarefa.
- Antes de declarar pronto, rode EXATAMENTE:
  curupira lint {art} --enable-rule CURUPIRA-PT-PONT-001 --format json
- Exit 1 = incompleto: corrija e repita (máx 2 ciclos). Só sucesso com exit 0.
- NÃO use semantic-review. NÃO chame APIs.
- NÃO peça nem carregue skill curupira-preflight.
- Sobrescreva somente: {art}
- Ao terminar: path, exit do lint, chars do arquivo, resumo 1 linha.
"""
        skills = []

    (out_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    usage = out_dir / "usage.json"
    stdout_p = out_dir / "stdout.txt"
    stderr_p = out_dir / "stderr.txt"

    cmd = [
        "hermes",
        "--usage-file",
        str(usage),
        "chat",
        "-q",
        prompt,
        "--in",
        str(work),
        "--reasoning",
        "low",
        "--yolo",
        "-Q",
        "--max-turns",
        str(args.max_turns),
        "--source",
        "tool",
        "--ignore-rules",
    ]
    for s in skills:
        cmd.extend(["-s", s])

    t0 = time.time()
    proc = sh(cmd, timeout=600)
    wall = round(time.time() - t0, 1)
    stdout_p.write_text(proc.stdout or "", encoding="utf-8")
    stderr_p.write_text(proc.stderr or "", encoding="utf-8")

    # snapshot artifact
    if art.is_file():
        shutil.copy2(art, out_dir / args.artifact_name)
    else:
        (out_dir / "MISSING_ARTIFACT").write_text(str(art), encoding="utf-8")

    # residual lint
    residual = {"exit_code": 2, "findings_n": None, "diagnostics": []}
    if (out_dir / args.artifact_name).is_file():
        lp = sh(
            [
                "curupira",
                "lint",
                str(out_dir / args.artifact_name),
                "--enable-rule",
                "CURUPIRA-PT-PONT-001",
                "--format",
                "json",
            ]
        )
        try:
            payload = json.loads(lp.stdout or "{}")
        except json.JSONDecodeError:
            payload = {}
        diags = payload.get("diagnostics") if isinstance(payload, dict) else []
        residual = {
            "exit_code": int(lp.returncode),
            "findings_n": len(diags) if isinstance(diags, list) else None,
            "diagnostics": diags if isinstance(diags, list) else [],
        }
    (out_dir / "residual-lint.json").write_text(
        json.dumps(residual, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # session id from stderr
    session_id = None
    for line in (proc.stderr or "").splitlines():
        if "session_id:" in line:
            session_id = line.split("session_id:", 1)[1].strip()

    meta = {
        "case_id": args.case_id,
        "run_id": args.run_id,
        "condition": args.condition,
        "hermes_exit": proc.returncode,
        "wall_s": wall,
        "session_id": session_id,
        "work_dir": str(work),
        "artifact": str(out_dir / args.artifact_name),
        "residual": residual,
        "skills": skills,
    }
    (out_dir / "arm-meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(meta, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
