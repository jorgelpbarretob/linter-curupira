# Estudo Hermes × Curupira — protocolo v2

Status: aberto  
Base: release fechada `v1-cli-default-2026-08-16`  
Default de tratamento: **CLI-min** (instrução curta + `curupira lint`, sem skill preload)

## O que herda de v1

- desenho pareado control × tratamento
- gate operacional: lint executado + residual 0
- qualidade independente: legibilidade, aceite, retrabalho, tokens
- holdout selado intocável

## O que muda em v2

1. Tratamento default = CLI-min (não skill).
2. Log obrigatório por braço: session_id, system_prompt_len, tools, tokens in/out, wall_s.
3. Outliers permanecem no agregado. Investigação anexa, sem exclusão.
4. Pacote de revisão cega em `artifacts/hermes-case-study/v2/blind/`.
5. Novos cases 011–014 somam ao banco (001–010 permanecem).

## Não fazer

- Não editar retrospectivamente resultados v1.
- Não voltar skill preload como default sem novo experimento fechado.

## Baterias executadas

| Run | Cases | Pares | Executor | Gate | Resumo |
|---|---|---|---|---|---|
| run-v2-01 | 001, 003, 004, 007–014 | 11 | grok-4.5 | 11/11 | `artifacts/hermes-case-study/v2/battery-run-v2-01-summary.json` |
| run-v2-02 | 015, 016, 002, 005, 006 | 5 | grok-4.6 | 5/5 | `artifacts/hermes-case-study/v2/battery-run-v2-02-summary.json` |

Cobertura do banco: 16/16 cases com par control × CLI-min em v2.

Nota de confound: o executor mudou de grok-4.5 (v2-01) para grok-4.6 (v2-02).
Medianas de tokens não são comparáveis entre baterias; comparar só dentro de cada run.
Em run-v2-02 o braço CLI venceu tokens em 4/5 pares (1 empate) — direção oposta a run-v2-01.
Pacote cego run-v2-02: `artifacts/hermes-case-study/v2/blind/run-v2-02/`.
