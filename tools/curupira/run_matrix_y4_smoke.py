#!/usr/bin/env python3
"""Matriz Y=4 OpenRouter × cases × A/B (control vs CLI-min).

Smoke default: case-007/008/012 × 4 models × 2 arms = 24 runs.
Rota: hermes -z --usage-file --in WORK --reasoning low --yolo
      -m MODEL --provider openrouter
Tratamento = CLI-min (sem skill preload).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path("/home/jorge/dev/linter-curupira")
CASES = REPO / "cases"
BASE = REPO / "artifacts/hermes-case-study/matrix-y4-smoke"
RULE = "CURUPIRA-PT-PONT-001"
TIMEOUT_S = 480
BRT = timezone(timedelta(hours=-3))

DEFAULT_Y = [
    "qwen/qwen3.8-27b",
    "nvidia/nemotron-3.5-lightning:free",
    "meta/muse-glimmer-30b",
    "thinkingmachines/inkling-small",
]
DEFAULT_CASES = ["case-007", "case-008", "case-012"]


def sh(cmd: list[str], timeout: int = TIMEOUT_S) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)


def slug_model(model: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", model)


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
    cmd = ["python3", str(REPO / "tools/curupira/score_readability.py"), str(path)]
    if input_path is not None:
        cmd += ["--input", str(input_path)]
    rp = sh(cmd, timeout=60)
    try:
        return json.loads(rp.stdout or "{}")
    except json.JSONDecodeError:
        return {"error": "score_readability falhou", "stderr": (rp.stderr or "")[:300]}


def lint_invoked_from_logs(stdout: str, stderr: str) -> bool:
    blob = (stdout or "") + "\n" + (stderr or "")
    if re.search(r"curupira\s+lint", blob):
        return True
    # agent final summary often only says "lint exit 0"
    if re.search(r"\blint\s+exit\s*0\b", blob, re.I):
        return True
    if re.search(r"\"exit_code\"\s*:\s*0", blob) and "CURUPIRA" in blob:
        return True
    return False


def build_prompt(
    case_id: str, run_id: str, condition: str, work: Path, art: Path, task: str, model: str
) -> str:
    if condition == "control":
        return f"""Você é o braço CONTROLE do estudo {case_id} (sem Curupira), execução {run_id}.
Modelo executor: {model}

Leia a tarefa e o arquivo de trabalho:
- tarefa: {work / "task.md"}
- artefato a editar: {art}

{task}

Regras do braço controle:
- NÃO chame curupira nem skill de lint.
- NÃO envie documento a APIs externas além das tools do agent.
- Preserve identificadores técnicos exigidos na tarefa.
- Priorize legibilidade para o usuário final e texto enxuto.
- Sobrescreva somente: {art}
- Ao terminar: imprima path, chars do arquivo e resumo de 1 linha.
"""
    # CLI-min treatment
    return f"""Você é o braço TRATAMENTO do estudo {case_id} (Curupira CLI-min), execução {run_id}.
Modelo executor: {model}

Arquivos:
- tarefa: {work / "task.md"}
- artefato a editar: {art}

{task}

Regras do braço tratamento (CLI-min):
- NÃO carregue skill longa de Curupira.
- Antes de declarar pronto, rode exatamente:
  curupira lint {art} --enable-rule CURUPIRA-PT-PONT-001 --format json
