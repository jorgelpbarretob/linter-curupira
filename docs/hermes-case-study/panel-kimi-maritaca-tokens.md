# Painel cego Kimi 2.7 + Maritaca (tokens sempre)

Run A/B: `run-v2-01` (control × CLI-min)
Fonte: `artifacts/hermes-case-study/v2/blind/scores-panel-kimi-maritaca.json`

## Tokens do painel (revisores)

- Kimi `kimi-k2.7`: {'input_tokens': 9147, 'output_tokens': 17539, 'total_tokens': 26686, 'calls': 22}
- Maritaca `sabia-4-thinking`: {'input_tokens': 8690, 'output_tokens': 9209, 'total_tokens': 17899, 'calls': 22}

## Tabela A/B com tokens de sessão + preferência do painel

| Case | sess tok C | sess tok CLI | Δ sess | Kimi pref | Maritaca pref | Kimi rev tok | Maritaca rev tok |
|---|---:|---:|---:|---|---|---:|---:|
| case-001 | 29275 | 29717 | 442 | control | tie | 1672 | 1415 |
| case-003 | 22222 | 29074 | 6852 | control | control | 2933 | 1330 |
| case-004 | 22676 | 29081 | 6405 | cli | cli | 2094 | 1212 |
| case-007 | 29029 | 29809 | 780 | control | control | 3227 | 1932 |
| case-008 | 29713 | 29935 | 222 | cli | control | 1782 | 1623 |
| case-009 | 22677 | 29930 | 7253 | cli | tie | 1869 | 1786 |
| case-010 | 2886 | 2824 | -62 | tie | cli | 2773 | 1904 |
| case-011 | 28579 | 29312 | 733 | cli | cli | 2445 | 1813 |
| case-012 | 2050 | 29587 | 27537 | cli | cli | 2808 | 1678 |
| case-013 | 13158 | 28691 | 15533 | tie | cli | 2066 | 1759 |
| case-014 | 23785 | 29699 | 5914 | cli | control | 3017 | 1447 |

## Clareza e classe (unblind)

| Case | Kimi C/CLI clarity | Kimi C/CLI class | Maritaca C/CLI clarity | Maritaca C/CLI class | sess Δtok |
|---|---|---|---|---|---:|
| case-001 | 5/4 | aceito/aceito | 4/4 | aceito_retrabalho_menor/aceito_retrabalho_menor | 442 |
| case-003 | 4/3 | aceito_retrabalho_menor/rejeitado_retrabalho_maior | 5/3 | aceito/rejeitado_retrabalho_maior | 6852 |
| case-004 | 4/5 | aceito_retrabalho_menor/aceito | 4/5 | aceito_retrabalho_menor/aceito | 6405 |
| case-007 | 4/4 | aceito/aceito_retrabalho_menor | 5/4 | aceito/aceito_retrabalho_menor | 780 |
| case-008 | 4/5 | aceito/aceito | 5/4 | aceito/aceito_retrabalho_menor | 222 |
| case-009 | 4/5 | aceito_retrabalho_menor/aceito | 5/5 | aceito/aceito | 7253 |
| case-010 | 4/4 | aceito_retrabalho_menor/aceito_retrabalho_menor | 4/5 | aceito_retrabalho_menor/aceito | -62 |
| case-011 | 3/4 | aceito_retrabalho_menor/aceito_retrabalho_menor | 4/5 | aceito_retrabalho_menor/aceito | 733 |
| case-012 | 3/4 | aceito_retrabalho_menor/aceito_retrabalho_menor | 4/5 | aceito_retrabalho_menor/aceito | 27537 |
| case-013 | 3/3 | aceito_retrabalho_menor/aceito_retrabalho_menor | 4/5 | aceito_retrabalho_menor/aceito | 15533 |
| case-014 | 4/4 | aceito_retrabalho_menor/aceito | 5/4 | aceito/aceito | 5914 |

## Agregado preferências

- Kimi preferred_condition: {'control': 3, 'cli': 6, 'tie': 2}
- Maritaca preferred_condition: {'tie': 2, 'control': 4, 'cli': 5}

## Política

- Sempre reportar **tokens de sessão A/B** (in/out/total e delta).
- Sempre reportar **tokens do revisor** por chamada e totais do painel.
- Gate operacional permanece separado (lint executado + residual 0).

