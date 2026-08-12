# ADR-004: contrato de Rule e Diagnostic

Status: Accepted
Data: 2026-08-12

## Contexto

O contrato sustenta catálogo, engine, reporting, baseline e integrações futuras.
Mudá-lo depois de consumidores públicos será caro.

## Decisão proposta

Usar modelos imutáveis no domínio. `Rule.check(context)` não faz I/O. Todo
`Diagnostic` contém `rule_id`, `source`, `severity`, `location`, `explanation` e
`suggestion` opcional. A borda cuida de validação e serialização.

## Consequências

- O domínio não importa CLI, filesystem, NLP, semantic ou SDK externo.
- Meta-testes verificam spans, ordenação, registry e fonte.
- Campos futuros entram de modo compatível somente com consumidor real.

## Aprovação necessária

Aceito pelo mantenedor em 2026-08-12, antes da Fase 1.
