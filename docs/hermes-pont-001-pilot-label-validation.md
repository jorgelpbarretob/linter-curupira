# Validação e congelamento do piloto HERMES-PT-PONT-001

Status: Accepted
Date: 2026-08-13

## Escopo

Este gate valida somente labels de desenvolvimento. Não autoriza execução do
linter, TDD, promoção, fixer ou criação retroativa de holdout.

## Arquivos

- proposta: `corpus/hermes/pont-001-development-proposal.jsonl`;
- canônico: `corpus/hermes/pont-001-development-v1.jsonl`;
- manifesto: `corpus/hermes/pont-001-development-v1.sha256`;
- schema: `corpus/hermes/schema-v1.json`;
- guia: `docs/hermes-annotation-guide-v0.1.md`.

SHA-256 canônico:
`51f52007848deaae5169171354d900488df9faedbf073a17a48b14d714703bfc`.

## Decisão humana

O mantenedor aprovou ADR-018, guia e 40/40 labels propostas em 2026-08-13.

| Truth | Casos aprovados |
|---|---:|
| `violation` | 12 |
| `non_violation` | 12 |
| `out_of_scope` | 12 |
| `ambiguous` | 4 |

Casos `pont-dev-037` a `pont-dev-040` permanecem `ambiguous`, com
`expected_diagnostics = null`.

## Transformação canônica

A proposta e o arquivo v1 têm bijeção por `case_id`. Texto, truth, expectativa,
racional e metadados de origem são idênticos. A transformação alterou somente:

- `review_status`: `pending-human-review` para `approved`;
- adição de `reviewed_by = project-maintainer`;
- adição de `reviewed_on = 2026-08-13`.

Ordem lexical, UTF-8 e LF foram preservados. O arquivo possui 40 linhas JSONL e
40 IDs únicos.

## Estado de execução

Nenhum linter ou detector, inglês ou Hermes, foi executado contra proposta ou
canônico. Não existe artefato de resultados. O próximo trabalho permanece a
definição independente de challenge/holdout em PT2.
