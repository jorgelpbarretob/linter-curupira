#!/usr/bin/env python3
"""Piloto de variância do estudo Hermes × Curupira.

Objetivo: validar captura de tokens na rota one-shot (-z --usage-file) e
estimar variância intra-tarefa antes da grade completa.

Desenho (conforme pré-registro v1 aprovado):
  2 casos × 2 braços × 3 execuções = 12 sessões
  rota: hermes -z PROMPT --usage-file U --in WORK --reasoning low --yolo
  tratamento adiciona --skills curupira-preflight

Saída por execução: usage.json, artefato, residual-lint.json,
readability.json, envelope run.json em artifacts/hermes-case-study/pilot-variance/.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from pathlib import Path

REPO = Path("/home/jorge/dev/linter-curupira")
CASES = REPO / "cases"
BASE = REPO / "artifacts/hermes-case-study/pilot-variance"
RULE = "CURUPIRA-PT-PONT-001"
TIMEOUT_S = 600


def sh(cmd: list[str], timeout: int = TIMEOUT_S) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)


def residual_lint(path: Path) -> dict:
    lp = sh(
        ["curupira", "lint", str(path), "--enable-rule", RULE, "--format", "json"],
        timeout=60,
    )
    try:
        payload = json.loads(lp.stdout or "{}")
    except json.JSONDecodeError:
        payload = {}
    diags = payload.get("diagnostics") if isinstance(payload, dict) else []
    return {
        "exit_code": int(lp.returncode),
        "findings_n": len(diags) if isinstance(diags, list) else None,
    }


def readability(path: Path, input_path: Path | None) -> dict:
    cmd = [
        "python3",
        str(REPO / "tools/curupira/score_readability.py"),
        str(path),
    ]
    if input_path is not None:
        cmd += ["--input", str(input_path)]
    rp = sh(cmd, timeout=60)
    try:
        return json.loads(rp.stdout or "{}")
    except json.JSONDecodeError:
        return {"error": "score_readability falhou", "stderr": (rp.stderr or "")[:300]}


def build_prompt(
    case_id: str, run_id: str, condition: str, work: Path, art: Path, task: str
) -> str:
    if condition == "control":
        return f"""Você é o braço CONTROLE do estudo {case_id} (sem Curupira), execução {run_id}.

Leia a tarefa completa abaixo e o arquivo de trabalho:
- tarefa: {work / "task.md"}
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
    return f"""/curupira-preflight

Você é o braço TRATAMENTO do estudo {case_id} (com Curupira preflight), execução {run_id}.
Siga a skill curupira-preflight.

Arquivos:
- tarefa: {work / "task.md"}
- artefato a editar: {art}

{task}

Regras do braço tratamento:
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


def run_one(case_id: str, condition: str, run_id: str) -> dict:
    case_dir = CASES / case_id
    manifest = json.loads((case_dir / "manifest.json").read_text(encoding="utf-8"))
    task = (case_dir / "task.md").read_text(encoding="utf-8")
    input_rel = manifest.get("input_rel") or "inputs/" + next((case_dir / "inputs").iterdir()).name
    src_input = case_dir / input_rel
    artifact_name = manifest.get("artifact_name") or "procedimento.md"

    work = Path(f"/tmp/cs-pilot/{case_id}-{run_id}-{condition}")
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    art = work / artifact_name
    shutil.copy2(src_input, art)
    shutil.copy2(case_dir / "task.md", work / "task.md")
    for name in ("expected-requirements.md", "acceptance-tests.md"):
        p = case_dir / name
        if p.is_file():
            shutil.copy2(p, work / name)

    out_dir = BASE / condition / f"{case_id}-{run_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    prompt = build_prompt(case_id, run_id, condition, work, art, task)
    (out_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    usage = out_dir / "usage.json"

    cmd = [
        "hermes",
        "-z",
        prompt,
        "--usage-file",
        str(usage),
        "--in",
        str(work),
        "--reasoning",
        "low",
        "--yolo",
    ]
    if condition == "curupira":
        cmd += ["--skills", "curupira-preflight"]

    t0 = time.time()
    timed_out = False
    try:
        proc = sh(cmd)
        stdout, stderr, rc = proc.stdout or "", proc.stderr or "", proc.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
        rc = 124
    wall = round(time.time() - t0, 1)
    (out_dir / "stdout.txt").write_text(stdout, encoding="utf-8")
    (out_dir / "stderr.txt").write_text(stderr, encoding="utf-8")

    art_out = out_dir / artifact_name
    if art.is_file():
        shutil.copy2(art, art_out)

    udata: dict = {}
    if usage.is_file():
        try:
            udata = json.loads(usage.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            udata = {"error": "usage ilegível"}

    result = {
        "schema_version": "hermes-case-study-pilot-run/v1",
        "case_id": case_id,
        "run_id": run_id,
        "condition": condition,
        "case_package_sha256": manifest.get("package_sha256"),
        "wall_seconds": wall,
        "timed_out": timed_out,
        "exit_code": rc,
        "usage": {
            "input_tokens": udata.get("input_tokens"),
            "output_tokens": udata.get("output_tokens"),
            "reasoning_tokens": udata.get("reasoning_tokens"),
            "cache_read_tokens": udata.get("cache_read_tokens"),
            "total_tokens": udata.get("total_tokens"),
            "api_calls": udata.get("api_calls"),
            "model": udata.get("model"),
            "provider": udata.get("provider"),
            "session_id": udata.get("session_id"),
        },
        "artifact_present": art_out.is_file(),
    }
    if art_out.is_file():
        result["residual_lint"] = residual_lint(art_out)
        result["readability"] = readability(art_out, src_input)
    (out_dir / "run.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    u = result["usage"]
    print(
        f"{case_id} {condition} {run_id}: wall={wall}s "
        f"tok_in={u.get('input_tokens')} tok_out={u.get('output_tokens')} "
        f"calls={u.get('api_calls')} residual={result.get('residual_lint', {}).get('findings_n')}"
    )
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cases", nargs="+", default=["case-007", "case-008"], help="casos do piloto")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--skip-existing", action="store_true", help="não reexecutar run já registrado")
    args = ap.parse_args()

    BASE.mkdir(parents=True, exist_ok=True)
    all_results = []
    for case_id in args.cases:
        for condition in ("control", "curupira"):
            for i in range(1, args.runs + 1):
                run_id = f"run-{i:02d}"
                out_dir = BASE / condition / f"{case_id}-{run_id}"
                if args.skip_existing and (out_dir / "run.json").is_file():
                    try:
                        prev = json.loads((out_dir / "run.json").read_text(encoding="utf-8"))
                        all_results.append(prev)
                        print(f"{case_id} {condition} {run_id}: reaproveitado (skip-existing)")
                        continue
                    except (OSError, json.JSONDecodeError):
                        pass
                all_results.append(run_one(case_id, condition, run_id))
    (BASE / "pilot-runs.json").write_text(
        json.dumps(all_results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"\npiloto completo: {len(all_results)} execuções em {BASE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
