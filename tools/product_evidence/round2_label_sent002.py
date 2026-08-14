#!/usr/bin/env python3
"""Create the independently reviewed SENT-002 label proposal."""

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
OUTPUT_DEFAULT = Path("/tmp/ste-lint-product-evidence-round2-labels-sent-002-proposal.jsonl")
SCHEMA_VERSION = "ste-lint-product-evidence-labels/v1"
ROUND_ID = "round-2-2026-08-13"
RULE_ID = "STE-I9-SENT-002"
EXPECTED_TOTAL = 329
EXPECTED_LABEL_COUNTS = {
    "violation": 15,
    "non_violation": 166,
    "ambiguous": 4,
    "out_of_scope": 144,
}
LABEL_FIELDS = {
    "schema_version",
    "round_id",
    "inventory_sha256",
    "rule_id",
    "case_id",
    "proposed_label",
}
PROCEDURAL_DOCUMENT_PATHS = frozenset({"content/en/docs/concepts/instrumentation/code-based.md"})

VIOLATION_CASE_IDS = frozenset(
    {
        "r2-073aa5b8d034ed9ae986aea620ba0d3e5142b45b29669db39b4470c213885ba7",
        "r2-93ddd6bb83a9405cafc45cd5618b4ab9ec79436d2b35355bfbc0dc040f2d33d8",
        "r2-01bcd357dc2fa698ae7acc621183dcf7cd7f91fe13cd7ae405f817d925398ee8",
        "r2-b1cd667b679e28e110726e20d4b361cf0c47acf461c4bc5038e71e4babb72032",
        "r2-a9782428c792cfca3f75693297944e6ae98f74b3f8bbeeb508d67932cbca19b8",
        "r2-60e870a2001dfc637abae8f3c255d4a1f3df41364e80fe3a4541aa01864c3265",
        "r2-060388e837e25c16c622a52babca05e1de1187fd2ceacc5f860439a93731992e",
        "r2-8585de6f19377176785617c07d2d5691066ee0ceea58a538f59bab647d328ec4",
        "r2-47604c3678bb5ba7446e48e8b849894c641be082800dbe8bd3ff776e87f2c994",
        "r2-22dd016263cc5202340407b3f21c5d23aa5d20d01d03a574f4c29a4f6c422148",
        "r2-ed389736cd9196db09d41a8c05755453c54eeba03c1db3a53df8d1ce3deeefc4",
        "r2-30ed20827ea31a048269b78bf14a4123f7db366c25f5124e6c1b6266f9c1f741",
        "r2-9c9185b0538fe70e39a34bf3660b2edbb85df09bc9efd0407737e903027245b4",
        "r2-403ded2ca64acbaa7d7031893b7c4eb8f2a81b4836c3f873b342e5e208568916",
        "r2-99696522e30fc352aea658ee3cac8a34c3f96418badaa51f9242cc4c02863c26",
    }
)

AMBIGUOUS_CASE_IDS = frozenset(
    {
        "r2-5fa2a886b5a7a903085fd8198ecbd293939e46e3c7b688d980901b0c27ea274f",
        "r2-084e0845699f76f07a9c96f9109b8637d07d01e36e07d4035293b66164258a17",
        "r2-3fdf4689c91ce1f5087f55b8da19b4d765739a4565f348b14b6cf51d5219d600",
        "r2-8583613e77fb0297ea2e9bb8f09c3819ee4ff52c04fba432f4d2f33c6154d784",
    }
)

