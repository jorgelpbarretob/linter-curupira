# Rodada 2 — validação pré-execução de `STE-I9-SENT-002`

Data: 2026-08-13

Status: 329/329 labels aceitas pelo Cursor; tranche congelada; linter não executado

## Âncoras

- inventário: 1.173 registros `pending-review`, SHA-256
  `bebbabe41b28f59e87250e188fe946b237152f9293c8765a06d1322cb3d94c38`;
- proposta SENT-002 externa:
  `/tmp/ste-lint-product-evidence-round2-labels-sent-002-proposal.jsonl`;
- SHA-256 da proposta aceita:
  `4276d16d76b7e5a79d91311252d5a9e551b9875edab2f465580b85c393fbca3f`;
- schema: `ste-lint-product-evidence-labels/v1`;
- cobertura: bijeção com os 329 `case_id` de `STE-I9-SENT-002`.

O JSONL de labels permanece fora do Git e não altera o inventário congelado.

## Produção independente

Codex revisou os 329 candidatos diretamente nos clones congelados. O labeler
independente valida o hash do inventário e os hashes dos spans, sem importar ou
executar `ste_lint`. `raw_alpha_token_count` foi usado somente para navegação;
as labels positivas usam contagem conservadora revisada individualmente.

Resultado congelado:

| Label | Casos |
|---|---:|
| `violation` | 15 |
| `non_violation` | 166 |
| `ambiguous` | 4 |
| `out_of_scope` | 144 |

Os 144 casos fora do escopo formam buckets disjuntos: 73 fragmentos
`incomplete`, 22 sentenças completas do documento procedural `code-based.md` e
49 casos completos procedurais, de navegação ou de fronteira estrutural
adjudicados individualmente. Desses 49, 33 estão contidos em spans PARA já
congelados como `out_of_scope`; os outros 16 cobrem listas, alertas, blockquotes
ou fragmentos que não constituem sentença descritiva normativa.

## Revisão Cursor

O décimo segundo gate revisou integralmente as 329 labels contra inventário,
scanner-spec, contrato, labeler e clones. O veredito foi `YES`, com **329/329
aceitas** e nenhum `case_id` contestado. O Cursor confirmou:

- contagem conservadora acima de 25 para as 15 violações;
- 166 controles completos no limite ou abaixo;
- quatro ambiguidades: três candidatos envolvidos no falso split por `etc.` e
  uma contagem de fronteira entre 25 e 26;
- a partição 73 + 22 + 49 dos casos `out_of_scope`;
- schema fechado, ordem canônica, bijeção e independência de `ste_lint`.

## Implicação metodológica

O denominador normativo desta tranche tem 185 casos: 15 `violation`, 166
`non_violation` e quatro `ambiguous`. Os 144 casos `out_of_scope` auditam a
fronteira e não entram na matriz normativa. As ambiguidades serão excluídas do
cenário estrito e contam contra a regra no cenário conservador definido pelo
plano.

## Limite do gate

Este congelamento não autoriza executar o linter, promover regra, implementar
fixer nem abrir automaticamente `STE-I9-SENT-001`. O próximo WIP depende de
decisão humana explícita.
