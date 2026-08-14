# Rodada 2 — validação pré-execução de `STE-I9-PARA-001`

Data: 2026-08-13

Status: 144/144 labels aceitas pelo Cursor; tranche congelada; linter não executado

## Âncoras

- inventário: 1.173 registros `pending-review`, SHA-256
  `bebbabe41b28f59e87250e188fe946b237152f9293c8765a06d1322cb3d94c38`;
- proposta PARA externa:
  `/tmp/ste-lint-product-evidence-round2-labels-para-001-proposal.jsonl`;
- SHA-256 da proposta aceita:
  `2e3a96a267bacec5bbe1530ff0c3c6ddcc698bd7967b4bb669e912be7507e93c`;
- schema: `ste-lint-product-evidence-labels/v1`;
- cobertura: bijeção com os 144 `case_id` de `STE-I9-PARA-001`.

O JSONL de labels permanece fora do Git e não altera o inventário congelado.

## Produção independente

Codex revisou os 144 parágrafos diretamente nos clones congelados. O labeler
independente valida o hash do inventário e os hashes dos spans, sem importar ou
executar `ste_lint`. A política pré-registrada considera normativo o parágrafo
descritivo com uma a seis sentenças completas e usa `out_of_scope` para
fragmentos sem sentença completa e conteúdo procedural ou de navegação.

Resultado final:

| Label | Casos |
|---|---:|
| `violation` | 0 |
| `non_violation` | 86 |
| `ambiguous` | 0 |
| `out_of_scope` | 58 |

Os 58 casos fora do escopo formam buckets disjuntos: 30 fragmentos com zero
sentença completa, sete parágrafos do documento procedural `code-based.md` e
21 casos procedurais ou de navegação adjudicados individualmente.

## Revisões Cursor e adjudicação

O décimo gate revisou integralmente as 144 labels e aceitou 141. Contestou três
casos manuais porque seus spans eram conceituais e descritivos, não procedurais:

- `r2-dfe51d8e98d64be27fd8f8f771b42298ad13fd39f1f4f1a5a53e97cffcee8e22`;
- `r2-398940768915abe09625062b6a6ec776de9222b94a917432db3546f628a65ed9`;
- `r2-36ee340beea4bdbd53aad94ad05481489f1eeeb3430db6c62fe5f596c352ddb0`.

Testes de regressão reproduziram os três rótulos incorretos antes da mudança.
Após a adjudicação, os casos passaram a `non_violation`, a lista manual caiu de
24 para 21 entradas e a proposta foi regenerada. O décimo primeiro gate
rechecou 144/144, aceitou todos os rótulos, confirmou a distribuição e devolveu
`YES` explícito para congelar somente `STE-I9-PARA-001`, sem `case_id`
contestado.

## Implicação metodológica

O denominador normativo desta tranche tem 86 controles `non_violation`. Não há
parágrafo com mais de seis sentenças no snapshot; por isso, a Rodada 2 não
exercita recall de violações para `STE-I9-PARA-001`. Os 58 casos
`out_of_scope` auditam a fronteira estrutural e não entram em precisão, recall,
TP, FP, FN ou TN.

## Limite do gate

Este congelamento não autoriza executar o linter, promover regra, implementar
fixer nem abrir automaticamente `STE-I9-SENT-001` ou `STE-I9-SENT-002`. O
próximo WIP depende de decisão humana explícita.
