# ADR-014: optional NLP backend and pinned local model

Status: Accepted
Date: 2026-08-12

## Context

Phase 6 needs grammatical analysis without adding NLP to the default offline
lint path. Backend types must not leak into the domain or rule contracts, model
drift must not silently change diagnostics, and source offsets must remain
traceable. A missing optional dependency or model must fail clearly only when an
NLP rule is explicitly enabled.

## Options considered

1. **spaCy plus `en_core_web_sm`:** mature Python packaging, Windows/Python 3.12
   wheels, POS tags and dependency parsing, CPU model with a published checksum.
   Cost: a sizeable optional dependency tree and accuracy that must be measured
   on technical text.
2. **Stanza plus English resources:** strong linguistic pipeline and local
   inference. Rejected for the first increment because PyTorch and separately
   downloaded resources create a heavier optional install and provenance path.
3. **Only a project heuristic or fake backend:** smallest implementation, but it
   does not satisfy the Phase 6 requirement for a pinned evaluated NLP model.
4. **Transformer pipeline:** potentially higher accuracy, but model size,
   latency, hardware variance and licensing review exceed the first NLP gate.

## Decision

Use spaCy `3.8.15` with `en_core_web_sm` `3.8.0` as the first optional backend.
Both are pinned. The model release declares compatibility with spaCy
`>=3.8.0,<3.9.0`, license MIT, size 12 MB and wheel SHA-256
`1932429db727d4bff3deed6b34cfc05df17794f4a52eeb26cf8928f7c1a0fb85`.

The distribution exposes an `nlp` optional extra containing only
`spacy==3.8.15`. The repository defines a non-default `nlp-model` dependency
group with the exact official model wheel URL. This keeps the model out of the
base wheel and prevents a released `ste-lint[nlp]` extra from depending on a
package that is not published on PyPI. The verified repository setup is:

```powershell
uv sync --extra nlp --group nlp-model
```

For an installed release, the equivalent explicit setup is:

```text
pip install "ste-lint[nlp]"
pip install "https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl#sha256=1932429db727d4bff3deed6b34cfc05df17794f4a52eeb26cf8928f7c1a0fb85"
```

Runtime never downloads a model or opens a network connection. The adapter
imports spaCy lazily and imports the model as a Python package. It validates
backend version, model package, model version, language, license metadata and
required tagger/parser components before analysis. Missing or divergent state is
an operational error with installation guidance.

### Public contract

`ste_lint.nlp` owns immutable project types:

- `NlpToken`: text, offsets relative to the analyzed text, lemma, coarse POS,
  fine tag, dependency label and head index;
- `NlpAnalysis`: exact source text, ordered tokens, backend/model identity;
- `NlpBackend.analyze(text)`: protocol returning `NlpAnalysis`.

No spaCy type crosses this boundary. The domain remains pure; rules receive the
backend through `RuleContext.capabilities["nlp"]`. Unit and public corpus tests
use a deterministic fake backend. The spaCy adapter is covered by a separate
offline integration gate with the pinned model installed.

Only an existing parser `Sentence` with `is_complete = true` and exactly one
contiguous lintable `TextSpan` is sent to NLP. Rules abstain for fragmented
spans, incomplete sentences, missing capability, unexpected token offsets or
unsupported parses. Token offsets must form ordered, non-overlapping spans
inside the exact input; any mismatch rejects the analysis rather than
realigning it. Adapter token offsets are Unicode code-point offsets into the
exact input and map back by adding the document span start. No NLP result can
change parser/document offsets.

### Configuration and activation

NLP rules remain `preview/info` and disabled by default. Enabling an NLP rule
also requires explicit configuration:

```toml
[nlp]
backend = "spacy"
model_package = "en_core_web_sm"
model_version = "3.8.0"
```

Unknown values or versions fail before rules execute. Without an enabled NLP
rule, spaCy and the model are not imported even if the section exists. With an
enabled NLP rule and no valid section/capability, lint fails operationally; it
does not silently skip a requested rule. This is CLI exit code `2` on stderr,
not a `Diagnostic` or JSON finding.

The adapter loads only components required for POS/dependency analysis and
disables NER. CPU execution is the supported reference gate. Backend, library,
model package and model version are recorded in Phase 6 evaluation evidence.
The initial integration gate is CPython 3.12.10 on Windows x86-64; other
supported environments remain explicit unverified risks until tested.

### Rule policy

- NLP output is evidence, not normative ground truth.
- Each rule defines explicit parse patterns and abstention conditions.
- No shared numeric confidence is invented when the model does not expose a
  calibrated confidence for the decision.
- Ambiguous patterns abstain; they are not converted to a categorical finding.
- Every NLP rule stays `preview` until its own labeled corpus reaches the
  precision gate with an interval reported.
- No autofix is added in Phase 6.

## Consequences

- Base install, base tests and deterministic rules remain dependency-free and
  offline.
- NLP installation is larger and must be selected explicitly.
- Exact pinning improves repeatability but requires a new ADR/evaluation to
  upgrade backend or model.
- The general web/news model can fail on technical prose; corpus evidence and
  conservative abstention control promotion.
- The model and spaCy remain external dependencies under their own MIT licenses;
  they are not embedded in this repository's wheel.

## Sources verified

- spaCy package and MIT license: https://pypi.org/project/spacy/
- official model release, compatibility, license, size and checksum:
  https://github.com/explosion/spacy-models/releases/tag/en_core_web_sm-3.8.0
- official model packaging guidance: https://spacy.io/usage/models

Verified on 2026-08-12.

## Independent review

`cursor-agent` with `composer-2.5-fast` reviewed the ADR and candidate labels in
two read-only rounds. The first round found no architectural blocker but blocked
the labels because abstention and non-violation were conflated. The revised
truth/detector axes, installation paths, offset contract and conservative parse
controls passed the second round with no blocker and a recommendation for human
approval.

## Approval

Accepted explicitly by the maintainer on 2026-08-12 after two independent
read-only review rounds with `cursor-agent` and `composer-2.5-fast`.
