#!/usr/bin/env python3
"""Run one isolated Grok review over the frozen PONT-001 review packet."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = Path(__file__).with_name("pont_001_grok_review_schema.json")
MODEL_REQUESTED = "grok-4.6"
EXPECTED_REVIEW_CSV_SHA256 = "b3fcb6214c5fc2eff295b4b7906d558f00770f1159a079648a64ac081e30fad4"
EXPECTED_CASES = 409
REVIEW_DATE = "2026-08-14"

SYSTEM_PROMPT = (
    "Você é um revisor externo somente-leitura de corpus pt-BR. "
    "Siga exclusivamente o prompt do usuário, não use ferramentas e retorne o schema exigido."
)

REVIEW_INSTRUCTIONS = """Revise cegamente todas as unidades de HERMES-PT-PONT-001.

Regra e guia aceitos:
- A unidade candidata é cada caractere `;` literal.
- `violation`: o alvo pertence a prosa técnica visível e lintável.
- `out_of_scope`: o alvo está inequivocamente em fenced code, inline code,
  destino de link/URL, metadado estrutural ou atributo/markup não apresentado como prosa.
- `ambiguous`: o contexto não permite decidir a região sem um contrato inexistente.
- `non_violation`: somente para documento-controle sem qualquer `;` literal.
- `expected_diagnostics`: 1 para violation; 0 para non_violation/out_of_scope;
  null para ambiguous.

Restrições:
- Não consulte, infira ou execute detector, código de produto ou labels anteriores.
- Não julgue a qualidade geral do texto nem a relação semântica entre orações.
- Não converta incerteza em negativo.
- Responda uma vez para cada case_id, na mesma ordem, sem omissão ou duplicata.
- Use somente o contexto e os metadados fornecidos.
- Para controles com document_has_literal_semicolon=false, use non_violation,
  document_control, expected_diagnostics=0 e high, salvo falha explícita de integridade.
- Rationale deve ser curta, específica e em pt-BR.
- Use requires_human=true quando truth=ambiguous, confidence não for high ou houver
  contexto insuficiente, markup malformado, região mista, problema de proveniência/licença,
  lacuna de protocolo ou incerteza do revisor.
- requires_human=false exige critical_reason=none; requires_human=true exige motivo diferente.

UNIDADES_JSON:
"""

DECISION_FIELDS = {
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

type JsonObject = dict[str, Any]


class ReviewRunError(RuntimeError):
    """Raised when inputs or Grok output violate the frozen review contract."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def ensure_external_output(output_dir: Path) -> None:
    resolved = output_dir.resolve()
    if resolved == PROJECT_ROOT or resolved.is_relative_to(PROJECT_ROOT):
        raise ReviewRunError("Grok review artifacts must remain outside the repository")


def load_packet_rows(review_csv: Path) -> list[dict[str, str]]:
    payload = review_csv.read_bytes()
    digest = sha256_bytes(payload)
    if digest != EXPECTED_REVIEW_CSV_SHA256:
        raise ReviewRunError(
            f"review CSV digest mismatch: expected {EXPECTED_REVIEW_CSV_SHA256}, got {digest}"
        )
    with review_csv.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != EXPECTED_CASES:
        raise ReviewRunError(f"review CSV must contain {EXPECTED_CASES} cases")
    if len({row["case_id"] for row in rows}) != len(rows):
        raise ReviewRunError("review CSV contains duplicate case_id")
    for row in rows:
        if row["review_status"] != "pending-human-review":
            raise ReviewRunError(f"review packet is not pristine: {row['case_id']}")
        populated = [field for field in DECISION_FIELDS - {"review_status"} if row[field]]
        if populated:
            raise ReviewRunError(f"review packet already has decisions: {row['case_id']}")
    return rows


