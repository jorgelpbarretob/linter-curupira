# PT2 — protocolo do corpus piloto de HERMES-PT-PONT-001

Status: Accepted
Date: 2026-08-13

## Objetivo

Validar schema, guia de anotação, variedade estrutural e processo de
congelamento antes de procurar um holdout independente. O piloto não estima
valor de produto nem autoriza promoção.

## Lote proposto

Arquivo: `corpus/hermes/pont-001-development-proposal.jsonl`

| Truth proposta | Casos | Finalidade |
|---|---:|---|
| `violation` | 12 | ponto e vírgula em prosa de seis domínios |
| `non_violation` | 12 | controles sem ponto e vírgula |
| `out_of_scope` | 12 | código, URLs, destinos, metadados e atributos |
| `ambiguous` | 4 | markup incompleto ou fronteira ainda não decidida |
| total | 40 | piloto de contrato |

Todo texto é sintético, autoral, pt-BR e proposto sob CC BY 4.0. Nenhum caso é
holdout e nenhum possui status `approved`.

## Validação antes da revisão

- JSON válido, um objeto por linha;
- schema e enums fechados;
- `case_id` único e ordem lexical;
- `rule_id = HERMES-PT-PONT-001`;
- `review_status = pending-human-review` em 40/40;
- `expected_diagnostics = null` somente em `ambiguous`;
- nenhuma saída ou versão do linter;
- contagens e texto preservados byte a byte.

## Revisão humana

O revisor aplica `docs/hermes-annotation-guide-v0.1.md` a todos os casos. Pode
aceitar, corrigir com justificativa ou rejeitar. A revisão deve ser feita sem
executar o linter e registrar:

- revisor e papel;
- data/hora;
- casos alterados/rejeitados;
- esclarecimento necessário na especificação;
- decisão final por `case_id`.

## Congelamento

Depois da aprovação:

1. gerar arquivo canônico `pont-001-development-v1.jsonl`;
2. remover casos rejeitados, sem renumerar IDs existentes;
3. preencher `review_status`, `reviewed_by` e `reviewed_on`;
4. ordenar por `case_id` e serializar UTF-8/LF;
5. calcular SHA-256 e gravar manifesto separado;
6. executar validação independente de bijeção e contagens;
7. solicitar autorização para a primeira execução.

## Próxima tranche

O challenge será criado a partir de ambiguidades adjudicadas e falhas futuras.
O holdout precisa de autoria ou fonte independente do lote-piloto, licença
redistribuível, pré-registro e tamanho calculado antes de sua geração.

## Resultado do congelamento

- proposta: 40 casos `pending-human-review`;
- decisão humana: 40/40 aceitos sem mudança de truth;
- canônico: `corpus/hermes/pont-001-development-v1.jsonl`;
- labels: 12 `violation`, 12 `non_violation`, 12 `out_of_scope` e 4
  `ambiguous`;
- SHA-256:
  `51f52007848deaae5169171354d900488df9faedbf073a17a48b14d714703bfc`;
- detector/linter: não executado.