- Exit 1 = incompleto: corrija e repita (máx 2 ciclos). Só sucesso com exit 0.
- Sem semantic-review.
- Preserve identificadores técnicos exigidos na tarefa.
- Otimize para o usuário: frases curtas, passos explícitos, sem muro de texto.
- Prefira enxugar prosa inútil sem apagar fatos.
- Sobrescreva somente: {art}
- Ao terminar: path, exit do lint, chars do arquivo, resumo 1 linha.
"""


def anomaly_flags(usage: dict, source: str) -> list[dict]:
    flags = []
    tin = int(usage.get("input_tokens") or 0)
    tout = int(usage.get("output_tokens") or 0)
    tot = int(usage.get("total_tokens") or 0)
    if tin == 0 and tout == 0 and tot == 0:
        flags.append({"code": "tokens_all_zero", "evidence": source})
    if tot > 0 and tin + tout > 0 and tot > 3 * (tin + tout):
        flags.append(
            {
                "code": "total_much_greater_than_in_plus_out",
                "evidence": f"total={tot} in+out={tin+tout}",
            }
        )
    if not usage.get("model"):
        flags.append({"code": "model_missing_in_usage", "evidence": source})
    return flags


def run_one(case_id: str, condition: str, run_id: str, model: str, provider: str) -> dict:
    case_dir = CASES / case_id
    manifest = json.loads((case_dir / "manifest.json").read_text(encoding="utf-8"))
    task = (case_dir / "task.md").read_text(encoding="utf-8")
    inputs = list((case_dir / "inputs").iterdir()) if (case_dir / "inputs").is_dir() else []
    input_rel = manifest.get("input_rel") or (
        "inputs/" + inputs[0].name if inputs else "inputs/procedimento.md"
    )
    src_input = case_dir / input_rel
    artifact_name = (
        manifest.get("artifact_name")
        or (case_dir / "artifact-name.txt").read_text(encoding="utf-8").strip()
        or "procedimento.md"
    )

    mslug = slug_model(model)
    work = Path(f"/tmp/cs-y4/{mslug}/{case_id}-{run_id}-{condition}")
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

    out_dir = BASE / mslug / condition / f"{case_id}-{run_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    prompt = build_prompt(case_id, run_id, condition, work, art, task, model)
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
        "-m",
        model,
        "--provider",
        provider,
    ]

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
    token_source = "usage-file"
    if usage.is_file():
        try:
            udata = json.loads(usage.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            udata = {"error": "usage ilegível"}
            token_source = "usage-file-corrupt"
    else:
        token_source = "usage-file-missing"

    usage_norm = {
        "input_tokens": udata.get("input_tokens"),
        "output_tokens": udata.get("output_tokens"),
        "reasoning_tokens": udata.get("reasoning_tokens"),
        "cache_read_tokens": udata.get("cache_read_tokens"),
        "total_tokens": udata.get("total_tokens"),
        "api_calls": udata.get("api_calls"),
        "model": udata.get("model") or model,
        "provider": udata.get("provider") or provider,
        "session_id": udata.get("session_id"),
    }
    flags = anomaly_flags(usage_norm, token_source)
    if token_source != "usage-file":
        flags.append({"code": token_source, "evidence": str(usage)})

    lint_invoked = lint_invoked_from_logs(stdout, stderr) if condition == "cli" else False
    residual = residual_lint(art_out) if art_out.is_file() else {"exit_code": None, "findings_n": None}
    if condition == "cli" and not lint_invoked:
        flags.append({"code": "cli_lint_not_observed_in_logs", "evidence": "stdout/stderr"})

    result = {
        "schema_version": "hermes-case-study-matrix-y4-run/v1",
        "case_id": case_id,
        "run_id": run_id,
        "condition": condition,
        "model_requested": model,
        "provider_requested": provider,
        "case_package_sha256": manifest.get("package_sha256"),
        "wall_seconds": wall,
        "timed_out": timed_out,
        "exit_code": rc,
        "token_source": token_source,
        "usage": usage_norm,
        "artifact_present": art_out.is_file(),
        "gate": {
            "treatment_lint_invoked": lint_invoked if condition == "cli" else None,
            "residual_n": residual.get("findings_n"),
            "residual_zero": residual.get("findings_n") == 0,
            "operational_pass": bool(
                condition == "cli" and lint_invoked and residual.get("findings_n") == 0
            )
            if condition == "cli"
            else None,
        },
        "integrity_flags": flags,
        "artifact_path": str(art_out) if art_out.is_file() else None,
    }
    if art_out.is_file():
        result["residual_lint"] = residual
        result["readability"] = readability(art_out, src_input)
    (out_dir / "run.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    u = result["usage"]
    print(
        f"{model} | {case_id} {condition} {run_id}: wall={wall}s "
        f"in={u.get('input_tokens')} out={u.get('output_tokens')} tot={u.get('total_tokens')} "
        f"residual={residual.get('findings_n')} lint_inv={lint_invoked if condition=='cli' else '-'}",
        flush=True,
    )
    return result


def pair_key(r: dict) -> tuple:
    return (r["model_requested"], r["case_id"], r["run_id"])


def build_pairs(runs: list[dict]) -> list[dict]:
    by: dict[tuple, dict] = {}
    for r in runs:
        by.setdefault(pair_key(r), {})[r["condition"]] = r
    pairs = []
    for key, arms in sorted(by.items()):
        model, case_id, run_id = key
        c = arms.get("control")
        t = arms.get("cli")
        if not c or not t:
            pairs.append(
                {
                    "model": model,
                    "case_id": case_id,
                    "run_id": run_id,
                    "incomplete": True,
                    "arms": list(arms),
                }
            )
            continue
        cu, tu = c["usage"], t["usage"]
        din = int(tu.get("input_tokens") or 0) - int(cu.get("input_tokens") or 0)
        dout = int(tu.get("output_tokens") or 0) - int(cu.get("output_tokens") or 0)
        dtot = int(tu.get("total_tokens") or 0) - int(cu.get("total_tokens") or 0)
        pairs.append(
            {
                "model": model,
                "case_id": case_id,
                "run_id": run_id,
                "executor": {
                    "control": {
                        "input_tokens": cu.get("input_tokens"),
                        "output_tokens": cu.get("output_tokens"),
                        "total_tokens": cu.get("total_tokens"),
                    },
                    "cli": {
                        "input_tokens": tu.get("input_tokens"),
                        "output_tokens": tu.get("output_tokens"),
                        "total_tokens": tu.get("total_tokens"),
                    },
                    "delta_cli_minus_control": {
                        "input_tokens": din,
                        "output_tokens": dout,
                        "total_tokens": dtot,
                    },
                    "token_source_control": c.get("token_source"),
                    "token_source_cli": t.get("token_source"),
                },
                "gate": t.get("gate"),
                "residual_control": (c.get("residual_lint") or {}).get("findings_n"),
                "residual_cli": (t.get("residual_lint") or {}).get("findings_n"),
                "integrity_flags": (c.get("integrity_flags") or []) + (t.get("integrity_flags") or []),
                "artifact_control": c.get("artifact_path"),
                "artifact_cli": t.get("artifact_path"),
                "readability_control": c.get("readability"),
                "readability_cli": t.get("readability"),
            }
        )
    return pairs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cases", nargs="+", default=DEFAULT_CASES)
    ap.add_argument("--models", nargs="+", default=DEFAULT_Y)
    ap.add_argument("--run-id", default="run-01")
    ap.add_argument("--provider", default="openrouter")
    ap.add_argument("--skip-existing", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="max cells (case×model×arm)")
    args = ap.parse_args()

    BASE.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    cells = 0
    for model in args.models:
        for case_id in args.cases:
            for condition in ("control", "cli"):
                if args.limit and cells >= args.limit:
                    break
                mslug = slug_model(model)
                out_dir = BASE / mslug / condition / f"{case_id}-{args.run_id}"
                if args.skip_existing and (out_dir / "run.json").is_file():
                    try:
                        prev = json.loads((out_dir / "run.json").read_text(encoding="utf-8"))
                        results.append(prev)
                        print(f"skip {model} {case_id} {condition}", flush=True)
                        cells += 1
                        continue
                    except (OSError, json.JSONDecodeError):
                        pass
                results.append(
                    run_one(case_id, condition, args.run_id, model, args.provider)
                )
                cells += 1
            if args.limit and cells >= args.limit:
                break
        if args.limit and cells >= args.limit:
            break

    pairs = build_pairs(results)
    summary = {
        "schema_version": "hermes-case-study-matrix-y4-smoke/v1",
        "generated_at": datetime.now(BRT).isoformat(),
        "models": args.models,
        "cases": args.cases,
        "run_id": args.run_id,
        "provider": args.provider,
        "treatment": "cli-min",
        "n_runs": len(results),
        "n_pairs": sum(1 for p in pairs if not p.get("incomplete")),
        "runs": results,
        "pairs": pairs,
    }
    (BASE / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"\nSMOKE DONE runs={len(results)} pairs_complete={summary['n_pairs']} base={BASE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
