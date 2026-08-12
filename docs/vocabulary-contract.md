# Vocabulary resource contract

Status: implemented in Phase 5
Date: 2026-08-12

`ste-lint` accepts a bring-your-own vocabulary resource. The project does not
ship the official ASD-STE100 vocabulary, definitions, examples, or source
documents. Importing a resource does not grant permission to use or redistribute
its contents.

## Authorized source JSON

The importer accepts only strict UTF-8 JSON with this versioned shape. This
example is synthetic and project-authored; a reusable copy is available at
[`examples/synthetic-vocabulary-source.json`](../examples/synthetic-vocabulary-source.json):

```json
{
  "format": "ste-lint-vocabulary-source",
  "schema_version": 1,
  "standard": "ASD-STE100",
  "issue": "9",
  "entries": [
    {
      "term": "flux valve",
      "part_of_speech": "synthetic-noun",
      "meaning_id": "synthetic-1",
      "case_sensitive": false
    }
  ]
}
```

Import it only when you have the right to process the source:

```powershell
uv run ste vocabulary import-json authorized-source.json `
  --cache-dir C:\local\ste-vocabulary-cache `
  --confirm-authorized
```

The command writes `<source_sha256>.json` atomically. The canonical resource
contains the entries required for lookup plus source and content hashes; it does
not retain the original source bytes or source path. The cache is explicit and
is never discovered globally.

## Lint configuration

Reference the generated canonical resource explicitly:

```toml
schema_version = 1

[vocabulary]
path = "C:/local/ste-vocabulary-cache/<source_sha256>.json"

[glossary]
terms = ["ZX-4 controller"]
```

`--vocabulary PATH` overrides `[vocabulary].path`. A relative TOML path is
resolved from the configuration file; a relative CLI path is resolved from the
current directory. When a path is configured, missing, invalid, incompatible or
tampered resources fail before rules run. With no path, lint continues without
the vocabulary capability.

## Lookup behavior

Lookup returns exactly one of `technical`, `matched`, `ambiguous`, or `missing`.
It preserves all matching `part_of_speech` and `meaning_id` values. Terms marked
case-sensitive require exact equality; other terms use Python 3.12 `casefold()`.
Optional class and meaning filters use exact equality.

The local `[glossary].terms` overlay is case-insensitive, has precedence and
returns `technical`. It is project policy, not normative vocabulary. Neither an
ambiguous nor a missing result can independently support a stable normative
diagnostic.

## Validation and limits

- strict keys, types, UTF-8 and Unicode NFC;
- exact format, schema, standard and Issue 9 identity;
- duplicate JSON keys and semantic collisions rejected;
- 16 MiB per resource, 100,000 entries and bounded fields;
- SHA-256 source provenance and deterministic content integrity;
- full validation on every load; no network access.

The canonical hashing algorithm and rationale are specified in
[`ADR-013`](adr/0013-vocabulary-resource-contract.md).