def grok_input_record(row: dict[str, str]) -> JsonObject:
    common: JsonObject = {
        "case_id": row["case_id"],
        "record_type": row["record_type"],
        "source_path": row["source_path"],
        "source_file_sha256": row["source_file_sha256"],
        "source_format": row["source_format"],
        "language": row["language"],
        "source_license": row["source_license"],
    }
    if row["record_type"] == "literal_semicolon":
        common.update(
            {
                "line": int(row["line"]),
                "column": int(row["column"]),
                "unicode_offset": int(row["unicode_offset"]),
                "utf8_byte_offset": int(row["utf8_byte_offset"]),
                "occurrence_index_in_document": int(row["occurrence_index_in_document"]),
                "context_first_line": int(row["context_first_line"]),
                "context_last_line": int(row["context_last_line"]),
                "context_sha256": row["context_sha256"],
                "context": row["context"],
            }
        )
    else:
        common.update(
            {
                "selection_rank": int(row["selection_rank"]),
                "document_has_literal_semicolon": False,
            }
        )
    return common


def build_prompt(rows: list[dict[str, str]]) -> bytes:
    units = [grok_input_record(row) for row in rows]
    payload = json.dumps({"units": units}, ensure_ascii=False, separators=(",", ":"))
    return (REVIEW_INSTRUCTIONS + payload + "\n").encode("utf-8")


def validate_review(review: JsonObject, record_type: str) -> None:
    truth = review.get("truth")
    confidence = review.get("confidence")
    requires_human = review.get("requires_human")
    critical_reason = review.get("critical_reason")
    expected = review.get("expected_diagnostics")

    if record_type == "literal_semicolon":
        if truth not in {"violation", "out_of_scope", "ambiguous"}:
            raise ReviewRunError(f"truth inconsistent with occurrence: {review.get('case_id')}")
    elif record_type == "zero_semicolon_control":
        if truth != "non_violation" or review.get("structural_region") != "document_control":
            raise ReviewRunError(f"truth inconsistent with control: {review.get('case_id')}")
    else:
        raise ReviewRunError(f"unknown input record_type: {record_type}")

    expected_by_truth = {
        "violation": 1,
        "non_violation": 0,
        "out_of_scope": 0,
        "ambiguous": None,
    }
    if expected != expected_by_truth[truth]:
        raise ReviewRunError(f"expected_diagnostics mismatch: {review.get('case_id')}")
    region = review.get("structural_region")
    excluded_regions = {
        "fenced_code",
        "inline_code",
        "link_destination_or_url",
        "metadata",
        "markup_or_attribute",
    }
    region_is_consistent = (
        (truth == "violation" and region == "visible_prose")
        or (truth == "out_of_scope" and region in excluded_regions)
        or (truth == "ambiguous" and region == "ambiguous")
        or (truth == "non_violation" and region == "document_control")
    )
    if not region_is_consistent:
        raise ReviewRunError(f"structural_region mismatch: {review.get('case_id')}")
    if not isinstance(review.get("rationale"), str) or not review["rationale"].strip():
        raise ReviewRunError(f"blank rationale: {review.get('case_id')}")
    if (truth == "ambiguous" or confidence != "high") and requires_human is not True:
        raise ReviewRunError(f"critical review not escalated: {review.get('case_id')}")
    if requires_human is False and critical_reason != "none":
        raise ReviewRunError(f"noncritical review has critical reason: {review.get('case_id')}")
    if requires_human is True and critical_reason == "none":
        raise ReviewRunError(f"critical review lacks reason: {review.get('case_id')}")


def validate_structured_output(
    structured: JsonObject, rows: list[dict[str, str]]
) -> list[JsonObject]:
    reviews = structured.get("reviews")
    if not isinstance(reviews, list) or len(reviews) != len(rows):
        raise ReviewRunError(f"Grok must return exactly {len(rows)} reviews")
    expected_ids = [row["case_id"] for row in rows]
    actual_ids = [review.get("case_id") for review in reviews]
    if actual_ids != expected_ids:
        raise ReviewRunError("Grok output case_id order/bijection mismatch")
    for review, row in zip(reviews, rows, strict=True):
        if not isinstance(review, dict):
            raise ReviewRunError(f"review is not an object: {row['case_id']}")
        validate_review(review, row["record_type"])
    return reviews


