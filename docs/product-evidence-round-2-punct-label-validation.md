# Rodada 2 — validação pré-execução de `STE-I9-PUNCT-001`

Data: 2026-08-13

Status: 69/69 labels aceitas pelo Cursor; tranche congelada; linter não executado

## Âncoras

- inventário: 1.173 registros `pending-review`, SHA-256
  `bebbabe41b28f59e87250e188fe946b237152f9293c8765a06d1322cb3d94c38`;
- proposta PUNCT externa:
  `/tmp/ste-lint-product-evidence-round2-labels-punct-001-proposal.jsonl`;
- SHA-256 da proposta:
  `b1ce0c8c0b418c9689df1c2de9bf7c24fb9396b9c582608834a2354195913cfa`;
- schema: `ste-lint-product-evidence-labels/v1`;
- cobertura: bijeção com os 69 `case_id` de `STE-I9-PUNCT-001`.

O JSONL de labels permanece fora do Git e não altera as duas cópias do
inventário congelado.

## Produção independente

Codex revisou cada ocorrência diretamente no path e offset do clone congelado,
sem consultar implementação ou saída do linter. O gerador separado ancora o
hash do inventário, aborta em contexto incerto ou novo caso de prosa e emite
somente seis campos canônicos. Nenhum texto-fonte, rationale ou resultado do
produto entra no arquivo.

Resultado proposto:

| Label | Casos |
|---|---:|
| `violation` | 2 |
| `non_violation` | 67 |
| `ambiguous` | 0 |
| `out_of_scope` | 0 |

As duas violações são ponto e vírgula em prosa visível. As 67 não violações são
ocorrências em markup, código ou exemplo estruturalmente ignorável.

## Revisão Cursor

O oitavo gate revisou integralmente as 69 labels contra inventário e clones. O
veredito foi `YES`, com **69/69 aceitas** e nenhum `case_id` contestado. Também
confirmou:

- cobertura bijectiva, schema fechado e ordem canônica;
- dois casos de prosa visível corretamente rotulados `violation`;
- 67 regiões ignoráveis corretamente rotuladas `non_violation`;
- zero ambiguidades e zero casos fora do escopo;
- ausência de circularidade com `ste_lint`.

## Limite do gate

Este congelamento não autoriza executar o linter, promover regra, implementar
fixer nem abrir automaticamente SENT, PARA ou LIST. O próximo WIP depende de
decisão humana explícita.
