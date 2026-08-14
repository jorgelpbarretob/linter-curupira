#!/usr/bin/env python3
"""Calcula métricas do holdout após a execução cega ter sido selada."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path

RULE_ID = "HERMES-PT-PONT-001"
EXECUTION_SHA256 = "eac833da22cf7c6d81a53a273cd067e32bbb734af075d0bb92f5b766db142333"
GROUND_TRUTH_SHA256 = "6cab9e0a4090df19fc5c3cc5a8e93122413160f523e032367ec25849567abab6"
METRICS_NAME = "pont-001-holdout-metrics-v1.json"
METRICS_SCHEMA = "hermes-holdout-metrics/v1"


class HoldoutScoringError(RuntimeError):
    """Impede score com artefatos divergentes ou unidades incoerentes."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_json(path: Path, expected_sha256: str) -> dict[str, object]:
    payload = path.read_bytes()
    actual = sha256_bytes(payload)
    if actual != expected_sha256:
        raise HoldoutScoringError(
            f"hash divergente para {path}: esperado {expected_sha256}, obtido {actual}"
        )
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as error:
        raise HoldoutScoringError(f"JSON inválido em {path}: {error}") from error
    if not isinstance(value, dict):
        raise HoldoutScoringError(f"objeto JSON esperado em {path}")
    return value


def read_jsonl(path: Path, expected_sha256: str) -> list[dict[str, object]]:
    payload = path.read_bytes()
    actual = sha256_bytes(payload)
    if actual != expected_sha256:
        raise HoldoutScoringError(
            f"hash divergente para {path}: esperado {expected_sha256}, obtido {actual}"
        )
    try:
        records = [json.loads(line) for line in payload.decode("utf-8").splitlines()]
    except (UnicodeError, json.JSONDecodeError) as error:
        raise HoldoutScoringError(f"JSONL inválido em {path}: {error}") from error
    if not records or any(not isinstance(record, dict) for record in records):
        raise HoldoutScoringError(f"registros inválidos em {path}")
    return records


def wilson_interval(successes: int, total: int) -> tuple[float, float] | None:
    if total <= 0:
        return None
    z = 1.959963984540054
    proportion = successes / total
    denominator = 1 + z**2 / total
    center = (proportion + z**2 / (2 * total)) / denominator
    margin = (
        z * math.sqrt(proportion * (1 - proportion) / total + z**2 / (4 * total**2)) / denominator
    )
    return (center - margin, center + margin)


def _metric_block(matrix: Mapping[str, int]) -> dict[str, object]:
    tp = matrix["tp"]
    fp = matrix["fp"]
    fn = matrix["fn"]
    emitted = tp + fp
    positives = tp + fn
    return {
        "confusion_matrix": dict(matrix),
        "precision": tp / emitted if emitted else None,
        "precision_wilson_95": wilson_interval(tp, emitted),
        "recall": tp / positives if positives else None,
        "recall_wilson_95": wilson_interval(tp, positives),
    }


