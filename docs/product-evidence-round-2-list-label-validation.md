# Rodada 2 — validação pré-execução de `STE-I9-LIST-001`

Data: 2026-08-13

Status: 73/73 labels aceitas pelo Cursor; tranche congelada; linter não executado

## Âncoras

- inventário: 1.173 registros `pending-review`, SHA-256
  `bebbabe41b28f59e87250e188fe946b237152f9293c8765a06d1322cb3d94c38`;
- proposta LIST externa:
  `/tmp/ste-lint-product-evidence-round2-labels-list-001-proposal.jsonl`;
- SHA-256 da proposta:
  `41f9110c7c60846b355ffecf3beadaac5924356a985e33df33c0898105871b10`;
- schema: `ste-lint-product-evidence-labels/v1`;
- cobertura: bijeção com os 73 `case_id` de `STE-I9-LIST-001`.

O JSONL de labels permanece fora do Git e não altera o inventário congelado.

## Produção independente

Codex revisou os 73 lead-ins e runs diretamente nos clones congelados. O
labeler independente valida hashes de cada span e aplica somente a subclasse
estreita pré-registrada: lista direta com pelo menos dois peers, indentation de
até três espaços, zero ou uma linha vazia, sem blocker e lead-in terminado na
mesma linha por `these <head>.` ou `these <head>:` com head plural regular.

Resultado proposto:

| Label | Casos |
|---|---:|
| `violation` | 0 |
| `non_violation` | 0 |
| `ambiguous` | 0 |
| `out_of_scope` | 73 |

Nenhum lead-in pertence à subclasse estreita. As construções observadas usam
formas como “the following”, “you will need”, “such as” ou frases independentes.

## Revisão Cursor

O nono gate revisou integralmente as 73 labels contra inventário, scanner-spec e
clones. O veredito foi `YES`, com **73/73 aceitas** e nenhum `case_id`
contestado. Confirmou também a cobertura bijectiva, schema fechado, ordem
canônica, hashes de spans e ausência de circularidade com `ste_lint`.

## Implicação metodológica

Os 73 casos `out_of_scope` auditam a fronteira entre runs Markdown e a
subclasse pública validada, mas não entram no denominador normativo. Esta
tranche adiciona **zero** casos `violation` e **zero** controles
`non_violation`; portanto, não produz precisão, recall, TP, FP, FN ou TN para
`STE-I9-LIST-001` nesta rodada. A regra continua dependendo da evidência F7 e de
novo corpus independente in-scope para qualquer promoção.

## Limite do gate

Este congelamento não autoriza executar o linter, promover regra, implementar
fixer nem abrir automaticamente SENT ou PARA. O próximo WIP depende de decisão
humana explícita.
