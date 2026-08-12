# ste-lint

`ste-lint` is a local-first Python linter that helps technical authors find a
carefully selected, traceable subset of detectable ASD-STE100 Issue 9 concerns.
It is an authoring aid: it does not certify documents, replace the official
standard, or claim ASD/STEMG approval.

Phases 1–3 (foundation, lossless parsing, engine, configuration, and reporting)
are complete. No stable lint rules exist yet.

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
```

The project configuration is explicit and strict:

```toml
schema_version = 1

[rules]
enable = []
disable = []
```

CLI `--enable-rule ID` and `--disable-rule ID` override the file. There is no
implicit or global configuration. Unknown keys and IDs are operational errors.
Until Phase 4 adds executable rules, `ste lint` without a path reports that no
stable rules are available, and linting a path reports that no executable rules
are enabled.

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

## Licensing and normative data

The code is licensed under Apache-2.0. ASD-STE100, its rules, examples, and
dictionary are not included or licensed by this repository. Official vocabulary
is a bring-your-own external resource and must not be committed to Git.