def score(
    execution: Mapping[str, object], labels: Sequence[Mapping[str, object]]
) -> dict[str, object]:
    if execution.get("schema_version") != "hermes-holdout-execution/v1":
        raise HoldoutScoringError("schema de execução inesperado")
    if execution.get("rule_id") != RULE_ID:
        raise HoldoutScoringError("rule_id inesperado na execução")
    raw_results = execution.get("case_results")
    raw_diagnostics = execution.get("diagnostics")
    if not isinstance(raw_results, list) or not isinstance(raw_diagnostics, list):
        raise HoldoutScoringError("execução sem arrays de resultados e diagnósticos")
    if any(not isinstance(result, dict) for result in raw_results):
        raise HoldoutScoringError("resultado de caso inválido")
    results = {_string(result, "case_id"): result for result in raw_results}
    if len(results) != len(raw_results):
        raise HoldoutScoringError("case_id duplicado nos resultados")

    label_map = {_string(label, "case_id"): label for label in labels}
    if len(label_map) != len(labels):
        raise HoldoutScoringError("case_id duplicado nos labels")
    if set(results) != set(label_map):
        raise HoldoutScoringError("bijeção entre labels e resultados falhou")

    matrix = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    by_domain: dict[str, dict[str, int]] = {}
    false_negative_case_ids: list[str] = []
    false_positive_case_ids: list[str] = []
    region_error_case_ids: list[str] = []
    label_counts: Counter[str] = Counter()
    for case_id in sorted(label_map):
        label = label_map[case_id]
        result = results[case_id]
        if _string(label, "rule_id") != RULE_ID:
            raise HoldoutScoringError(f"rule_id inesperado no label {case_id}")
        if _string(label, "source_path") != _string(result, "source_path"):
            raise HoldoutScoringError(f"source_path divergente em {case_id}")
        truth = _string(label, "truth")
        label_counts[truth] += 1
        expected = label.get("expected_diagnostics")
        record_type = _string(result, "record_type")
        if record_type == "literal_semicolon":
            if _integer(label, "unicode_offset") != _integer(result, "start_offset"):
                raise HoldoutScoringError(f"offset divergente em {case_id}")
            emitted = _boolean(result, "emitted_exact")
        elif record_type == "zero_semicolon_control":
            emitted = _integer(result, "diagnostic_count") > 0
        else:
            raise HoldoutScoringError(f"record_type inesperado em {case_id}")

        if truth == "violation":
            if expected != 1:
                raise HoldoutScoringError(f"expectativa incoerente em {case_id}")
            outcome = "tp" if emitted else "fn"
            if not emitted:
                false_negative_case_ids.append(case_id)
        elif truth in {"non_violation", "out_of_scope"}:
            if expected != 0:
                raise HoldoutScoringError(f"expectativa incoerente em {case_id}")
            outcome = "fp" if emitted else "tn"
            if emitted:
                false_positive_case_ids.append(case_id)
                if truth == "out_of_scope":
                    region_error_case_ids.append(case_id)
        else:
            raise HoldoutScoringError(f"truth não categórica em {case_id}: {truth}")
        matrix[outcome] += 1
        domain_matrix = by_domain.setdefault(
            _string(label, "domain"), {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
        )
        domain_matrix[outcome] += 1

    unmatched = _integer(execution, "unmatched_diagnostic_count")
    if unmatched:
        matrix["fp"] += unmatched
    diagnostic_count = _integer(execution, "diagnostic_count")
    lintable_words = _integer(execution, "lintable_word_count")
    metrics = _metric_block(matrix)
    metrics.update(
        {
            "schema_version": METRICS_SCHEMA,
            "rule_id": RULE_ID,
            "execution_sha256": EXECUTION_SHA256,
            "ground_truth_sha256": GROUND_TRUTH_SHA256,
            "detector_sha256": _string(execution, "detector_sha256"),
            "holdout_manifest_sha256": _string(execution, "holdout_manifest_sha256"),
            "case_count": len(results),
            "label_counts": dict(sorted(label_counts.items())),
            "diagnostic_count": diagnostic_count,
            "span_accuracy": matrix["tp"] / diagnostic_count if diagnostic_count else None,
            "lintable_word_count": lintable_words,
            "fp_per_1000_lintable_words": (
                matrix["fp"] * 1000 / lintable_words if lintable_words else None
            ),
            "unmatched_diagnostic_count": unmatched,
            "offset_error_count": unmatched,
            "region_error_count": len(region_error_case_ids),
            "false_negative_case_ids": false_negative_case_ids,
            "false_positive_case_ids": false_positive_case_ids,
            "region_error_case_ids": region_error_case_ids,
            "by_domain": {
                domain: _metric_block(domain_matrix)
                for domain, domain_matrix in sorted(by_domain.items())
            },
        }
    )
    return metrics


def canonical_json(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def materialize(output_dir: Path, metrics: Mapping[str, object]) -> tuple[Path, str]:
    if output_dir.exists():
        raise HoldoutScoringError(f"diretório de saída já existe: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=output_dir.parent))
    try:
        metrics_path = temporary / METRICS_NAME
        payload = canonical_json(metrics)
        metrics_path.write_bytes(payload)
        digest = sha256_bytes(payload)
        (temporary / f"{METRICS_NAME}.sha256").write_text(
            f"{digest}  {METRICS_NAME}\n", encoding="ascii", newline="\n"
        )
        os.replace(temporary, output_dir)
    except BaseException:
        for child in temporary.iterdir():
            child.unlink(missing_ok=True)
        temporary.rmdir()
        raise
    return output_dir / METRICS_NAME, digest


def _string(record: Mapping[str, object], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str):
        raise HoldoutScoringError(f"campo {key} não é string")
    return value


def _integer(record: Mapping[str, object], key: str) -> int:
    value = record.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise HoldoutScoringError(f"campo {key} não é inteiro")
    return value


def _boolean(record: Mapping[str, object], key: str) -> bool:
    value = record.get(key)
    if not isinstance(value, bool):
        raise HoldoutScoringError(f"campo {key} não é booleano")
    return value


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("execution", type=Path)
    parser.add_argument("ground_truth", type=Path)
    parser.add_argument("output_dir", type=Path)
    options = parser.parse_args(argv)
    try:
        execution = read_json(options.execution, EXECUTION_SHA256)
        labels = read_jsonl(options.ground_truth, GROUND_TRUTH_SHA256)
        metrics = score(execution, labels)
        metrics_path, digest = materialize(options.output_dir.resolve(), metrics)
    except (HoldoutScoringError, OSError, UnicodeError) as error:
        print(f"ABORT\t{error}", file=sys.stderr)
        return 2
    print(f"METRICS\t{metrics_path}")
    print(f"METRICS_SHA256\t{digest}")
    print(f"MATRIX\t{metrics['confusion_matrix']}")
    print(f"PRECISION\t{metrics['precision']}")
    print(f"RECALL\t{metrics['recall']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
