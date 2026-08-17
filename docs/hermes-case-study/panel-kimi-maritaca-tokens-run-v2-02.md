# Painel cego Kimi 2.7 + Maritaca — run-v2-02 (tokens sempre)

Run A/B: `run-v2-02` (control × CLI-min)
Fontes: `artifacts/hermes-case-study/v2/blind/run-v2-02/scores-panel-kimi-maritaca.json` e `scores-semantic-c1c4-kimi-maritaca.json`

## Tokens do painel de clareza (revisores)

- Kimi `kimi-k2.7`: {'input_tokens': 4301, 'output_tokens': 5972, 'total_tokens': 10273, 'calls': 10}
- Maritaca `sabia-4-thinking`: {'input_tokens': 4159, 'output_tokens': 4525, 'total_tokens': 8684, 'calls': 10}

## Tokens da rubrica semântica v1 C1-C4 (revisores)

- Kimi `kimi-k2.7`: {'calls': 10, 'input_tokens': 7651, 'output_tokens': 12715, 'total_tokens': 20366}
- Maritaca `sabia-4-thinking`: {'calls': 10, 'input_tokens': 7069, 'output_tokens': 5922, 'total_tokens': 12991}

## Tabela A/B com tokens de sessão + preferência de clareza

| Case | sess tok C | sess tok CLI | Δ sess | Kimi pref | Maritaca pref | Kimi rev tok | Maritaca rev tok |
|---|---:|---:|---:|---|---|---:|---:|
| case-015 | 30957 | 30224 | -733 | tie | tie | 1907 | 1740 |
| case-016 | 42290 | 34820 | -7470 | tie | cli | 2322 | 1938 |
| case-002 | 30433 | 30353 | -80 | control | tie | 2462 | 1820 |
| case-005 | 29772 | 29345 | -427 | control | control | 1403 | 1357 |
| case-006 | 30360 | 30360 | 0 | control | control | 2179 | 1829 |

## Clareza e classe (unblind)

| Case | Kimi C/CLI clarity | Kimi C/CLI class | Maritaca C/CLI clarity | Maritaca C/CLI class | sess Δtok |
|---|---|---|---|---|---:|
| case-015 | 5/5 | aceito/aceito | 5/5 | aceito/aceito | -733 |
| case-016 | 4/4 | aceito_retrabalho_menor/aceito_retrabalho_menor | 4/5 | aceito_retrabalho_menor/aceito | -7470 |
| case-002 | 4/4 | aceito/aceito_retrabalho_menor | 4/4 | aceito_retrabalho_menor/aceito_retrabalho_menor | -80 |
| case-005 | 4/3 | aceito_retrabalho_menor/aceito_retrabalho_menor | 5/4 | aceito/aceito_retrabalho_menor | -427 |
| case-006 | 5/4 | aceito/aceito_retrabalho_menor | 4/4 | aceito/aceito_retrabalho_menor | 0 |

## Rubrica semântica v1 C1-C4 (unblind)

| Case | Kimi S C/CLI | Kimi class C/CLI | Maritaca S C/CLI | Maritaca class C/CLI | Kimi pref | Maritaca pref |
|---|---|---|---|---|---|---|
| case-015 | 4/7 | bloqueado/aceito | 6/7 | aceito_retrabalho_menor/aceito | cli | cli |
| case-016 | 7/7 | aceito/aceito | 7/7 | aceito/aceito | tie | tie |
| case-002 | 7/5 | aceito/aceito_retrabalho_menor | 7/7 | aceito/aceito | control | tie |
| case-005 | 6/7 | aceito_retrabalho_menor/aceito | 7/7 | aceito/aceito | cli | tie |
| case-006 | 7/7 | aceito/aceito | 7/7 | aceito/aceito | tie | tie |

## Agregado preferências

- Clareza — Kimi preferred_condition: {'tie': 2, 'control': 3}
- Clareza — Maritaca preferred_condition: {'tie': 2, 'cli': 1, 'control': 2}
- Semântica C1-C4 — Kimi preferred_condition: {'cli': 2, 'tie': 2, 'control': 1}
- Semântica C1-C4 — Maritaca preferred_condition: {'cli': 1, 'tie': 4}
- Concordância semântica: {'n_artifacts_both': 10, 'accept_class_agreement': '7/10', 'mean_abs_delta_S': 0.5, 'coarse_S_agreement_abs_delta_le_1': '8/10', 'preference_agreement': '3/5'}

## Integridade

- `integrity.reviewer_disagreement`: case-015 A (control): Kimi S=4 block=True (bloqueado) vs Maritaca S=6 block=False (aceito_retrabalho_menor). Kimi: A ordem de parada instrui fechar XV-205 antes de desligar P-77, o que pode fazer a bomba operar sem fluxo (risco de cavitação/dano) — ordem perigosa.

## Política

- Sempre reportar **tokens de sessão A/B** (in/out/total e delta).
- Sempre reportar **tokens do revisor** por chamada e totais do painel.
- Gate operacional permanece separado (lint executado + residual 0).
- Executor run-v2-02 = grok-4.6; não misturar medianas de tokens com run-v2-01 (grok-4.5).
