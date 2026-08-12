# Phase 5 validation evidence

Status: passed
Date: 2026-08-12
Python: CPython 3.12.10
Package manager: uv 0.11.14

## Delivered scope

- accepted ADR-013 after independent review;
- strict, versioned source and canonical JSON schemas;
- deterministic source provenance and canonical content integrity hashes;
- NFC-aware, case-aware lookup preserving part of speech and meaning;
- closed `technical`, `matched`, `ambiguous`, and `missing` states;
- technical overlay from the existing local glossary;
- explicit project/CLI resource selection and precedence;
- authorized JSON importer with bounded reads and atomic local cache writes;
- offline composition through `RuleContext.capabilities`;
- entirely synthetic tests and reusable synthetic example.

No official vocabulary, definition, normative example, source PDF/DOCX, network
dependency or vocabulary compliance rule was added.

## TDD evidence

1. Loader and lookup tests first failed because `ste_lint.vocabulary` did not
   exist, then passed after the minimal strict models and parser were added.
2. Configuration and CLI tests first failed because `[vocabulary]`,
   `--vocabulary`, and `ste vocabulary import-json` did not exist, then passed
   after composition and cache I/O were implemented.
3. Independent review identified NFD lookup and ambiguous-match ordering as
   reproducibility risks. Both became failing regression tests before NFC
   normalization and canonical ordering were implemented.
4. Additional tests cover non-finite JSON, duplicate entries, byte/entry limits,
   issue mismatch, CLI precedence, validation before document reads, atomic
   cache cleanup and socket-free operation.

## Independent review

`cursor-agent` used `composer-2.5-fast` in read-only question mode:

- three ADR rounds found and closed missing configured-resource failure,
  casefold collision, deterministic hash and JSON type details;
- the loader/lookup review found no blocker and proposed NFC query normalization
  and stable match ordering, both implemented with regressions;
- the I/O/configuration/CLI review found no blocker and recommended earlier
  resource validation, which was implemented;
- residual path containment and symlink restrictions were not adopted because
  ADR-013 intentionally allows operator-supplied absolute and relative BYO
  paths. Cache filenames remain internally derived from SHA-256.

## Commands and results

| Command | Result |
|---|---|
| `uv --version` | passed; uv 0.11.14 |
| `uv lock --check` | passed; 12 packages resolved |
| `uv sync --locked` | passed; 12 packages checked |
| `uv run --no-sync python --version` | passed; Python 3.12.10 |
| `uv run --no-sync pytest` | passed; 163 tests in 6.30 s |
| `uv run --no-sync ruff check .` | passed |
| `uv run --no-sync ruff format --check .` | passed; 54 files formatted |
| `uv run --no-sync mypy src` | passed; 26 source files |
| `uv tree --no-dev` | passed; no external runtime package |
| `ste vocabulary import-json` synthetic smoke | passed; SHA-256 cache created atomically |
| `ste lint README.md --vocabulary ... --format json` | passed offline; empty diagnostics |
| `uv build --no-sources` | passed; sdist and wheel created |
| wheel inspection | passed; code, metadata, `LICENSE`, and `NOTICE` only |
| sdist inspection | passed; Phase 5 code/docs/tests and synthetic example present |
| protected-resource extension scan | passed; no matching artifact found |
| `git diff --check` | passed |

The smoke cache was removed after validation. No timeout was treated as success.

## Failures during execution

- the first focused runs failed in Red because the vocabulary module and CLI
  surface did not exist;
- the first broad Ruff gate found one unused import, one long line and two files
  requiring formatting; they were corrected and all gates repeated;
- a later Ruff gate found one import-order issue, which was corrected before the
  final gates;
- the first cache-cleanup tool call appeared delayed but completed successfully
  and confirmed that the generated directory no longer existed.

## Not verified

- any official or confidential vocabulary resource;
- throughput at the maximum 100,000-entry contract limit;
- Python 3.13, other operating systems, or remote CI;
- vocabulary-dependent diagnostic rules, which remain outside Phase 5.

## Next gate

Phase 6, optional NLP, requires a new explicit maintainer approval.
