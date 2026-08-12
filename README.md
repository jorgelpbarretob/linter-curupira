# ste-lint

`ste-lint` is a local-first Python linter that helps technical authors find a
carefully selected, traceable subset of detectable ASD-STE100 Issue 9 concerns.
It is an authoring aid: it does not certify documents, replace the official
standard, or claim ASD/STEMG approval.

Phases 1–4 are complete. Phase 4 provides five deterministic Issue 9 rules as
explicitly opt-in `preview` checks. No rule is `stable` yet, and absence of
diagnostics does not mean full compliance.

## Requirements

- Python 3.12 or newer; the local environment is pinned by `.python-version`
- `uv` 0.11.14; `pyproject.toml` rejects a different uv version

The base package has no runtime dependencies. NLP, LLM SDKs, the official
vocabulary, and network access are not part of the default lint path.

## Development

```powershell
uv sync --locked
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run ste --help
uv run ste lint
```

Lint one UTF-8 document with deterministic text or JSON output:

```powershell
uv run ste lint manual.md
uv run ste lint manual.md --format json
uv run ste lint manual.md --config ste-lint.toml
uv run ste --rules
uv run ste --explain STE-I9-PUNCT-001
```

The project configuration is explicit and strict:

```toml
schema_version = 1
text_type = "procedural" # procedural | descriptive | procedural-note

[rules]
enable = ["STE-I9-PUNCT-001"]
disable = []

[glossary]
terms = ["bleed-air valve", "ZX-4 controller"]
```

CLI `--enable-rule ID` and `--disable-rule ID` override the file. There is no
implicit or global configuration. Unknown keys and IDs are operational errors.
`--text-type` overrides the file. The local glossary is passed to rules as a
project allowlist. It is not the official STE vocabulary and does not enable a
vocabulary-compliance claim.

All five rules remain disabled by default because they are `preview`. Enable
only the rules you want to evaluate:

| Rule ID | Coverage |
|---|---|
| `STE-I9-PUNCT-001` | semicolons in lintable prose |
| `STE-I9-SENT-001` | unambiguously countable procedural sentences above 20 words |
| `STE-I9-SENT-002` | unambiguously countable descriptive sentences above 25 words |
| `STE-I9-PARA-001` | unambiguous descriptive paragraphs above six sentences |
| `STE-I9-LIST-001` | narrow direct Markdown list lead-ins containing `these` |

Sentence and paragraph rules abstain when `text_type` is missing or does not
match. Ambiguous counting constructs also cause abstention.

Create and apply a content-based baseline:

```powershell
uv run ste lint manual.md --enable-rule STE-I9-PUNCT-001 `
  --write-baseline ste-baseline.json
uv run ste lint manual.md --enable-rule STE-I9-PUNCT-001 `
  --baseline ste-baseline.json
```

The baseline stores only SHA-256 fingerprints, not document excerpts. It
suppresses reporting after every rule and diagnostic has executed and passed
validation.

Exit codes:

| Code | Meaning |
|---:|---|
| `0` | execution succeeded and emitted no diagnostics |
| `1` | execution succeeded and emitted diagnostics |
| `2` | configuration, input, catalog, parser, or rule execution failed |

The parser accepts decoded Unicode text for `.txt`, `.md`, and `.markdown`
documents. See [`docs/parsing-contract.md`](docs/parsing-contract.md) for the
supported Markdown subset, offset model, and conservative abstention behavior.
The engine, configuration, reporting schema, and failure model are documented in
[`docs/engine-contract.md`](docs/engine-contract.md).
Corpus metrics and limitations are in
[`docs/f4-evaluation.md`](docs/f4-evaluation.md).

## Licensing and normative data

The code is licensed under Apache-2.0. ASD-STE100, its rules, examples, and
dictionary are not included or licensed by this repository. Official vocabulary
is a bring-your-own external resource and must not be committed to Git.
