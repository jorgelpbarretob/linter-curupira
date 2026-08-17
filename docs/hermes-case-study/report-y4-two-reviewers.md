# Matriz Y4 — dois revisores (Kimi C1–C4 + Maritaca)

Run `matrix-y4-clarity-run-01` · 24 artefatos pareados · gerado 2026-08-17T02:22:09

Instrumentos: Kimi `kimi-k2.7` com rubrica C1–C4 (semantic-rubric-v1) + clareza 1–5 + achados; Maritaca `sabia-4-thinking` com clareza 1–5 + achados. Mesmos 24 artefatos cegos (M01–M24).

## Concordância Kimi–Maritaca

| Métrica | Valor |
|---|---|
| Spearman clareza (1–5) | 0.369 |
| Spearman findings_total | 0.208 |
| Acordo de classe de aceite | 0.417 (10/24) |
| Acordo de preferência A/B | 0.333 (4/12) |

## Tokens do painel Kimi

calls 24 · ok 24 · retries 0 · in 20776 · out 48608 · **total 69384**

## Por modelo (Kimi C1–C4)

| Modelo | S C | S CLI | clareza C | clareza CLI | findings C | findings CLI |
|---|---:|---:|---:|---:|---:|---:|
| qwen/qwen3.8-27b | 7.0 | 7.0 | 4.0 | 4.0 | 3.67 | 3.0 |
| nvidia/nemotron-3.5-lightning | 6.33 | 6.0 | 3.33 | 3.33 | 4.0 | 4.33 |
| meta/muse-glimmer-30b | 7.0 | 7.0 | 4.0 | 4.0 | 2.33 | 3.0 |
| thinkingmachines/inkling-small | 6.67 | 7.0 | 4.0 | 4.0 | 2.67 | 4.0 |

## Preferência por par

| Modelo | Case | S C→CLI (Kimi) | clareza C→CLI (Maritaca) | pref Kimi | pref Maritaca |
|---|---|---|---|---|---|
| qwen/qwen3.8-27b | case-007 | 7→7 | 4→4 | tie | tie |
| qwen/qwen3.8-27b | case-008 | 7→7 | 4→5 | tie | cli |
| qwen/qwen3.8-27b | case-012 ⚠ | 7→7 | 5→4 | tie | control |
| nvidia/nemotron-3.5-lightning | case-007 | 7→7 | 4→4 | tie | control |
| nvidia/nemotron-3.5-lightning | case-008 | 7→4 | 4→4 | control | control |
| nvidia/nemotron-3.5-lightning | case-012 ⚠ | 5→7 | 1→5 | cli | cli |
| meta/muse-glimmer-30b | case-007 | 7→7 | 4→4 | tie | tie |
| meta/muse-glimmer-30b | case-008 | 7→7 | 4→4 | tie | control |
| meta/muse-glimmer-30b | case-012 ⚠ | 7→7 | 4→4 | tie | cli |
| thinkingmachines/inkling-small | case-007 | 7→7 | 4→4 | tie | control |
| thinkingmachines/inkling-small | case-008 | 7→7 | 4→4 | tie | cli |
| thinkingmachines/inkling-small | case-012 ⚠ | 6→7 | 4→3 | cli | control |

⚠ = case-012 mantido em todos os agregados; análise de sensibilidade abaixo, sem exclusão.

## Sensibilidade case-012 (sem exclusão)

Acordo de preferência com case-012: 4/12 · sem case-012: 3/8

## Decisão (framework do mantenedor)

Classificação: **misto_discordante**

- Revisores não convergem na camada semântica (acordo de preferência abaixo de 2/3).
- Narrativa do estudo fica limitada ao gate determinístico. Sem alegação de ganho semântico.
- Benefício do Inkling-small permanece: gate determinístico zerou residual que o control deixou (1/3 vs 3/3). Esse fato independe da camada semântica.

## Integridade

- M13 (Kimi) truncado na primeira passada (`finish_reason=length`, zeros default). Detectado, re-executado com max_tokens maior. S final 7.
- SIGPIPE matou o script no meio do loop em uma passada; M14–M24 perdidos do checkpoint e recomputados. Tokens das passadas perdidas não entram no total abaixo.
- case-012 mantido em todos os agregados; sensibilidade acima, sem exclusão.

