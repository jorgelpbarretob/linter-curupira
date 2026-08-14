#!/usr/bin/env python3
"""Create the independently reviewed PUNCT-001 label proposal."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from collections import Counter
from contextlib import suppress
from pathlib import Path

INVENTORY_SHA256 = "bebbabe41b28f59e87250e188fe946b237152f9293c8765a06d1322cb3d94c38"
INVENTORY_DEFAULT = Path("/tmp/ste-lint-product-evidence-round2-inventory-a.jsonl")
OUTPUT_DEFAULT = Path("/tmp/ste-lint-product-evidence-round2-labels-punct-001-proposal.jsonl")
SCHEMA_VERSION = "ste-lint-product-evidence-labels/v1"
ROUND_ID = "round-2-2026-08-13"
RULE_ID = "STE-I9-PUNCT-001"
EXPECTED_TOTAL = 69
LABEL_FIELDS = {
    "schema_version",
    "round_id",
    "inventory_sha256",
    "rule_id",
    "case_id",
    "proposed_label",
}
VIOLATION_CASE_IDS = frozenset(
    {
        "r2-97c71fea7179cc5dededff248457d1361cac721b19954726a89a62457270b679",
        "r2-3a73e87245cb5698424b6f5f7ce772ab4725f5c5ab1152b42427d2d99df91e5c",
    }
)


class LabelError(RuntimeError):
    """Raised when the frozen inventory or reviewed label policy diverges."""


def _string(record: dict[str, object], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str):
        raise LabelError(f"inventory field {key} is not a string")
    return value


def propose_labels(
    inventory_records: list[dict[str, object]], *, expected_total: int = EXPECTED_TOTAL
) -> list[dict[str, str]]:
    punct_records = [record for record in inventory_records if record.get("rule_id") == RULE_ID]
    if len(punct_records) != expected_total:
        raise LabelError(
            f"PUNCT inventory mismatch: expected {expected_total}, got {len(punct_records)}"
        )

    labels: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for record in punct_records:
        case_id = _string(record, "case_id")
        context = _string(record, "structural_context")
        if case_id in seen_ids:
            raise LabelError(f"duplicate PUNCT case ID: {case_id}")
        seen_ids.add(case_id)

        if context == "uncertain":
            raise LabelError(f"uncertain case requires adjudication: {case_id}")
        if context == "visible_prose":
            if case_id not in VIOLATION_CASE_IDS:
                raise LabelError(f"visible case not in reviewed violation allowlist: {case_id}")
            proposed_label = "violation"
        elif context == "markup_or_code":
            if case_id in VIOLATION_CASE_IDS:
                raise LabelError(f"reviewed violation was reclassified as markup: {case_id}")
            proposed_label = "non_violation"
        else:
            raise LabelError(f"unsupported structural context {context}: {case_id}")

        labels.append(
            {
                "schema_version": SCHEMA_VERSION,
                "round_id": ROUND_ID,
                "inventory_sha256": INVENTORY_SHA256,
                "rule_id": RULE_ID,
                "case_id": case_id,
                "proposed_label": proposed_label,
            }
        )

    if expected_total == EXPECTED_TOTAL and not seen_ids >= VIOLATION_CASE_IDS:
        missing = sorted(VIOLATION_CASE_IDS - seen_ids)
        raise LabelError(f"reviewed violation case IDs missing from inventory: {missing}")
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
    options = parser.parse_args(arguments)

    try:
        inventory_bytes = options.inventory.read_bytes()
        actual_hash = hashlib.sha256(inventory_bytes).hexdigest()
        if actual_hash != INVENTORY_SHA256:
            raise LabelError(
                f"inventory digest mismatch: expected {INVENTORY_SHA256}, got {actual_hash}"
            )
        inventory = [json.loads(line) for line in inventory_bytes.decode().splitlines()]
        labels = propose_labels(inventory)
        payload = canonical_bytes(labels)
        _write_atomic(options.output, payload)
    except (OSError, UnicodeError, json.JSONDecodeError, LabelError) as error:
        print(f"ABORT\t{error}", file=sys.stderr)
        return 2

    counts = Counter(record["proposed_label"] for record in labels)
    print(f"LABELS\t{len(labels)}")
    print(f"VIOLATION\t{counts['violation']}")
    print(f"NON_VIOLATION\t{counts['non_violation']}")
    print(f"SHA256\t{hashlib.sha256(payload).hexdigest()}")
    print(f"PATH\t{options.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
