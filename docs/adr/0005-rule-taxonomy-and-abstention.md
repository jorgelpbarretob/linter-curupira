# ADR-005: taxonomia de regras e abstenção

Status: Accepted
Data: 2026-08-12

## Contexto

O plano v2 distingue `pure` e `pos_dependent`, mas o contrato do projeto exige
quatro classes públicas. POS e parsing probabilístico não devem parecer
determinísticos por conveniência.

## Decisão proposta

Manter exatamente `deterministic`, `nlp`, `semantic` e `human-review` como
classes públicas. Registrar a base interna do detector separadamente, por
exemplo `pure`, `pos-dependent`, `parser-dependent`, `model-dependent` ou
`none`. Baixa confiança provoca abstenção ou degradação prevista; `semantic`
nunca emite `error`.

## Consequências

- A taxonomia pública permanece simples e compatível com `AGENTS.md`.
- Métricas podem ser segmentadas por capacidade sem criar tipos concorrentes.
- Regra que não cumpre precisão permanece `preview` ou não emite diagnóstico.

## Aprovação necessária

Aceito pelo mantenedor e revisor da seleção inicial em 2026-08-12.
