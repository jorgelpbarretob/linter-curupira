#!/usr/bin/env python3
"""Create the independently reviewed PARA-001 label proposal."""

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
OUTPUT_DEFAULT = Path("/tmp/ste-lint-product-evidence-round2-labels-para-001-proposal.jsonl")
SCHEMA_VERSION = "ste-lint-product-evidence-labels/v1"
ROUND_ID = "round-2-2026-08-13"
RULE_ID = "STE-I9-PARA-001"
EXPECTED_TOTAL = 144
EXPECTED_LABEL_COUNTS = {
    "violation": 0,
    "non_violation": 86,
    "ambiguous": 0,
    "out_of_scope": 58,
}
PROCEDURAL_DOCUMENT_PATHS = frozenset({"content/en/docs/concepts/instrumentation/code-based.md"})
MANUAL_OUT_OF_SCOPE_CASE_IDS = frozenset(
    {
        "r2-81ee274ea6cca7469a057ca10980cb4d64bbdab9ab2a644f9536110c1a782f0f",
        "r2-bfafa304e056be86cf4f3a29e0e3495eeffa9f2b1a62588a3bb9f0e62bfd9639",
        "r2-10818be3c89e1f5ff2d35bd16ddad7fd3b1c02fc5c7fef322549cd189178a89b",
        "r2-4089fb40732b1a15643a4fb83bbd74ee55dae15b028cc70e412f825da8b8f084",
        "r2-8f1120f913abb42d853a9f1f5da87bb5ab7622abbd3ddaef0754fa95938262d1",
        "r2-f6503d76baa4e06e7d572d39f6dda013b362520ab3a97311b3c581756d110c09",
        "r2-769a893e9525e1fd328f118e920d1385f81cf1f39e5ccec9f0b795b479b6e207",
        "r2-e9e32ef169db813cbd97e20dddff87ef9fcae2e92ecd8193c61f7df17054dd8f",
        "r2-9b4c11b42d2f41698380bd82c1501bd63bc21297441a8a921903e7a7624ac07f",
        "r2-51e4dff61f7f6b5a13e019015b9e73b03713e8afe500ea9c7dbe0276631846cd",
        "r2-401d195e75ee7f7f8d94e3daae3713f3ce8c47e8fdf908239f426f4a067c9a56",
        "r2-7187b1cd6162d35922df9a62c2ffcb89b79f08d33b195a4ea26ded8f0cd7a8dd",
        "r2-22525571b8accd125091ab5d4cd83212e5aa2bc2efc5932cfffe51534baa70c1",
        "r2-3f3d7dc2d51865735283a0234231b6ae08abd0f3b39e6cad35794a823df60226",
        "r2-20e6d85d287b77e93b537c18c6f25a0b5261af3d8b2e39347ac5918a23beedc0",
        "r2-0e37baa1b6fa6366d359aa7889fccdfa581733b8ec0892bf0d4aa0b75aba61a6",
        "r2-93dc4539019c8a35a64118bc92cae6757758d851ac48dccd549bb44cd4a5c180",
        "r2-0b04de784480e7ae86d00a54635de8adad025a05d114f1d7e96cababb28f6330",
        "r2-6829296f8fe475c763af80a7ba5b77b5e2fc5ea0d186146643e7a9877b5642a2",
        "r2-51f8d4eb6120691c52641a4ca53eb50c7a4e36da549558b554a754d5b1be0218",
        "r2-cedcb250cf01d788586be7771e54997bf5e408e439cce5f48f4748fd701f5f3b",
    }
)
LABEL_FIELDS = {
    "schema_version",
    "round_id",
    "inventory_sha256",
    "rule_id",
    "case_id",
    "proposed_label",
}


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


def propose_label(record: dict[str, object]) -> str:
    context = _string(record, "structural_context")
    if context == "uncertain":
        return "ambiguous"
    if context != "visible_prose":
        return "out_of_scope"
    if (
        _string(record, "case_id") in MANUAL_OUT_OF_SCOPE_CASE_IDS
        or _string(record, "path") in PROCEDURAL_DOCUMENT_PATHS
    ):
        return "out_of_scope"

    sentence_count = _integer(record, "candidate_terminal_count")
    if sentence_count == 0:
        return "out_of_scope"
    if 1 <= sentence_count <= 6:
        return "non_violation"
    return "violation"


def propose_labels(
    inventory_records: list[dict[str, object]],
    texts: dict[tuple[str, str], str],
    *,
    expected_total: int = EXPECTED_TOTAL,
) -> list[dict[str, str]]:
    paragraph_records = [record for record in inventory_records if record.get("rule_id") == RULE_ID]
    if len(paragraph_records) != expected_total:
        raise LabelError(
            f"PARA inventory mismatch: expected {expected_total}, got {len(paragraph_records)}"
        )

    labels: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for record in paragraph_records:
        case_id = _string(record, "case_id")
        if case_id in seen_ids:
            raise LabelError(f"duplicate PARA case ID: {case_id}")
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
            raise LabelError(f"invalid paragraph span for {case_id}")
        slice_digest = hashlib.sha256(text[start:end].encode()).hexdigest()
        if slice_digest != _string(record, "slice_sha256"):
            raise LabelError(f"paragraph span digest mismatch for {case_id}")

        labels.append(
            {
                "schema_version": SCHEMA_VERSION,
                "round_id": ROUND_ID,
                "inventory_sha256": INVENTORY_SHA256,
                "rule_id": RULE_ID,
                "case_id": case_id,
                "proposed_label": propose_label(record),
            }
        )

    counts = Counter(record["proposed_label"] for record in labels)
    if expected_total == EXPECTED_TOTAL and any(
        counts[label] != expected for label, expected in EXPECTED_LABEL_COUNTS.items()
    ):
        raise LabelError(
            f"reviewed label-count mismatch: expected {EXPECTED_LABEL_COUNTS}, got {dict(counts)}"
        )
    if expected_total == EXPECTED_TOTAL and not seen_ids >= MANUAL_OUT_OF_SCOPE_CASE_IDS:
        raise LabelError("reviewed out-of-scope case ID is missing from inventory")
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
