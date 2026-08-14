#!/usr/bin/env python3
"""Validate completed PONT-001 human decisions without executing product code."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path

import prepare_pont_001_human_review as preparer

DECISION_FIELDS = frozenset(
    {
        "domain",
        "truth",
        "structural_region",
        "expected_diagnostics",
        "rationale",
        "review_status",
        "reviewed_by",
        "reviewer_role",
        "reviewed_on",
        "decision_notes",
    }
)

type ReviewRow = dict[str, str]


class ReviewError(RuntimeError):
    """Raised when the human-review CSV is incomplete or inconsistent."""


def load_review_csv(review_path: Path) -> list[ReviewRow]:
    with review_path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != preparer.CSV_FIELDS:
            raise ReviewError("review CSV header does not match packet v2")
        return list(reader)


def validate_immutable_fields(actual: list[ReviewRow], expected: list[ReviewRow]) -> None:
    if len(actual) != len(expected):
        raise ReviewError(f"review row count mismatch: expected {len(expected)}, got {len(actual)}")

    immutable_fields = [field for field in preparer.CSV_FIELDS if field not in DECISION_FIELDS]
    paired_rows = zip(actual, expected, strict=True)
    for row_number, (actual_row, expected_row) in enumerate(paired_rows, start=2):
        if actual_row.get("case_id") != expected_row["case_id"]:
            raise ReviewError(f"case order mismatch at CSV row {row_number}")
        changed = [
            field
            for field in immutable_fields
            if actual_row.get(field, "") != expected_row.get(field, "")
        ]
        if changed:
            names = ", ".join(changed)
            raise ReviewError(f"immutable fields changed for {expected_row['case_id']}: {names}")


def require_nonblank(row: ReviewRow, fields: tuple[str, ...]) -> None:
    missing = [field for field in fields if not row[field].strip()]
    if missing:
        raise ReviewError(f"{row['case_id']} has blank fields: {', '.join(missing)}")


def validate_review_date(row: ReviewRow) -> None:
    try:
        date.fromisoformat(row["reviewed_on"])
    except ValueError as error:
        raise ReviewError(f"{row['case_id']} has invalid reviewed_on date") from error


def validate_decision(row: ReviewRow) -> None:
    for field in DECISION_FIELDS:
        if row[field] != row[field].strip():
            raise ReviewError(f"{row['case_id']} has surrounding whitespace in {field}")

    status = row["review_status"]
    if status not in {"approved", "rejected"}:
        raise ReviewError(f"{row['case_id']} is not human-reviewed")

    require_nonblank(row, ("reviewed_by", "reviewer_role", "reviewed_on"))
    validate_review_date(row)

    if status == "rejected":
        require_nonblank(row, ("decision_notes",))
        return

    require_nonblank(row, ("domain", "truth", "structural_region", "rationale"))
    truth = row["truth"]
    record_type = row["record_type"]
    if record_type == "literal_semicolon":
        allowed_truths = {"violation", "out_of_scope", "ambiguous"}
    elif record_type == "zero_semicolon_control":
        allowed_truths = {"non_violation"}
    else:
        raise ReviewError(f"{row['case_id']} has unsupported record_type")
    if truth not in allowed_truths:
        raise ReviewError(f"{row['case_id']} has truth inconsistent with record_type")

    expected_by_truth = {
        "violation": "1",
        "non_violation": "0",
        "out_of_scope": "0",
        "ambiguous": "",
    }
    if row["expected_diagnostics"] != expected_by_truth[truth]:
        raise ReviewError(f"{row['case_id']} has expected_diagnostics inconsistent with truth")


def validate_decisions(rows: list[ReviewRow]) -> dict[str, int]:
    if len({row["case_id"] for row in rows}) != len(rows):
        raise ReviewError("review CSV contains duplicate case_id")
    for row in rows:
        validate_decision(row)

    truth_counts = Counter(row["truth"] for row in rows if row["review_status"] == "approved")
    return {
        "case_count": len(rows),
        "approved": sum(row["review_status"] == "approved" for row in rows),
        "rejected": sum(row["review_status"] == "rejected" for row in rows),
        "violation": truth_counts["violation"],
        "non_violation": truth_counts["non_violation"],
        "out_of_scope": truth_counts["out_of_scope"],
        "ambiguous": truth_counts["ambiguous"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", type=Path, help="checkout root for kubernetes/website")
    parser.add_argument("manifest", type=Path, help="frozen label-free holdout manifest")
    parser.add_argument("review_csv", type=Path, help="completed human-review CSV v2")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_root = args.source_root.resolve()
    preparer.verify_source_snapshot(source_root)
    manifest = preparer.load_manifest(args.manifest)
    expected_rows = preparer.build_review_rows(source_root, manifest)
    actual_rows = load_review_csv(args.review_csv)
    validate_immutable_fields(actual_rows, expected_rows)
    summary = validate_decisions(actual_rows)
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
