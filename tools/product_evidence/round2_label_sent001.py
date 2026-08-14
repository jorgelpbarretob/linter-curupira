#!/usr/bin/env python3
"""Create the independently reviewed SENT-001 label proposal."""

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
OUTPUT_DEFAULT = Path("/tmp/ste-lint-product-evidence-round2-labels-sent-001-proposal.jsonl")
SCHEMA_VERSION = "ste-lint-product-evidence-labels/v1"
ROUND_ID = "round-2-2026-08-13"
RULE_ID = "STE-I9-SENT-001"
EXPECTED_TOTAL = 558
EXPECTED_LABEL_COUNTS = {
    "violation": 40,
    "non_violation": 200,
    "ambiguous": 8,
    "out_of_scope": 310,
}
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
        "r2-0a8c926c5e654f16b77bb51552aa96d5b6edd354c6d4549e4ee1ec269be23ab0",
        "r2-11ab128e611033eacca16f8d636b3a0119d7b7c9ff5c4f6243ea863425271eac",
        "r2-11ed4e4e93b34e419abd35e8d2e69c7cb57e34aa0a481deff8ad1abf95311943",
        "r2-15f164257c5132a7aeb0061b25fd34a8fcd5b4ee6aa37a799ce5bba51ac61c7c",
        "r2-187f81be4b449987ca460c9a91610cbaef6110dcee47e2254bca2bdc0507385b",
        "r2-1c6cfb507805cd003c62ba61eaed6dd39ff69c2ce1583acd191420027b8181a0",
        "r2-1c939643f3a259991f2b9fc7fa2b08faf469673d2b5f263585e02e9817f4a1e6",
        "r2-1de8666c1de6241409479730c29f8d6451e64035f3abef8783b2c1a12b1a8f3e",
        "r2-216794529b4cdb2e5fdeab13c4b943b953038109c392bf954f18999794d76c33",
        "r2-28adafbe1b51ca6e17a2125aac0f5b9fd0a8a13454b293a03caf7c7100f4e41c",
        "r2-35f5a1fabe2bcaa3c63ba4b5347263e6543f84832e7fca763c3bf3d6bb0d1a4b",
        "r2-3a0af0a9460644fe3c9080f3d4c0d269eda249708b4058aabb899385f8e72b4b",
        "r2-3e6f4fa3ddbdfac95c36f17cb083d24c197abee01bd87db347db85c2b1f7cbc7",
        "r2-42b26bd2085a75fbe54f199337edc536965f1459057bd9d6afff803932872b26",
        "r2-4b319901e245700a8051de068bfdc293627a3d2b7d346684e9c092c1c076d6d3",
        "r2-4f931c531c8c1fd19b4cc563b47231d9240981df98367213a58feed10ab398ba",
        "r2-718188b52e8697da1f109a29cc51802fa418e766c41af814c55bfa88aeec9c7b",
        "r2-7b1ba3628ad7faaf39e0b533475ae626e2c69894564404c493678185886d87fb",
        "r2-7eec65875cea3eaa2f04bbac4f8472a90b2dbc85e8cc33889e7b365d1d859186",
        "r2-891a1e82511ba7b3ec7bc07dff6a22b59e49b7b157a0cacfce1f8124596c1175",
        "r2-8a248423a519d173fda1014ba09bca95eb787585e4feba38ceb85d105e3b25db",
        "r2-8a2eb52a47cf87b6658dc6334972847b6df2848ed9ebd69132947ac19fde20ae",
        "r2-9c5b99d81effc4f8c4b1454611cd4ede2f7d95fa475a7d6f1212b0ec498de92e",
        "r2-9cb2f7800c3e22b746466aa7203d22a0e4544d796b5dbd1e181407087a0d8543",
        "r2-9da75d09aa2da586010ceacd23ef164e6cf3c72ab00a0873df7006425d7d6b39",
        "r2-9eecdce0284af2d9615fc333c780945eb8d870c5f65cd7167acc5a5f481135a2",
        "r2-b00820c0f47389d330119983e94c59246bfe82081c0081c427dd3bef70ba7c24",
        "r2-b03ec89b813a328673239cd836111ac66b5a0da645c476927dc77a24423d5b67",
        "r2-b4ea068960333fba662a07de64422f5ddeaeb3e5ab7b3ed9c1abc6e577ebb37a",
        "r2-be8bc253f400f22239a95c10672ce28c42bf774623c772b93ea78d9d509f0bc7",
        "r2-ca23eb9e25963c4a7d9a10c74d3880b7d4fcade45caae24647aba1184b645c91",
        "r2-cc90f2a400049f493400fa5e631e084030be80e120e90644cfad08f59bd087ba",
        "r2-cea47d1ef05039de8e13ec93eb81b6bacb20be6c3de0aaa5a4cd50efc5c22e1a",
        "r2-d1f9a93a7a58f260a29d467e73a2823ad4498f36f63acb07b067f3e40d298eab",
        "r2-d82c32a0caadec376fa9de68996165a88f893fbadb112b7c02caac3d4e3faca8",
        "r2-e0323f998a2ebd4701dbe3203ba14b258cb0d8d5c526279f7be01ce097d4df13",
        "r2-e190ee9372dfedbccce1b81aaa0263e013b3a264a24e0cdbf62a8a383f8a36de",
        "r2-e38ddc86f9dc90b625acec736f459eab7bd3f102aca3ec159b39ede4f13be582",
        "r2-f59675a726497d8ef19274bab258e5bec9358c23a54adb144b13804563437d2b",
        "r2-faeaa041c997e9ae737343dc6f5ab1ad03a511f282cc7f67cdde0d537ee76325",
    }
)

