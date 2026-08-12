# Phase 6 validation evidence

Status: passed
Date: 2026-08-12
Python: CPython 3.12.10
Package manager: uv 0.11.14

## Delivered scope

- accepted ADR-014 with spaCy 3.8.15 and `en_core_web_sm` 3.8.0;
- immutable vendor-neutral NLP contracts and exact offset validation;
- lazy local model loading with pinned distribution, pipeline and metadata
  validation;
- strict `[nlp]` configuration and operational exit `2` on missing/divergent
  requested capability;
- `STE-I9-VOICE-001` and `STE-I9-NOTE-001` as disabled-by-default
  `preview/info` rules with no autofix;
- 26 synthetic labeled cases, including all 20 approved seed labels;
- separate base and optional-NLP installation gates.

No official rule example, vocabulary entry, source document or protected
resource was added. Runtime does not download a model or open a network
connection.

## Evaluation

The pinned model produced zero FP, FN and unsafe emissions in the seed. Voice
had TP=4, TN=5 and 4/4 indeterminate abstentions. Note imperative had TP=6,
TN=5 and 2/2 indeterminate abstentions. Precision and recall were 1.00 for both,
but their 95% Wilson precision lower bounds were 0.510 and 0.610. Both remain
`preview` because the evidence is not sufficient for promotion.

Detailed metrics and limitations are in `docs/f6-evaluation.md`.

## TDD evidence

1. Contract tests first failed because `ste_lint.nlp` did not exist; immutable
   validated NLP models made them pass.
2. Rule tests first failed because the NLP support and rule modules did not
   exist; the minimum conservative `emit/clear/abstain` logic made them pass.
3. Configuration and CLI tests first failed before the strict `[nlp]` contract,
   lazy loader and operational error path were implemented.
4. The real pinned model tagged the imperative after a purpose clause as
   `VBP`; a guarded subjectless `VB/VBP` policy admitted the approved example,
   while explicit subjects and `VBZ` remain non-emitting.
5. Independent review requested stronger isolation/provenance failure tests and
   a neutral error module. These were implemented before the reviewer approved
   the rule/offset layer.

## Independent review

`cursor-agent` with `composer-2.5-fast` ran in read-only ask mode. The first
implementation review requested changes for optional-install/version/model
failure coverage, CLI-to-adapter coupling and an explicit no-import regression.
The changes added a neutral `NlpSetupError`, failure-path tests, exact model
compatibility metadata validation and a fresh-process import check. A second
review of rule logic, false-positive controls and offset rebasing returned
`APPROVE`. A third-person `VBZ` regression and note-offset parity test were
also added after the review.

## Commands and results

| Command | Result |
|---|---|
| `uv --version` | passed; uv 0.11.14 |
| `uv lock --check` | passed; 54 packages resolved |
| `uv sync --locked` | passed; NLP packages absent from environment |
| base `uv run --no-sync pytest -q` | passed; 204 tests, 3 expected NLP skips |
| base import probe | passed; neither `spacy` nor `en_core_web_sm` installed |
| `uv sync --locked --extra nlp --group nlp-model` | passed |
| NLP `uv run --no-sync pytest -q` | passed; 208 tests |
| `uv run --no-sync ruff check .` | passed |
| `uv run --no-sync ruff format --check .` | passed; 70 files formatted |
| `uv run --no-sync mypy src` | passed; 33 source files |
| `uv run --no-sync ste --rules` | passed; seven preview rules listed |
| `uv run --no-sync ste lint` | passed; default path has no stable rule |
| `uv build --no-sources` | passed; sdist and wheel built |
| wheel metadata inspection | passed; no mandatory dependency, spaCy only under `nlp` extra |
| offline socket-blocked model test | passed |
| protected-resource extension scan | passed; no matching artifact |
| `git diff --check` | passed |

No timeout was treated as success.

## Failures during execution

- all focused TDD Red failures were expected missing-module/contract failures;
- the first broad Ruff run found one long line and four formatting candidates;
  formatting and import order were corrected before the full gates;
- the first Cursor transport exceeded the Windows argument-size limit, so the
  review was split into two smaller embedded-file rounds;
- the first independent implementation review requested changes; all confirmed
  findings were covered by regressions and the follow-up review approved;
- `uv tree --no-dev` displayed optional lock-graph packages even after a base
  sync, so installed-module probes and wheel metadata were used as the direct
  isolation evidence.

## Not verified

- precision on a large independently labeled or confidential technical corpus;
- Python 3.13, non-Windows operating systems, GPU execution or remote CI;
- NLP throughput at the one-million-character parser limit;
- promotion to `stable`, which remains explicitly out of scope.

## Next gate

Phase 7, safe fixer, requires a new explicit maintainer approval.
