#!/usr/bin/env python3
"""Recomputa independentemente as métricas congeladas de PONT-001."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path

EXECUTION_SHA256 = "eac833da22cf7c6d81a53a273cd067e32bbb734af075d0bb92f5b766db142333"
GROUND_TRUTH_SHA256 = "6cab9e0a4090df19fc5c3cc5a8e93122413160f523e032367ec25849567abab6"
METRICS_SHA256 = "ec38740c65dd2c5d081f8e1080f637264f237e121580fd29c322d1a971144e37"


class AuditError(RuntimeError):
    """Indica que a recomputação não confirma o artefato submetido."""


def read_bytes(path: Path, expected_sha256: str) -> bytes:
    payload = path.read_bytes()
    actual = hashlib.sha256(payload).hexdigest()
    if actual != expected_sha256:
        raise AuditError(f"hash divergente para {path}: {actual}")
    return payload


def wilson_lower(successes: int, total: int) -> float:
    return wilson_interval(successes, total)[0]


def wilson_interval(successes: int, total: int) -> tuple[float, float]:
    if total <= 0:
        return (0.0, 0.0)
    z = 1.959963984540054
    proportion = successes / total
    denominator = 1 + z**2 / total
    center = (proportion + z**2 / (2 * total)) / denominator
    margin = (
        z * math.sqrt(proportion * (1 - proportion) / total + z**2 / (4 * total**2)) / denominator
    )
    return (center - margin, center + margin)


def _metric_block(matrix: Mapping[str, int]) -> dict[str, object]:
    tp, fp, fn = matrix["tp"], matrix["fp"], matrix["fn"]
    emitted = tp + fp
    positives = tp + fn
    return {
        "confusion_matrix": dict(matrix),
        "precision": tp / emitted,
        "precision_wilson_95": list(wilson_interval(tp, emitted)),
        "recall": tp / positives,
        "recall_wilson_95": list(wilson_interval(tp, positives)),
    }


def recompute(
    execution: Mapping[str, object], labels: Sequence[Mapping[str, object]]
) -> dict[str, object]:
    raw_results = execution.get("case_results")
    if not isinstance(raw_results, list) or any(not isinstance(item, dict) for item in raw_results):
        raise AuditError("resultados de execução inválidos")
    results = {_string(item, "case_id"): item for item in raw_results}
    label_map = {_string(item, "case_id"): item for item in labels}
    if len(results) != len(raw_results) or len(label_map) != len(labels):
        raise AuditError("case_id duplicado")
    if set(results) != set(label_map):
        raise AuditError("bijeção falhou")

    matrix = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    false_positives: list[str] = []
    false_negatives: list[str] = []
    region_errors: list[str] = []
    label_counts: Counter[str] = Counter()
    by_domain: dict[str, dict[str, int]] = {}
    for case_id in sorted(results):
        result = results[case_id]
        label = label_map[case_id]
        if _string(result, "source_path") != _string(label, "source_path"):
            raise AuditError(f"path divergente em {case_id}")
        record_type = _string(result, "record_type")
        if record_type == "literal_semicolon":
            emitted = _boolean(result, "emitted_exact")
            if _integer(result, "start_offset") != _integer(label, "unicode_offset"):
                raise AuditError(f"offset divergente em {case_id}")
        elif record_type == "zero_semicolon_control":
            emitted = _integer(result, "diagnostic_count") != 0
        else:
            raise AuditError(f"tipo inesperado em {case_id}")
        truth = _string(label, "truth")
        label_counts[truth] += 1
        if truth == "violation":
            outcome = "tp" if emitted else "fn"
            if not emitted:
                false_negatives.append(case_id)
        elif truth in {"non_violation", "out_of_scope"}:
            outcome = "fp" if emitted else "tn"
            if emitted:
                false_positives.append(case_id)
                if truth == "out_of_scope":
                    region_errors.append(case_id)
        else:
            raise AuditError(f"truth inesperada em {case_id}")
        matrix[outcome] += 1
        domain_matrix = by_domain.setdefault(
            _string(label, "domain"), {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
        )
        domain_matrix[outcome] += 1

    unmatched = _integer(execution, "unmatched_diagnostic_count")
    matrix["fp"] += unmatched
    tp, fp, fn = matrix["tp"], matrix["fp"], matrix["fn"]
    emitted_count = tp + fp
    positives = tp + fn
    precision = tp / emitted_count
    recall = tp / positives
    precision_lower = wilson_lower(tp, emitted_count)
    extra_tp = 0
    while wilson_lower(tp + extra_tp, emitted_count + extra_tp) < 0.95:
        extra_tp += 1
    lintable_words = _integer(execution, "lintable_word_count")
    diagnostic_count = _integer(execution, "diagnostic_count")
    return {
        "matrix": matrix,
        "label_counts": dict(sorted(label_counts.items())),
        "false_positive_case_ids": false_positives,
        "false_negative_case_ids": false_negatives,
        "region_error_case_ids": region_errors,
        "case_count": len(results),
        "diagnostic_count": diagnostic_count,
        "lintable_word_count": lintable_words,
        "unmatched_diagnostic_count": unmatched,
        "offset_error_count": unmatched,
        "region_error_count": len(region_errors),
        "precision": precision,
        "precision_wilson_95": list(wilson_interval(tp, emitted_count)),
        "recall": recall,
        "recall_wilson_95": list(wilson_interval(tp, positives)),
        "span_accuracy": tp / diagnostic_count,
        "fp_per_1000_lintable_words": fp * 1000 / lintable_words,
        "by_domain": {
            domain: _metric_block(domain_matrix)
            for domain, domain_matrix in sorted(by_domain.items())
        },
        "additional_error_free_tp_for_wilson_gate": extra_tp,
        "gate_assessment": {
            "point_precision_gte_0_95": precision >= 0.95,
            "wilson_lower_gte_0_95": precision_lower >= 0.95,
            "zero_known_false_positives": fp == 0,
            "at_least_73_positive_units": positives >= 73,
            "overall_promotion_gate": (
                precision >= 0.95 and precision_lower >= 0.95 and fp == 0 and positives >= 73
            ),
        },
    }


def compare(independent: Mapping[str, object], submitted: Mapping[str, object]) -> None:
    exact_pairs = {
        "matrix": "confusion_matrix",
        "label_counts": "label_counts",
        "false_positive_case_ids": "false_positive_case_ids",
        "false_negative_case_ids": "false_negative_case_ids",
        "region_error_case_ids": "region_error_case_ids",
        "by_domain": "by_domain",
    }
    for independent_key, submitted_key in exact_pairs.items():
        if independent[independent_key] != submitted.get(submitted_key):
            raise AuditError(f"divergência em {submitted_key}")
    float_pairs = {
        "precision": "precision",
        "recall": "recall",
        "fp_per_1000_lintable_words": "fp_per_1000_lintable_words",
        "span_accuracy": "span_accuracy",
    }
    for independent_key, submitted_key in float_pairs.items():
        if not math.isclose(
            _number(independent[independent_key], independent_key),
            _number(submitted.get(submitted_key), submitted_key),
            rel_tol=0.0,
            abs_tol=1e-15,
        ):
            raise AuditError(f"divergência em {submitted_key}")
    integer_pairs = {
        "case_count": "case_count",
        "diagnostic_count": "diagnostic_count",
        "lintable_word_count": "lintable_word_count",
        "unmatched_diagnostic_count": "unmatched_diagnostic_count",
        "offset_error_count": "offset_error_count",
        "region_error_count": "region_error_count",
    }
    for independent_key, submitted_key in integer_pairs.items():
        if independent[independent_key] != submitted.get(submitted_key):
            raise AuditError(f"divergência em {submitted_key}")
    _compare_interval(independent, submitted, "precision_wilson_95", "precisão")
    _compare_interval(independent, submitted, "recall_wilson_95", "recall")


def _compare_interval(
    independent: Mapping[str, object], submitted: Mapping[str, object], key: str, label: str
) -> None:
    expected = independent.get(key)
    actual = submitted.get(key)
    if not isinstance(expected, list) or not isinstance(actual, list) or len(actual) != 2:
        raise AuditError(f"intervalo Wilson de {label} ausente")
    for index in range(2):
        if not math.isclose(
            _number(expected[index], f"{key}[{index}]"),
            _number(actual[index], f"{key}[{index}]"),
            rel_tol=0.0,
            abs_tol=1e-15,
        ):
            raise AuditError(f"divergência no Wilson de {label}")


def canonical_json(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _string(record: Mapping[str, object], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str):
        raise AuditError(f"campo {key} não é string")
    return value


def _integer(record: Mapping[str, object], key: str) -> int:
    value = record.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise AuditError(f"campo {key} não é inteiro")
    return value


def _boolean(record: Mapping[str, object], key: str) -> bool:
    value = record.get(key)
    if not isinstance(value, bool):
        raise AuditError(f"campo {key} não é booleano")
    return value


def _number(value: object, label: str) -> float:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise AuditError(f"campo {label} não é numérico")
    return float(value)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("execution", type=Path)
    parser.add_argument("ground_truth", type=Path)
    parser.add_argument("submitted_metrics", type=Path)
    parser.add_argument("output", type=Path)
    options = parser.parse_args(argv)
    try:
        execution = json.loads(read_bytes(options.execution, EXECUTION_SHA256))
        labels = [
            json.loads(line)
            for line in read_bytes(options.ground_truth, GROUND_TRUTH_SHA256)
            .decode("utf-8")
            .splitlines()
        ]
        submitted = json.loads(read_bytes(options.submitted_metrics, METRICS_SHA256))
        if not isinstance(execution, dict) or not isinstance(submitted, dict):
            raise AuditError("artefato JSON não é objeto")
        if any(not isinstance(label, dict) for label in labels):
            raise AuditError("label JSONL não é objeto")
        independent = recompute(execution, labels)
        compare(independent, submitted)
        report = {
            "verdict": "CONFIRMED",
            "execution_sha256": EXECUTION_SHA256,
            "ground_truth_sha256": GROUND_TRUTH_SHA256,
            "submitted_metrics_sha256": METRICS_SHA256,
            "independent_result": independent,
            "absolute_delta": 0.0,
            "relative_delta": 0.0,
        }
        options.output.write_bytes(canonical_json(report))
    except (AuditError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"REFUTED\t{error}")
        return 2
    print("VERDICT\tCONFIRMED")
    print(f"OUTPUT\t{options.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