AMBIGUOUS_CASE_IDS = frozenset(
    {
        "r2-7e14674bb6058c0e6aff2a8e826ad38711cd9f97cae14ffcf5e16fcef5fba915",
        "r2-a192f0d7cf1cb244f2564a369140248950d150d44a11d7e776bbed28e2933fcf",
        "r2-022b039547dfaf60501a130e0c82d7043e8c18c2e35bacf9768a275ff5a64a94",
        "r2-b7653dafdef48db19ffaaadb9745516fad3d29c5e399677d5a79073c0bcb2b4e",
        "r2-381ea5d64b2bbae3c8b7b70f3c483c200d6be4de7a4523bc06adbb13ee5c509b",
        "r2-f41fd4755110d3fd2294377adc262702a6d40d3cc303306e8d1fdd37d7b0627f",
        "r2-73d59031d03a138747318b2e4c4c3e26081e46579d61c580cdf3f2efd35a2fd2",
        "r2-3b0aa4c914fa7d8c91dfd26ba3929caad2afc52026d4f660bad79a6f2b686f6d",
    }
)

MANUAL_OUT_OF_SCOPE_CASE_IDS = frozenset(
    {
        "r2-9e98d8bb7cfd19087d8c8887c238c818e076fea2a9138ab33a28e7f73057fb84",
        "r2-8bee33b941ccc6f7388691986cd94f5ebf41e070379b05cf50c5004709e595f8",
        "r2-a449f05b1adac70f183f642c24494af075d5a6f38039c6be39e7a280789d2265",
        "r2-99e6ba0ed6d4faf1fde5943d7f32c8c7df97c3bf7ac9ac115d6020cb76b94fae",
        "r2-278d448b89e626aa10a8de567649be6a1cdba6dac9c9d750ea4eaf218c1d1761",
        "r2-831d37b27bafb3c1a1984d1cc3c82ca3d7afbb12c37e02e9cbe5b57f1a78972f",
        "r2-d8ce06c4971878ac1ebbfe3e641398d412142d48a7362f65c7307f1a836fb1cd",
        "r2-251d5372df87a486e18241fad9288b3d20b19e09529b3629ed2a8b0bf921569f",
        "r2-320b88de9fd55594b4c4e43bb069567502cae63cef7946f1b4e9d79af626b3ee",
        "r2-398b97c24c72a3578247bcb50a041aa814677886be930d79a2d964100c85ef8a",
        "r2-2d355d23c77df511e8ae62d95de0d730db9a34d81912f31d21d67b08968ad15b",
        "r2-8a993c3bdccdce8a3fb79ff6fd7020fdd735a499e91dadd635735c8f5dde7efb",
        "r2-6cab36742e07980f5d9028dc73535de0856976d8a49bbaf679119f64b9772858",
        "r2-0deb40749f0c4133c770e2cd04f238f2a209db0ffc9d3bc2e993b6a3a3dedd30",
        "r2-d7fea36aa20ce0d739350331b25a18d240525aefaaf5801ed83bcf154af8b040",
        "r2-a22e90f2f080ee5582016531047216c4062a26326fcbc9a87cba674b6eef1f2a",
        "r2-6a350d2def23bf6c704369b7ecc49d3b3d542e801a017301fa1f7843e8836124",
        "r2-0cc0defe76fed6f82124c6e386475088e80fe5fe30395a4f19b499d410163b13",
        "r2-6b92603e5d79c6e5f1d173cabb2add000864bf0de61ee2cac2ab61f48654d754",
        "r2-d1621b1dd89f686190e13e63cf74619d7a243570b264bb49761635c4390e7e2d",
        "r2-f1b725e1529c93a01a903e48c7ba71d1f40babff5fab5e2d885e7fa06eb06df1",
        "r2-b0648ecd64e74ce247618b1cc21a5c776c2d9273f1a6d23eb720d0892ac97e0b",
        "r2-24462d47ad0fa4be135deaedafbadc63fb232a6206c6ecf4bedd8d9adeb470f2",
        "r2-74f886cb32733579211711f4a558f2f0f768cdc629a3e556630115aa3fabb2a7",
        "r2-d7a939c74e20ceef3687b6432741127569b1fa4b761ae36c79847f40c547e174",
        "r2-7891b65d1a3bce0887fe86007ab56a7a9d5204a2256f5e142a3ae7b4fd346375",
        "r2-45a9fb3308b84acc058b7bfb46988458daa8398350ea183cff01912ec67836bb",
        "r2-9997f8880a12343c5b0dfbfa0785a289ce7f67ca9a095498c1e143e7693da904",
        "r2-1288a59f92134c5c831888ee8e14ab54a292ddc1314976b10a77057ff0cb370f",
        "r2-67b348abd91d9c01c6d70793eeb0b72f5b22d9385d8a1ece4cac9e4783561ab5",
        "r2-56b8258ded05ae0bf9c291f5a2640354615cd362b84737a590d71d4f2128c19e",
        "r2-c2785ec3b22d89a3a72648b9762cceb6e68e5909e18e6ccace13027a3bedb7fa",
        "r2-00e5da0aed3219249489b216555dbd5e75565688d2727f5a62cbfc7a43b4175a",
        "r2-b2d8a1fbcf397f76059aa97c10b6b1860678ccfe699ee6ca9ca8e95050465dd1",
        "r2-0d08c0b320a3181b140f8a0fd172d02a703b2f736472416c5134b2527e8a2104",
        "r2-7104697601d0628aa2892e1104073990e610e5160536f538e629f92fc366fab5",
        "r2-a50109edd97b32f83331514f244b311e72478df94955355c23f2b8f735abf065",
        "r2-0b2194d5eb4f34770b40fa18cb7a2e2bbc79f3fd3fecc226b703b71ad4efeae4",
        "r2-c36d8a26e20c70adfcf25cfbf0004394aa5836fe5b5949b61cde10cc1fddf229",
        "r2-865d3dbee330e838a9a02b9a5f3d50c1a2765788a68dc09bf8e5e4a6a1bc81bf",
        "r2-d8211a86a69d1e5f473f419b5960998855901b36d4f9ae144832ef0817c36266",
        "r2-fa36aa79eff34d7861764c0518b70b673f3a7cffb43b5a0da37223b211f71ada",
        "r2-e9113059f109890baa7ed0e4fc176162a38ffd2f2a48d53d87942271610cc922",
        "r2-18b5dfabd106182bf14c15c4180cb9a344fcec07d3725fe9254b516077cbf19a",
        "r2-da47afada12a46e19b62e4ec802425dec770bbf361f28e2416a3fd258e1acab6",
        "r2-42bf354e3e1df5d6a0a5cc6fe0fb48d369ef125d8e4514d0edc22db12b6f2a34",
        "r2-ec98e0c1e82a6eae444209759b9aa82544de5475d25ea90a44c3c81fe6449dba",
        "r2-6eb787a2f199d45311540a3456b0f90e5f08e69f961992b3b2b3d0e6fa455ba1",
        "r2-3d318b74fecfa41c7bdddd9e2cc7d026fe76d80827a43a9fdf374010ea02189a",
        "r2-6fc1befd5677e2b590b35ec33f8ef1c7b018ae61cdc5ed16a163f5d85a3eb61d",
        "r2-c18beaf8beb1d53b87a1f49a0c368655042b6c97752023a420042ea48765f700",
        "r2-835d795d5a5614603467a2b2cd76786640a81bff3de9bdcedbdb0164a3707820",
        "r2-570827fffe8b21ca77ae10886f5085a30d414fc6c60a0dee9f9baee45f1a8294",
        "r2-ca4aef4c19a6f293c5814fc5d000d721b2d1a5822b45c7b10af1a8d620679ee0",
        "r2-9d97a43c1b512dd8b5ea4adf33805c686e470297e7cf1dfb1350e6e00fdaf21b",
        "r2-d2162a10d8007116247466a9b49021fa7208864cba3fe62d31ed3c5457fb49f8",
        "r2-0c4c5e073bcdfacc3be4989dcbde8f62c21cdf5d9e026a6f065b6cfb4f6da757",
        "r2-54f5b1f120b8efa6f890e182510eed7706f56190c8e24508874f1ce6daf98ee7",
        "r2-21dd317a1db4f6099b7e0aa5b55c11039b8919fddc5720288881ffc74dd55f4c",
        "r2-7e50b125f40a4d63dcf7391a144b69312a903feff9aeb5edd8fed39a79d9f2cc",
        "r2-2be02aced3e45fb248be6d79ccbc00facc49f00378387bc9ecc86af45045e96b",
        "r2-32d80d64ae919b28d53ce6ebe65f20c499e2374e00bfa435527ef56aea4f6990",
        "r2-2d72a75f4f61c93935fb2d8554bd0b06a061501ea4ed8f3e6e3ac67ebc026223",
        "r2-1e46b589d41b19bd076a1461039f41137611a028b52e4742203d06f59480514d",
        "r2-1a3a8d7aa1c279b9be4cb4ae2d37bae4a9ce5f71b699e05a6bd979057289a79a",
        "r2-76609a8692841be83ab4cc8b642872987730010e094e7027f115b4b2b6d4c6ec",
        "r2-cf690c855c4f6d65647c29d81e620f3a90e2e315710d5abd79aa01b240f5d7c5",
        "r2-90eb0740764178c7bc8a5c20df0d9868652f2f3b1acceffeecf318ab710ffbb7",
        "r2-2dbb33160a2a4e4025633b1660655443280ae92675ef93f248b673c16e1836bf",
        "r2-e8a489976361e5dd9f49a8bb879c769428fe87ac515b8baaa0d3120f9fec7aee",
        "r2-c4b291f98e391610c8ddefd757b7fb20152e2afbd07af809144d45aac2062e96",
        "r2-b1637be847f36e32484215e542ae643f3768dbc73c4c50977b76f3225c31095d",
        "r2-e3bec98059e012511ed5ed7ece9aed4b036eb79b4c09649ede6e0ab51d2ac11d",
        "r2-9362abd4fd0f7d9247224338cbfd7fce79496c287c0727563b21c4dd00e98ff6",
        "r2-b7070fa617aa3283b92685cac5ac5945bfdb772fe04300d9ad35a218d6153cd1",
        "r2-a1f9c9500e78ecd326a28b3b5ed5eba60c77ebaf25916ddbbaea04af5f5e13cb",
        "r2-66b9f95c81767e4d01dcb83a24e67345ee75de4841792b2bf2bf1922aea231a6",
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
    if sentence_status == "incomplete" or case_id in MANUAL_OUT_OF_SCOPE_CASE_IDS:
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
            f"SENT-001 inventory mismatch: expected {expected_total}, got {len(sentence_records)}"
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
        raise LabelError("reviewed SENT-001 case-ID sets overlap")

    labels: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for record in sentence_records:
        case_id = _string(record, "case_id")
        if case_id in seen_ids:
            raise LabelError(f"duplicate SENT-001 case ID: {case_id}")
        seen_ids.add(case_id)

        source_id = _string(record, "source_id")
        path = _string(record, "path")
        try:
            source_text = texts[(source_id, path)]
        except KeyError as error:
            raise LabelError(f"source text missing for {source_id}:{path}") from error
        start = _integer(record, "start_offset")
        end = _integer(record, "end_offset")
        if not 0 <= start < end <= len(source_text):
            raise LabelError(f"invalid sentence span for {case_id}")
        slice_digest = hashlib.sha256(source_text[start:end].encode()).hexdigest()
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
        raise LabelError("reviewed SENT-001 case ID is missing from inventory")
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