MANUAL_OUT_OF_SCOPE_CASE_IDS = frozenset(
    {
        "r2-c71c34390625c9bf66c8a159acf4d32abc0b49a73215f217c380574a24a08148",
        "r2-ab2c8506bd369388e5b5bf9be2716faaf25f4638305845ef9d9c35ebe8dea3ef",
        "r2-9f8c9e662fba0bb04f656052d90db7ae3d1924e65718c6b17518502513f08b09",
        "r2-0bc6c3ec6db7f17f8f76a61bdfe7917d28cdf6e9afba5e1cb40e443869acf85c",
        "r2-c3355b8450f221250d4f93b96cabb8ad2da03278b0acb34c780ca71871cc0aa6",
        "r2-2ee32e775404d86625a03881b93a7460349472ef008007b063d08cdf4124639a",
        "r2-d85db2880d91c948afe421399aa1f43b94eeadab5016b9bc608cb0917398016a",
        "r2-ad7c5c92f6ecd887b101936213661decb04e08bfaff01384c723eba8aa8c4b24",
        "r2-769abfce7e359ac96a87cc6f9312a5a7c75afc90f5bba68e421b36e218b944dd",
        "r2-caee36983adeafad701ec818cf9e259a9c35286a0f759318497e8d1a3557fac4",
        "r2-51fb18ef3433bef8e76b5e95d46fb163024738542ddedbc54358f1e5b1287e1b",
        "r2-222d694514658171574dc696a373791c585fcf18f5ff27ccfc20e0d3a0980d90",
        "r2-a6d7bd56f6bc732fac81130ec18fc6b7b87a1c2b2c0e7037ee987776b9de7d12",
        "r2-257523fa390e3b1bb3e9894bb524bbdf56e81ff7043b1cfcec5679833c8a5a0e",
        "r2-e60067cfb428e4175e05a9e492a8717e26617729b13068948e31396b28cee1da",
        "r2-d2e482d022a3c699198fd8498e24c3dcd3f0b59cc838dd487310a1e83d138bdb",
        "r2-50478296d1489dc42fde067323d915a9c86e2e01974b925b1a8dce95f2189f0d",
        "r2-e60e965cd92818ff19e30a589a90d25d2a648a85a06f336e98b83830a8bfffa4",
        "r2-2f4d173f613fa2659d5c3789f5dfbcc5d0d6f2e89ef7293531e128d6d55f229d",
        "r2-8953efd3101aae14d21604f9fee24461ba1fbfea493426135523bdb3533699a8",
        "r2-1617050a303a4b5175843d9475dc67e73228a78f2d73a496a8d4bc68ee06349e",
        "r2-9c38f2b4a92d6e683e474ec4c0fcec2ad602370fa1da4819bfe679d5cd5d0279",
        "r2-740c293a11561672bf74e0f1e28feb56943eb4de843d705de20e987935d78507",
        "r2-1c4e4035a02a10f41d7a93c0d35a277cfbdc8bea2157ddf2903bea6cb5ddaac3",
        "r2-033a771fdc3b9f91ba88566cebcfcc0d58f039a1cbd0078109a64357c7bb323e",
        "r2-0a20a93104e776e0544885c4609f149ae4befa029248d978fdfdb719cceafaae",
        "r2-5b10e979d592ab1b4b736ec8deca7e8191526189733b292491330544e5ca3d46",
        "r2-b930913ceef64df544899e735f0c38cd9c4180d5d6988a766ae740409e923520",
        "r2-fa3250b3e809987c218d651d21fcc55803119438d7a0a6a5b4ff3554eae32581",
        "r2-aa82d3b78bd5fdbcedbebc9f792170706ed2f26b550056df72797fced8d3a9dc",
        "r2-b9f351d463de1bff7091087eb1529d75c6612b0878e293c2e7e35f4c60f017a2",
        "r2-879c1ed0d8dc125ce14c7cb659e0aa52dfcb0bce8571d8365a932e475819696e",
        "r2-8580453d1606f1f2a10bd84b96cee17b7a04dd3fed873ea8140e218a87ddc4c4",
        "r2-324a35b3b89d2baa5f6b06e1c77ca740fa96653174bb250990af882e9a56e221",
        "r2-1d4c7e15498acfdc4327cdfbbfda7f927563fb49a57474bbd7f37e07553fc927",
        "r2-b6c348cfb53f92b8d4e1232894c218b1b4c43e0daac5550dbce2dd643c242799",
        "r2-dbc41fa504a086162203d9419d6020ca27a2e086c6dbeff6f69234f37677296b",
        "r2-f34b9138831c89b69073a17e0fccdb577c9d46bddf56a7e66da5b20f57d3609c",
        "r2-c9c6e9f39e34e833ca4284398f812062c9149ecef4f9423fc393e21323ad61f8",
        "r2-44a60a5959fd69ca8c08b5d96a2c877997b3cbcdec75c943ed820a5f5c1862f2",
        "r2-5f0331443dda91a3bfde1299c690c5106e0c713273d6d784883a02af79658775",
        "r2-8363c45e2499f415e8b34f1b89ce90fc4f749b9c69fea4d922914695a2b95ec9",
        "r2-364850c0ecf3739bd9ef4094f8e67d55a08d45776e5ab69b2fb74b4ea7fc29f8",
        "r2-b1cd1eb46b673df65c82826ee50b983a61d9a072c4f67ecca770a3c14896d6ed",
        "r2-56496e32bc23de9ede5881a0e3444b11c38ad962f8ad1806be382f3efa57b858",
        "r2-0a0c9d16cb0d17c3178a6e5402124b1bafe396b31312f2d353146582db092300",
        "r2-84646a6d01ddf6de6e90b840733da3d757b1acce8c69d3567c84b84f69b20c68",
        "r2-863e24fd8c79039d9ca3c1255c6c375150d40a95f41c6ffabdd98508b18fa701",
        "r2-6f3ca1bbcb472153e370d0643a7e7f167928fcb8a3391a9037cf6f3ed46145f9",
    }
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


def propose_label(record: dict[str, object]) -> str:
    context = _string(record, "structural_context")
    if context == "uncertain":
        return "ambiguous"
    if context != "visible_prose":
        return "out_of_scope"

    sentence_status = _string(record, "sentence_status")
    if sentence_status not in {"complete", "incomplete"}:
        raise LabelError(f"unknown sentence status: {sentence_status}")
    case_id = _string(record, "case_id")
    if (
        sentence_status == "incomplete"
        or _string(record, "path") in PROCEDURAL_DOCUMENT_PATHS
        or case_id in MANUAL_OUT_OF_SCOPE_CASE_IDS
    ):
        return "out_of_scope"
    if case_id in VIOLATION_CASE_IDS:
        return "violation"
    if case_id in AMBIGUOUS_CASE_IDS:
        return "ambiguous"
    return "non_violation"


def propose_labels(
    inventory_records: list[dict[str, object]],
    texts: dict[tuple[str, str], str],
    *,
    expected_total: int = EXPECTED_TOTAL,
) -> list[dict[str, str]]:
    sentence_records = [record for record in inventory_records if record.get("rule_id") == RULE_ID]
    if len(sentence_records) != expected_total:
        raise LabelError(
            f"SENT-002 inventory mismatch: expected {expected_total}, got {len(sentence_records)}"
        )

    reviewed_sets = (
        VIOLATION_CASE_IDS,
        AMBIGUOUS_CASE_IDS,
        MANUAL_OUT_OF_SCOPE_CASE_IDS,
    )
    if any(
        left & right
        for index, left in enumerate(reviewed_sets)
        for right in reviewed_sets[index + 1 :]
    ):
        raise LabelError("reviewed SENT-002 case-ID sets overlap")

    labels: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for record in sentence_records:
        case_id = _string(record, "case_id")
        if case_id in seen_ids:
            raise LabelError(f"duplicate SENT-002 case ID: {case_id}")
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
            raise LabelError(f"invalid sentence span for {case_id}")
        slice_digest = hashlib.sha256(text[start:end].encode()).hexdigest()
        if slice_digest != _string(record, "slice_sha256"):
            raise LabelError(f"sentence span digest mismatch for {case_id}")

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
    reviewed_case_ids = set().union(*reviewed_sets)
    if expected_total == EXPECTED_TOTAL and not seen_ids >= reviewed_case_ids:
        raise LabelError("reviewed SENT-002 case ID is missing from inventory")
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
