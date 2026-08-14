#!/usr/bin/env python3
"""Create the independently reviewed LIST-001 label proposal."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from collections import Counter
from contextlib import suppress
from pathlib import Path

INVENTORY_SHA256 = "bebbabe41b28f59e87250e188fe946b237152f9293c8765a06d1322cb3d94c38"
INVENTORY_DEFAULT = Path("/tmp/ste-lint-product-evidence-round2-inventory-a.jsonl")
OUTPUT_DEFAULT = Path("/tmp/ste-lint-product-evidence-round2-labels-list-001-proposal.jsonl")
SCHEMA_VERSION = "ste-lint-product-evidence-labels/v1"
ROUND_ID = "round-2-2026-08-13"
RULE_ID = "STE-I9-LIST-001"
EXPECTED_TOTAL = 73
LABEL_FIELDS = {
    "schema_version",
    "round_id",
    "inventory_sha256",
    "rule_id",
    "case_id",
    "proposed_label",
}
_CLEAR_ASSOCIATION = re.compile(
    r"\bthese\s+(?P<head>[^\W\d_]+(?:-[^\W\d_]+)*)(?P<terminal>[.:])\s*$",
    re.IGNORECASE,
)


class LabelError(RuntimeError):
    """Raised when the frozen inventory or source span diverges."""


def _string(record: dict[str, object], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str):
        raise LabelError(f"inventory field {key} is not a string")
    return value


def _integer(record: dict[str, object], key: str) -> int:
    value = record.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise LabelError(f"inventory field {key} is not an integer")
    return value


def propose_label(record: dict[str, object], lead_in: str) -> str:
    status = _string(record, "lead_in_status")
    if status == "uncertain":
        return "ambiguous"
    if status != "found":
        return "out_of_scope"
    blockers = record.get("blockers")
    if not isinstance(blockers, list) or blockers:
        return "out_of_scope"
    if _integer(record, "blank_lines_before") not in {0, 1}:
        return "out_of_scope"
    if not 0 <= _integer(record, "indentation") <= 3:
        return "out_of_scope"
    if _integer(record, "peer_count") < 2:
        return "out_of_scope"

    final_line = lead_in.splitlines()[-1] if lead_in.splitlines() else ""
    match = _CLEAR_ASSOCIATION.search(final_line)
    if not match or not match.group("head").lower().endswith("s"):
        return "out_of_scope"
    return "violation" if match.group("terminal") == "." else "non_violation"


def propose_labels(
    inventory_records: list[dict[str, object]],
    texts: dict[tuple[str, str], str],
    *,
    expected_total: int = EXPECTED_TOTAL,
) -> list[dict[str, str]]:
    list_records = [record for record in inventory_records if record.get("rule_id") == RULE_ID]
    if len(list_records) != expected_total:
        raise LabelError(
            f"LIST inventory mismatch: expected {expected_total}, got {len(list_records)}"
        )

    labels: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for record in list_records:
        case_id = _string(record, "case_id")
        if case_id in seen_ids:
            raise LabelError(f"duplicate LIST case ID: {case_id}")
        seen_ids.add(case_id)

        source_id = _string(record, "source_id")
        path = _string(record, "path")
        try:
            text = texts[(source_id, path)]
        except KeyError as error:
            raise LabelError(f"source text missing for {source_id}:{path}") from error
        start = _integer(record, "start_offset")
        end = _integer(record, "end_offset")
        if not 0 <= start < end <= len(text):
            raise LabelError(f"invalid list span for {case_id}")
        slice_digest = hashlib.sha256(text[start:end].encode()).hexdigest()
        if slice_digest != _string(record, "slice_sha256"):
            raise LabelError(f"list span digest mismatch for {case_id}")

        lead_start = _integer(record, "lead_in_start_offset")
        lead_end = _integer(record, "lead_in_end_offset")
        if _string(record, "lead_in_status") == "not_found":
            lead_in = ""
        else:
            if not 0 <= lead_start < lead_end <= len(text):
                raise LabelError(f"invalid lead-in span for {case_id}")
            lead_in = text[lead_start:lead_end]
            lead_digest = hashlib.sha256(lead_in.encode()).hexdigest()
            if lead_digest != _string(record, "lead_in_slice_sha256"):
                raise LabelError(f"lead-in span digest mismatch for {case_id}")

        labels.append(
            {
                "schema_version": SCHEMA_VERSION,
                "round_id": ROUND_ID,
                "inventory_sha256": INVENTORY_SHA256,
                "rule_id": RULE_ID,
                "case_id": case_id,
                "proposed_label": propose_label(record, lead_in),
            }
        )
    return labels


def canonical_bytes(records: list[dict[str, str]]) -> bytes:
    if any(set(record) != LABEL_FIELDS for record in records):
        raise LabelError("label schema mismatch")
    lines = [
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for record in records
    ]
    return ("\n".join(lines) + "\n").encode()


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


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=INVENTORY_DEFAULT)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--dapr-root", type=Path, default=Path("/tmp/ste-round2-dapr-docs"))
    parser.add_argument(
        "--otel-root", type=Path, default=Path("/tmp/ste-round2-opentelemetry-docs")
    )
    options = parser.parse_args(arguments)

    try:
        inventory_bytes = options.inventory.read_bytes()
        actual_hash = hashlib.sha256(inventory_bytes).hexdigest()
        if actual_hash != INVENTORY_SHA256:
            raise LabelError(
                f"inventory digest mismatch: expected {INVENTORY_SHA256}, got {actual_hash}"
            )
        inventory = [json.loads(line) for line in inventory_bytes.decode().splitlines()]
        texts: dict[tuple[str, str], str] = {}
        roots = {"dapr": options.dapr_root, "otel": options.otel_root}
        for record in inventory:
            if record.get("rule_id") != RULE_ID:
                continue
            source_id = _string(record, "source_id")
            path = _string(record, "path")
            texts[(source_id, path)] = (roots[source_id] / path).read_text(encoding="utf-8")
        labels = propose_labels(inventory, texts)
        payload = canonical_bytes(labels)
        _write_atomic(options.output, payload)
    except (OSError, UnicodeError, json.JSONDecodeError, LabelError, KeyError) as error:
        print(f"ABORT\t{error}", file=sys.stderr)
        return 2

    counts = Counter(record["proposed_label"] for record in labels)
    print(f"LABELS\t{len(labels)}")
    for label in ("violation", "non_violation", "ambiguous", "out_of_scope"):
        print(f"{label.upper()}\t{counts[label]}")
    print(f"SHA256\t{hashlib.sha256(payload).hexdigest()}")
    print(f"PATH\t{options.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