def grok_command(prompt_path: Path, schema: JsonObject) -> list[str]:
    schema_text = json.dumps(schema, separators=(",", ":"))
    return [
        "grok",
        "--prompt-file",
        str(prompt_path),
        "-m",
        MODEL_REQUESTED,
        "--system-prompt-override",
        SYSTEM_PROMPT,
        "--json-schema",
        schema_text,
        "--disable-web-search",
        "--no-subagents",
        "--no-memory",
        "--max-turns",
        "1",
        "--verbatim",
        "--output-format",
        "json",
        "--reasoning-effort",
        "high",
        "--disallowed-tools",
        "run_terminal_cmd,read_file,grep,list_dir,web_search,web_fetch,search_replace,Agent",
    ]


def normalized_proposals_bytes(reviews: list[JsonObject]) -> bytes:
    lines = []
    for review in reviews:
        proposal = {
            **review,
            "review_status": "grok-proposed",
            "reviewed_by": MODEL_REQUESTED,
            "reviewer_role": "delegated-external-reviewer",
            "reviewed_on": REVIEW_DATE,
        }
        lines.append(json.dumps(proposal, ensure_ascii=False, separators=(",", ":")))
    return ("\n".join(lines) + "\n").encode("utf-8")


def run_review(review_csv: Path, output_dir: Path) -> JsonObject:
    ensure_external_output(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ReviewRunError("refusing to overwrite an existing Grok review run")
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = load_packet_rows(review_csv)
    prompt_payload = build_prompt(rows)
    prompt_path = output_dir / "grok-review-prompt.txt"
    response_path = output_dir / "grok-review-response.json"
    proposals_path = output_dir / "grok-review-proposals.jsonl"
    run_manifest_path = output_dir / "grok-review-run-manifest.json"
    prompt_path.write_bytes(prompt_payload)

    schema_payload = SCHEMA_PATH.read_bytes()
    schema = json.loads(schema_payload)
    completed = subprocess.run(
        grok_command(prompt_path, schema),
        cwd=output_dir,
        check=False,
        capture_output=True,
        text=True,
        timeout=1800,
    )
    if completed.returncode != 0:
        raise ReviewRunError(f"Grok CLI failed with exit {completed.returncode}")
    response_payload = completed.stdout.encode("utf-8")
    response_path.write_bytes(response_payload)
    wrapper = json.loads(completed.stdout)
    structured = wrapper.get("structuredOutput")
    if not isinstance(structured, dict):
        text_output = wrapper.get("text")
        if not isinstance(text_output, str):
            raise ReviewRunError("Grok response lacks structured output")
        structured = json.loads(text_output)
    reviews = validate_structured_output(structured, rows)
    proposals_payload = normalized_proposals_bytes(reviews)
    proposals_path.write_bytes(proposals_payload)

    truth_counts = Counter(review["truth"] for review in reviews)
    critical_count = sum(review["requires_human"] is True for review in reviews)
    run_manifest: JsonObject = {
        "schema_version": "hermes-grok-review-run/v1",
        "input_review_csv_sha256": EXPECTED_REVIEW_CSV_SHA256,
        "input_manifest_sha256": "3eaf4069017593c4f9e0d0c573736899ccbf137e3792ba97161e94d0663f86e7",
        "prompt_sha256": sha256_bytes(prompt_payload),
        "output_schema_sha256": sha256_bytes(schema_payload),
        "model_requested": MODEL_REQUESTED,
        "models_returned": sorted(wrapper.get("modelUsage", {}).keys()),
        "session_id": wrapper.get("sessionId"),
        "request_id": wrapper.get("requestId"),
        "usage": wrapper.get("usage"),
        "total_cost_usd": wrapper.get("total_cost_usd"),
        "response_sha256": sha256_bytes(response_payload),
        "proposals_sha256": sha256_bytes(proposals_payload),
        "case_count": len(reviews),
        "critical_count": critical_count,
        "truth_counts": dict(sorted(truth_counts.items())),
    }
    run_manifest_payload = (
        json.dumps(run_manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    run_manifest_path.write_bytes(run_manifest_payload)
    return run_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review_csv", type=Path, help="pristine human-review packet v2")
    parser.add_argument("output_dir", type=Path, help="new external Grok run directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = run_review(args.review_csv, args.output_dir)
    print(json.dumps(manifest, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
