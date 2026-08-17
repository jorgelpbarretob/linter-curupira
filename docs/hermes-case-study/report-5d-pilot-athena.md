# Report 5D — piloto Athena `qwen3.8-max`

Gerado: 2026-08-17T00:50:19.880327-03:00
Pares: 6

## 1. Sessão executor

| Case | Run | in C | out C | tot C | in T | out T | tot T | Δin | Δout | Δtot |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| case-007 | run-01 | 9128 | 3399 | 102255 | 7144 | 4849 | 187481 | -1984 | 1450 | 85226 |
| case-007 | run-02 | 2980 | 4793 | 103261 | 6890 | 4631 | 211841 | 3910 | -162 | 108580 |
| case-007 | run-03 | 3592 | 2498 | 126154 | 8781 | 3743 | 213996 | 5189 | 1245 | 87842 |
| case-008 | run-01 | 2710 | 1692 | 124466 | 5935 | 1845 | 184548 | 3225 | 153 | 60082 |
| case-008 | run-02 | 4440 | 1768 | 151616 | 6829 | 2870 | 213219 | 2389 | 1102 | 61603 |
| case-008 | run-03 | 3044 | 3112 | 125836 | 4992 | 4295 | 184519 | 1948 | 1183 | 58683 |

Mediana Δin/out/tot: 2807.0 / 1142.5 / 73414.5

## 2. Painel revisor
Fonte: `artifacts/hermes-case-study/v2/blind/scores-panel-kimi-maritaca.json`
Totais: `{'kimi': {'input_tokens': 9147, 'output_tokens': 17539, 'total_tokens': 26686, 'calls': 22}, 'maritaca': {'input_tokens': 8690, 'output_tokens': 9209, 'total_tokens': 17899, 'calls': 22}}`
Preferências: `{'kimi': {'control': 3, 'cli': 6, 'tie': 2}, 'maritaca': {'tie': 2, 'control': 4, 'cli': 5}}`

## 3. Gate operacional
Pass: 6/6
Nota: piloto usou skill preload, não CLI-min.

## 4. Qualidade
attached_from_panel
Preferências painel: {'kimi': {'control': 3, 'cli': 6, 'tie': 2}, 'maritaca': {'tie': 2, 'control': 4, 'cli': 5}}
Rubrica semântica C1–C4: `semantic-rubric-v1.md`. Aplicar nas próximas baterias.

## 5. Integridade
Flags: {'total_much_greater_than_in_plus_out': 12, 'treatment_was_skill_preload_not_cli_min': 6}
Anômalos mantidos no agregado.

### Cross-source v2 (Grok SessionDB)
n_pairs=11 mediana Δtok=5914 flags=3
v2 battery used grok-4.5 + chat -q. Kept for comparison. Not mixed into pilot medians.
