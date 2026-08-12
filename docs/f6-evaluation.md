# Evaluation of the Phase 6 NLP preview rules

Status: seed corpus complete
Date: 2026-08-12

## Reproducible environment

- CPython 3.12.10, Windows x86-64, CPU;
- spaCy 3.8.15, MIT;
- `en_core_web_sm` 3.8.0, MIT;
- official model wheel SHA-256:
  `1932429db727d4bff3deed6b34cfc05df17794f4a52eeb26cf8928f7c1a0fb85`;
- runtime loading from the installed local package, with NER excluded and no
  network access.

The 26 English examples are short project-authored fixtures. The 20 cases
approved with the candidates are preserved, and six further synthetic
technical cases expand the seed to 13 cases per rule. The official standard,
its examples and its vocabulary are not in the corpus.

## Results

Determinate truth contributes to TP, FP, FN and TN. Indeterminate truth is
excluded from that matrix and evaluated as abstention. Wilson intervals are
bilateral 95% intervals over emitted diagnostics.

| Rule ID | TP | FP | FN | TN | Precision | 95% precision CI | Recall | Indeterminate abstention | Unsafe emissions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `STE-I9-VOICE-001` | 4 | 0 | 0 | 5 | 1.00 | 0.510–1.000 | 1.00 | 4/4 (1.00) | 0 |
| `STE-I9-NOTE-001` | 6 | 0 | 0 | 5 | 1.00 | 0.610–1.000 | 1.00 | 2/2 (1.00) | 0 |

Both rules remain `preview/info` and disabled by default. Point precision meets
0.95, but the corpus is too small and both Wilson lower bounds are below 0.95.
There is no autofix.

## Conservative controls

- only one complete, contiguous parser sentence is analyzed;
- validated NLP tokens must match exact source offsets;
- passive voice reports explicit agents, plus unambiguous modal passive chains
  only in procedural text;
- agentless passive/state ambiguity abstains;
- note commands require `text_type = "procedural-note"`, a parser command root
  and no explicit grammatical subject;
- fragments and ambiguous present-tense roots abstain;
- missing or divergent NLP installation is an operational error, never a quiet
  rule skip.

## Limitations

The small general-English model does not provide calibrated confidence for
these rule decisions. This seed does not establish production precision,
coverage across technical domains, or behavior on operating systems other than
the reference gate. A larger independently labeled corpus is required before
either rule can be considered for `stable`.
