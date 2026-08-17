# Tarefa case-004 — atualização

## Mudança definida
A CLI antiga `hermes-lint` foi substituída por `curupira`.
Flag de regra: `--enable-rule CURUPIRA-PT-PONT-001` (antes `HERMES-PT-PONT-001`).

## Entrada
Atualize `inputs/runbook.md` para a CLI nova sem mudar o restante do fluxo.

## Pronto quando
1. Nenhuma ocorrência de `hermes-lint` ou `HERMES-PT-PONT-001`.
2. Comandos usam `curupira`.
3. Lint PONT-001 exit 0 no runbook final.
