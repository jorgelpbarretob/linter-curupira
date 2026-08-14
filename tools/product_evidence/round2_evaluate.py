#!/usr/bin/env python3
"""Execute and score the frozen product-evidence Round 2."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from contextlib import suppress
from pathlib import Path

from ste_lint.domain import RegionKind  # type: ignore[import-untyped]
from ste_lint.parsing import parse_document  # type: ignore[import-untyped]

INVENTORY_PATH = Path("/tmp/ste-lint-product-evidence-round2-inventory-a.jsonl")
INVENTORY_SHA256 = "bebbabe41b28f59e87250e188fe946b237152f9293c8765a06d1322cb3d94c38"
DIAGNOSTICS_OUTPUT = Path("/tmp/ste-lint-product-evidence-round2-diagnostics.jsonl")
METRICS_OUTPUT = Path("/tmp/ste-lint-product-evidence-round2-metrics.json")
LABEL_SPECS = {
    "STE-I9-PUNCT-001": (
        Path("/tmp/ste-lint-product-evidence-round2-labels-punct-001-proposal.jsonl"),
        "b1ce0c8c0b418c9689df1c2de9bf7c24fb9396b9c582608834a2354195913cfa",
    ),
    "STE-I9-LIST-001": (
        Path("/tmp/ste-lint-product-evidence-round2-labels-list-001-proposal.jsonl"),
        "41f9110c7c60846b355ffecf3beadaac5924356a985e33df33c0898105871b10",
    ),
    "STE-I9-PARA-001": (
        Path("/tmp/ste-lint-product-evidence-round2-labels-para-001-proposal.jsonl"),
        "2e3a96a267bacec5bbe1530ff0c3c6ddcc698bd7967b4bb669e912be7507e93c",
    ),
    "STE-I9-SENT-002": (
        Path("/tmp/ste-lint-product-evidence-round2-labels-sent-002-proposal.jsonl"),
        "4276d16d76b7e5a79d91311252d5a9e551b9875edab2f465580b85c393fbca3f",
    ),
    "STE-I9-SENT-001": (
        Path("/tmp/ste-lint-product-evidence-round2-labels-sent-001-proposal.jsonl"),
        "930e5e9324c79cf3546363e324675a7d3274e13b398c7cdfc53871d264b16a8d",
    ),
}
ALL_DOCUMENT_RULES = frozenset({"STE-I9-PUNCT-001", "STE-I9-LIST-001"})
SOURCE_ROOTS = {
    "dapr": Path("/tmp/ste-round2-dapr-docs"),
    "otel": Path("/tmp/ste-round2-opentelemetry-docs"),
}


class EvaluationError(RuntimeError):
    """Raised before or during a non-reproducible evaluation."""


def read_frozen(path: Path, expected_sha256: str) -> bytes:
    payload = path.read_bytes()
    actual_sha256 = hashlib.sha256(payload).hexdigest()
    if actual_sha256 != expected_sha256:
        raise EvaluationError(
            f"digest mismatch for {path}: expected {expected_sha256}, got {actual_sha256}"
        )
    return payload


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


def _unit_span(rule_id: str, record: Mapping[str, object]) -> tuple[object, ...]:
    if rule_id == "STE-I9-LIST-001" and record.get("lead_in_status") != "not_found":
        end = record["lead_in_end_offset"]
        if isinstance(end, int):
            return (record["source_id"], record["path"], end - 1, end)
    return (
        record["source_id"],
        record["path"],
        record["start_offset"],
        record["end_offset"],
    )


def evaluate_rule(
    rule_id: str,
    inventory: Sequence[Mapping[str, object]],
    labels: Mapping[str, str],
    diagnostics: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    emitted_spans = [
        (
            diagnostic["source_id"],
            diagnostic["path"],
            diagnostic["start_offset"],
            diagnostic["end_offset"],
        )
        for diagnostic in diagnostics
    ]
    strict = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    conservative = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    known_spans: set[tuple[object, ...]] = set()
    boundary_false_positives: list[str] = []
    false_negative_case_ids: list[str] = []
    false_positive_case_ids: list[str] = []
    for record in inventory:
        if record.get("rule_id") != rule_id:
            continue
        span = _unit_span(rule_id, record)
        known_spans.add(span)
        emitted = span in emitted_spans
        case_id = str(record["case_id"])
        label = labels[case_id]
        if label == "violation":
            outcome = "tp" if emitted else "fn"
            strict[outcome] += 1
            conservative[outcome] += 1
            if not emitted:
                false_negative_case_ids.append(case_id)
        elif label == "non_violation":
            outcome = "fp" if emitted else "tn"
            strict[outcome] += 1
            conservative[outcome] += 1
            if emitted:
                false_positive_case_ids.append(case_id)
        elif label == "ambiguous":
            conservative["fp" if emitted else "fn"] += 1
        elif label == "out_of_scope" and emitted:
            strict["fp"] += 1
            conservative["fp"] += 1
            boundary_false_positives.append(case_id)
            false_positive_case_ids.append(case_id)

    unmatched_diagnostics = sum(span not in known_spans for span in emitted_spans)
    strict["fp"] += unmatched_diagnostics
    conservative["fp"] += unmatched_diagnostics
    return {
        "strict": strict,
        "conservative": conservative,
        "boundary_false_positives": boundary_false_positives,
        "unmatched_diagnostics": unmatched_diagnostics,
        "false_negative_case_ids": false_negative_case_ids,
        "false_positive_case_ids": false_positive_case_ids,
    }


def _jsonl(payload: bytes, label: str) -> list[dict[str, object]]:
    try:
        records = [json.loads(line) for line in payload.decode().splitlines()]
    except (UnicodeError, json.JSONDecodeError) as error:
        raise EvaluationError(f"invalid {label} JSONL: {error}") from error
    if any(not isinstance(record, dict) for record in records):
        raise EvaluationError(f"{label} JSONL contains a non-object record")
    return records


def _string(record: Mapping[str, object], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str):
        raise EvaluationError(f"field {key} is not a string")
    return value


def _integer(record: Mapping[str, object], key: str) -> int:
    value = record.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise EvaluationError(f"field {key} is not an integer")
    return value


def _write_atomic(path: Path, payload: bytes) -> None:
    temporary_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            temporary_name = handle.name
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except OSError:
        if temporary_name:
            with suppress(OSError):
                Path(temporary_name).unlink(missing_ok=True)
        raise


def _run_cli(command: list[str], *, allow_diagnostics: bool) -> str:
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    allowed = {0, 1} if allow_diagnostics else {0}
    if completed.returncode not in allowed:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise EvaluationError(
            f"CLI failed with exit {completed.returncode}: {' '.join(command)}: {detail}"
        )
    return completed.stdout


def _normalize_cli_output(
    output: str,
    *,
    rule_id: str,
    source_id: str,
    relative_path: str,
    absolute_path: Path,
) -> list[dict[str, object]]:
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as error:
        raise EvaluationError(f"invalid CLI JSON for {rule_id}:{relative_path}: {error}") from error
    if not isinstance(payload, dict) or payload.get("schema_version") != "1.0":
        raise EvaluationError(f"unexpected CLI schema for {rule_id}:{relative_path}")
    raw_diagnostics = payload.get("diagnostics")
    if not isinstance(raw_diagnostics, list):
        raise EvaluationError(f"CLI diagnostics are not an array for {rule_id}:{relative_path}")

    normalized: list[dict[str, object]] = []
    for raw in raw_diagnostics:
        if not isinstance(raw, dict) or raw.get("rule_id") != rule_id:
            raise EvaluationError(f"unexpected diagnostic rule for {rule_id}:{relative_path}")
        location = raw.get("location")
        if not isinstance(location, dict) or location.get("uri") != str(absolute_path):
            raise EvaluationError(f"unexpected diagnostic URI for {rule_id}:{relative_path}")
        normalized.append(
            {
                "rule_id": rule_id,
                "source_id": source_id,
                "path": relative_path,
                "start_offset": _integer(location, "start_offset"),
                "end_offset": _integer(location, "end_offset"),
            }
        )
    return normalized


def _documents_for_rule(
    rule_id: str, inventory: Sequence[Mapping[str, object]]
) -> list[tuple[str, str, str]]:
    candidates = (
        inventory
        if rule_id in ALL_DOCUMENT_RULES
        else [record for record in inventory if record.get("rule_id") == rule_id]
    )
    documents: dict[tuple[str, str], str] = {}
    for record in candidates:
        key = (_string(record, "source_id"), _string(record, "path"))
        text_type = _string(record, "text_type")
        previous = documents.setdefault(key, text_type)
        if previous != text_type:
            raise EvaluationError(f"conflicting text types for {key[0]}:{key[1]}")
    return [(source, path, documents[(source, path)]) for source, path in sorted(documents)]


def _lintable_word_count(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    document = parse_document(str(path), text)
    return sum(
        token.kind is RegionKind.LINTABLE and any(character.isalpha() for character in token.text)
        for token in document.tokens
    )


def _with_metrics(result: dict[str, object], *, lintable_words: int) -> dict[str, object]:
    enriched = dict(result)
    enriched["lintable_words"] = lintable_words
    for scenario in ("strict", "conservative"):
        matrix = result[scenario]
        if not isinstance(matrix, dict):
            raise EvaluationError(f"invalid {scenario} matrix")
        tp = int(matrix["tp"])
        fp = int(matrix["fp"])
        fn = int(matrix["fn"])
        emitted = tp + fp
        positives = tp + fn
        lower, upper = wilson_interval(tp, emitted)
        enriched[f"{scenario}_precision"] = tp / emitted if emitted else None
        enriched[f"{scenario}_recall"] = tp / positives if positives else None
        enriched[f"{scenario}_wilson_95"] = [lower, upper]
    strict = result["strict"]
    if not isinstance(strict, dict):
        raise EvaluationError("invalid strict matrix")
    enriched["strict_fp_per_1000_lintable_words"] = (
        int(strict["fp"]) * 1000 / lintable_words if lintable_words else None
    )
    return enriched


def _canonical_json(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _canonical_jsonl(records: Sequence[Mapping[str, object]]) -> bytes:
    lines = [
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for record in records
    ]
    return ("\n".join(lines) + "\n").encode()


def execute_round(ste_path: Path) -> tuple[dict[str, object], list[dict[str, object]]]:
    inventory = _jsonl(read_frozen(INVENTORY_PATH, INVENTORY_SHA256), "inventory")
    all_labels: dict[str, dict[str, str]] = {}
    for rule_id, (path, expected_hash) in LABEL_SPECS.items():
        records = _jsonl(read_frozen(path, expected_hash), f"{rule_id} labels")
        labels: dict[str, str] = {}
        for record in records:
            if _string(record, "rule_id") != rule_id:
                raise EvaluationError(f"wrong rule in label file for {rule_id}")
            case_id = _string(record, "case_id")
            if case_id in labels:
                raise EvaluationError(f"duplicate label case ID: {case_id}")
            labels[case_id] = _string(record, "proposed_label")
        inventory_ids = {
            _string(record, "case_id") for record in inventory if record.get("rule_id") == rule_id
        }
        if set(labels) != inventory_ids:
            raise EvaluationError(f"label/inventory case-ID mismatch for {rule_id}")
        all_labels[rule_id] = labels

    diagnostics: list[dict[str, object]] = []
    lintable_words: dict[str, dict[str, int]] = {}
    invocation_count = 0
    baseline_replays = 0
    with tempfile.TemporaryDirectory(prefix="ste-round2-baselines-") as temporary:
        baseline_root = Path(temporary)
        for rule_id in LABEL_SPECS:
            lintable_words[rule_id] = {"dapr": 0, "otel": 0}
            for source_id, relative_path, text_type in _documents_for_rule(rule_id, inventory):
                absolute_path = SOURCE_ROOTS[source_id] / relative_path
                lintable_words[rule_id][source_id] += _lintable_word_count(absolute_path)
                command = [
                    str(ste_path),
                    "lint",
                    str(absolute_path),
                    "--format",
                    "json",
                    "--text-type",
                    text_type,
                    "--enable-rule",
                    rule_id,
                ]
                output = _run_cli(command, allow_diagnostics=True)
                invocation_count += 1
                diagnostics.extend(
                    _normalize_cli_output(
                        output,
                        rule_id=rule_id,
                        source_id=source_id,
                        relative_path=relative_path,
                        absolute_path=absolute_path,
                    )
                )

                baseline_path = baseline_root / f"baseline-{invocation_count}.json"
                _run_cli(
                    command + ["--write-baseline", str(baseline_path)], allow_diagnostics=False
                )
                replay_output = _run_cli(
                    command + ["--baseline", str(baseline_path)], allow_diagnostics=False
                )
                replay = _normalize_cli_output(
                    replay_output,
                    rule_id=rule_id,
                    source_id=source_id,
                    relative_path=relative_path,
                    absolute_path=absolute_path,
                )
                if replay:
                    raise EvaluationError(
                        f"baseline replay left diagnostics for {rule_id}:{relative_path}"
                    )
                baseline_replays += 1

    diagnostics.sort(
        key=lambda record: (
            str(record["rule_id"]),
            str(record["source_id"]),
            str(record["path"]),
            _integer(record, "start_offset"),
            _integer(record, "end_offset"),
        )
    )
    metrics_by_rule: dict[str, object] = {}
    for rule_id, labels in all_labels.items():
        rule_inventory = [record for record in inventory if record.get("rule_id") == rule_id]
        rule_diagnostics = [record for record in diagnostics if record.get("rule_id") == rule_id]
        by_source: dict[str, object] = {}
        for source_id in ("dapr", "otel"):
            source_result = evaluate_rule(
                rule_id,
                [record for record in rule_inventory if record.get("source_id") == source_id],
                labels,
                [record for record in rule_diagnostics if record.get("source_id") == source_id],
            )
            by_source[source_id] = _with_metrics(
                source_result, lintable_words=lintable_words[rule_id][source_id]
            )
        aggregate = evaluate_rule(rule_id, rule_inventory, labels, rule_diagnostics)
        aggregate = _with_metrics(aggregate, lintable_words=sum(lintable_words[rule_id].values()))
        aggregate["diagnostic_count"] = len(rule_diagnostics)
        aggregate["label_counts"] = dict(sorted(Counter(labels.values()).items()))
        aggregate["by_source"] = by_source
        metrics_by_rule[rule_id] = aggregate

    metrics: dict[str, object] = {
        "schema_version": "ste-lint-product-evidence-evaluation/v1",
        "round_id": "round-2-2026-08-13",
        "inventory_sha256": INVENTORY_SHA256,
        "label_sha256": {rule: digest for rule, (_, digest) in LABEL_SPECS.items()},
        "isolated_invocations": invocation_count,
        "baseline_replays": baseline_replays,
        "rules": metrics_by_rule,
    }
    return metrics, diagnostics


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ste", type=Path, default=Path(".venv/bin/ste"))
    parser.add_argument("--diagnostics-output", type=Path, default=DIAGNOSTICS_OUTPUT)
    parser.add_argument("--metrics-output", type=Path, default=METRICS_OUTPUT)
    options = parser.parse_args(arguments)
    try:
        metrics, diagnostics = execute_round(options.ste.resolve())
        diagnostics_payload = _canonical_jsonl(diagnostics)
        metrics["diagnostics_sha256"] = hashlib.sha256(diagnostics_payload).hexdigest()
        metrics_payload = _canonical_json(metrics)
        _write_atomic(options.diagnostics_output, diagnostics_payload)
        _write_atomic(options.metrics_output, metrics_payload)
    except (EvaluationError, OSError, UnicodeError) as error:
        print(f"ABORT\t{error}", file=sys.stderr)
        return 2

    print(f"DIAGNOSTICS\t{len(diagnostics)}")
    print(f"DIAGNOSTICS_SHA256\t{hashlib.sha256(diagnostics_payload).hexdigest()}")
    print(f"METRICS_SHA256\t{hashlib.sha256(metrics_payload).hexdigest()}")
    print(f"DIAGNOSTICS_PATH\t{options.diagnostics_output}")
    print(f"METRICS_PATH\t{options.metrics_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
