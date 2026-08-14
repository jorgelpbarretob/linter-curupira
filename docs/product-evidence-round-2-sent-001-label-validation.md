# Rodada 2 — validação pré-execução de `STE-I9-SENT-001`

Data: 2026-08-13

Status: 558/558 labels aceitas pelo Cursor; tranche congelada; linter não executado

## Âncoras

- inventário: 1.173 registros `pending-review`, SHA-256
  `bebbabe41b28f59e87250e188fe946b237152f9293c8765a06d1322cb3d94c38`;
- proposta SENT-001 externa:
  `/tmp/ste-lint-product-evidence-round2-labels-sent-001-proposal.jsonl`;
- SHA-256 da proposta aceita:
  `930e5e9324c79cf3546363e324675a7d3274e13b398c7cdfc53871d264b16a8d`;
- schema: `ste-lint-product-evidence-labels/v1`;
- cobertura: bijeção com os 558 `case_id` de `STE-I9-SENT-001`.

O JSONL de labels permanece fora do Git e não altera o inventário congelado.

## Produção independente

Codex revisou os 558 candidatos diretamente nos clones congelados. O labeler
independente valida o hash do inventário e os hashes dos spans, sem importar ou
executar `ste_lint`. `raw_alpha_token_count` foi usado somente para navegação;
as labels positivas usam contagem conservadora revisada individualmente.

Resultado congelado:

| Label | Casos |
|---|---:|
| `violation` | 40 |
| `non_violation` | 200 |
| `ambiguous` | 8 |
| `out_of_scope` | 310 |

Os 310 casos fora do escopo formam dois buckets disjuntos: 233 fragmentos com
`sentence_status=incomplete` e 77 candidatos completos adjudicados como
títulos, referências, notas, rótulos, navegação ou fragmentos não procedurais.

## Revisão Cursor

O décimo terceiro gate revisou integralmente as 558 labels contra inventário,
scanner-spec, contrato, labeler e clones. O veredito foi `YES`, com **558/558
aceitas** e nenhum `case_id` contestado. O Cursor confirmou:

- contagem conservadora acima de 20 para as 40 violações;
- 200 controles completos no limite ou abaixo;
- oito ambiguidades: dois casos de fronteira e seis registros pertencentes a
  três grupos com falso split por `e.g.`;
- a partição disjunta 233 + 77 dos casos `out_of_scope`;
- schema fechado, ordem canônica, bijeção e independência de `ste_lint`.

## Implicação metodológica

O denominador normativo desta tranche tem 248 casos: 40 `violation`, 200
`non_violation` e oito `ambiguous`. Os 310 casos `out_of_scope` auditam a
fronteira e não entram na matriz normativa. As ambiguidades serão excluídas do
cenário estrito e contam contra a regra no cenário conservador definido pelo
plano.

## Limite do gate

Este congelamento não autoriza executar o linter, promover regra nem implementar
fixer. A primeira execução controlada nos corpora depende de decisão humana
explícita.
