#!/usr/bin/env python3
"""Pré-registro de poder estatístico para o estudo Hermes × Curupira.

Calcula o tamanho mínimo de amostra pareada para os três desfechos do
protocolo v1 e emite um envelope JSON versionado. Sem dependências além
da biblioteca padrão; usa scipy/statsmodels quando disponíveis.

Uso:
  python3 tools/curupira/power_analysis_preregister.py \
    --n-tasks 16 --output docs/hermes-case-study/prereg-v1.json
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

SCHEMA = "curupira-case-study-prereg/v1"
ALPHA = 0.05
POWER = 0.80


def _z(p: float) -> float:
    try:
        from scipy.stats import norm

        return float(norm.ppf(p))
    except ImportError as err:
        # aproximação de Acklam inversa seria melhor, mas basta para registro
        raise SystemExit("scipy necessária para calcular o pré-registro") from err


def mde_paired_t(n: int, alpha: float = ALPHA, power: float = POWER) -> float:
    """Efeito mínimo detectável (d_z) em teste t pareado."""
    try:
        from statsmodels.stats.power import TTestPower

        return float(
            TTestPower().solve_power(
                effect_size=None,
                nobs=n,
                alpha=alpha,
                power=power,
                alternative="two-sided",
            )
        )
    except ImportError:
        za2 = _z(1 - alpha / 2)
        zb = _z(power)
        return (za2 + zb) / math.sqrt(n)


def mcnemar_n(p01: float, p10: float, alpha: float = ALPHA, power: float = POWER) -> int | None:
    """n de pares para McNemar dado p01 (só controle falha) e p10 (só tratamento falha)."""
    if p01 <= p10:
        return None
    za2 = _z(1 - alpha / 2)
    zb = _z(power)
    pd = p01 + p10
    delta = p01 - p10
    n = ((za2 * math.sqrt(pd) + zb * math.sqrt(max(pd - delta**2, 1e-9))) / delta) ** 2
    return math.ceil(n)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n-tasks", type=int, default=16)
    ap.add_argument(
        "--residual-p01",
        type=float,
        default=0.63,
        help="prob controle falha e tratamento passa (achados residuais)",
    )
    ap.add_argument("--residual-p10", type=float, default=0.02)
    ap.add_argument("--accept-p01", type=float, default=0.25)
    ap.add_argument("--accept-p10", type=float, default=0.06)
    ap.add_argument("--output", type=Path, default=None)
    args = ap.parse_args()

    payload = {
        "schema_version": SCHEMA,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "alpha": ALPHA,
        "power": POWER,
        "n_tasks_proposed": args.n_tasks,
        "rubric_mde_dz": round(mde_paired_t(args.n_tasks), 3),
        "accept_mcnemar_pairs": mcnemar_n(args.accept_p01, args.accept_p10),
        "accept_premises": {"p01": args.accept_p01, "p10": args.accept_p10},
        "residual_mcnemar_pairs": mcnemar_n(args.residual_p01, args.residual_p10),
        "residual_premises": {"p01": args.residual_p01, "p10": args.residual_p10},
        "primary_outcome": "residual_findings_enabled_rules",
        "secondary_correction": "holm",
        "analysis_unit": "task (median over runs)",
    }
    out = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(out, encoding="utf-8", newline="\n")
        print(f"pré-registro escrito em {args.output}")
    else:
        print(out, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
