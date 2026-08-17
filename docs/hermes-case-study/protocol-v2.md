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
