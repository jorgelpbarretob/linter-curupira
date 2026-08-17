# Revisão cega piloto — reviewer A (Hermes-time)

Run: `run-v2-01`
Scores: `artifacts/hermes-case-study/v2/blind/scores-reviewer-A-pilot.json`
Unblind join: `artifacts/hermes-case-study/v2/blind/unblind-join-reviewer-A-pilot.json`

Método: li só arquivos A/B + lint residual. Abri a KEY só depois de gravar os scores.

## Agregado (após unblind)

- pares: 11
- preferência (classe+clareza): {'control': 5, 'cli': 6}
- clareza CLI > control: 4
- clareza control > CLI: 1
- clareza empate: 6
- classe aceito CLI: 10/11
- classe aceito control: 10/11

## Por case

| Case | pref | clarity C | clarity CLI | class C | class CLI |
|---|---|---:|---:|---|---|
| case-001 | control | 5 | 5 | aceito | aceito |
| case-003 | control | 5 | 5 | aceito | aceito |
| case-004 | cli | 4 | 5 | rejeitado_retrabalho_maior | aceito |
| case-007 | control | 5 | 4 | aceito | aceito_retrabalho_menor |
| case-008 | cli | 4 | 5 | aceito | aceito |
| case-009 | cli | 5 | 5 | aceito | aceito |
| case-010 | cli | 5 | 5 | aceito | aceito |
| case-011 | control | 5 | 5 | aceito | aceito |
| case-012 | cli | 4 | 5 | aceito | aceito |
| case-013 | cli | 4 | 5 | aceito | aceito |
| case-014 | control | 5 | 5 | aceito | aceito |

## Notas do piloto

1. Quase todos os artefatos estão aceitáveis. O diferencial é micro-legibilidade e fidelidade de comando.
2. case-004: um lado perdeu por `curupira` sem subcomando `lint`.
3. case-007: typo Camine gerou retrabalho menor.
4. case-011: A e B idênticos nesta rodada.
5. Este score é piloto de um revisor (agente). Não substitui segundo revisor humano.

