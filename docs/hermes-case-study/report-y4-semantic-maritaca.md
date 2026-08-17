# Matriz Y4 — camada semântica Maritaca (clareza + achados contáveis)

Status: painel concluído 24/24 · run `matrix-y4-clarity-run-01`

SoT:
- Lock: `artifacts/hermes-case-study/matrix-y4-lock.json`
- Scores: `artifacts/hermes-case-study/matrix-y4-smoke/blind-clarity/maritaca-clarity-scores.json`
- Executor/gate: `artifacts/hermes-case-study/matrix-y4-smoke/report-5d.json` e `report-5d-y2-lightning-paid.json`

Revisor único: Maritaca `sabia-4-thinking` (temp=0). Clareza cega 1–5 + 4 categorias semânticas com trecho verificável.

## 2. Painel revisor — tokens

Maritaca: 24 calls · in 16855 · out 20831 · **total 37686**

## qwen/qwen3.8-27b

### 1. Sessão executor (tokens)

| Case | in C | out C | tot C | in CLI | out CLI | tot CLI | Δin | Δtot |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| case-007 | 124253 | 1615 | 125868 | 179667 | 4722 | 261221 | 55414 | 135353 |
| case-008 | 76752 | 1041 | 93473 | 69049 | 4152 | 193937 | -7703 | 100464 |
| case-012 | 117578 | 1209 | 186211 | 100414 | 4841 | 196983 | -17164 | 10772 |

Mediana Δin **-7703** · Δtot **100464**

### 4. Clareza + achados semânticos (Maritaca, cego)

| Case | clarity C | clarity CLI | findings C | findings CLI | aceite C | aceite CLI | pref |
|---|---:|---:|---:|---:|---|---|---|
| case-007 | 4 | 4 | 0 | 0 | aceito_retrabalho_menor | aceito | tie |
| case-008 | 4 | 5 | 0 | 0 | aceito | aceito | cli |
| case-012 | 5 | 4 | 0 | 3 | aceito | aceito_retrabalho_menor | control |

Média clareza control 4.33 · CLI 4.33 · findings 0.0 · 1.0

## nvidia/nemotron-3.5-lightning

### 1. Sessão executor (tokens)

| Case | in C | out C | tot C | in CLI | out CLI | tot CLI | Δin | Δtot |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| case-007 | 57219 | 5478 | 243305 | 22678 | 2938 | 204048 | -34541 | -39257 |
| case-008 | 37675 | 5845 | 348160 | 24621 | 2568 | 236085 | -13054 | -112075 |
| case-012 | 23561 | 3343 | 235800 | 17510 | 3497 | 168975 | -6051 | -66825 |

Mediana Δin **-13054** · Δtot **-66825**

### 4. Clareza + achados semânticos (Maritaca, cego)

| Case | clarity C | clarity CLI | findings C | findings CLI | aceite C | aceite CLI | pref |
|---|---:|---:|---:|---:|---|---|---|
| case-007 | 4 | 4 | 0 | 1 | aceito | aceito | control |
| case-008 | 4 | 4 | 1 | 3 | aceito_retrabalho_menor | aceito_retrabalho_menor | control |
| case-012 | 1 | 5 | 3 | 0 | rejeitado_retrabalho_maior | aceito | cli |

Média clareza control 3.0 · CLI 4.33 · findings 1.33 · 1.33

## meta/muse-glimmer-30b

### 1. Sessão executor (tokens)

| Case | in C | out C | tot C | in CLI | out CLI | tot CLI | Δin | Δtot |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| case-007 | 50205 | 1908 | 153809 | 2793 | 2216 | 153105 | -47412 | -704 |
| case-008 | 3930 | 3058 | 277836 | 4611 | 3436 | 374191 | 681 | 96355 |
| case-012 | 50715 | 3003 | 367254 | 6462 | 3626 | 505768 | -44253 | 138514 |

Mediana Δin **-44253** · Δtot **96355**

### 4. Clareza + achados semânticos (Maritaca, cego)

| Case | clarity C | clarity CLI | findings C | findings CLI | aceite C | aceite CLI | pref |
|---|---:|---:|---:|---:|---|---|---|
| case-007 | 4 | 4 | 1 | 1 | aceito_retrabalho_menor | aceito_retrabalho_menor | tie |
| case-008 | 4 | 4 | 0 | 4 | aceito | aceito_retrabalho_menor | control |
| case-012 | 4 | 4 | 2 | 0 | aceito_retrabalho_menor | aceito_retrabalho_menor | cli |

Média clareza control 4.0 · CLI 4.0 · findings 1.0 · 1.67

## thinkingmachines/inkling-small

### 1. Sessão executor (tokens)

| Case | in C | out C | tot C | in CLI | out CLI | tot CLI | Δin | Δtot |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| case-007 | 40639 | 615 | 141222 | 2504 | 995 | 199467 | -38135 | 58245 |
| case-008 | 2237 | 549 | 168546 | 2089 | 482 | 140555 | -148 | -27991 |
| case-012 | 2058 | 877 | 141943 | 3338 | 641 | 200715 | 1280 | 58772 |

Mediana Δin **-148** · Δtot **58245**

### 4. Clareza + achados semânticos (Maritaca, cego)

| Case | clarity C | clarity CLI | findings C | findings CLI | aceite C | aceite CLI | pref |
|---|---:|---:|---:|---:|---|---|---|
| case-007 | 4 | 4 | 0 | 1 | aceito | aceito_retrabalho_menor | control |
| case-008 | 4 | 4 | 3 | 2 | aceito_retrabalho_menor | aceito_retrabalho_menor | cli |
| case-012 | 4 | 3 | 2 | 4 | aceito_retrabalho_menor | aceito_retrabalho_menor | control |

Média clareza control 4.0 · CLI 3.67 · findings 1.67 · 2.33

## 3. Gate operacional (herdado do Hermes)

| Modelo | residual0 C | residual0 CLI | lint no log | gate pass |
|---|---:|---:|---:|---:|
| qwen/qwen3.8-27b | 3/3 | 3/3 | 1/3 | 1/3 |
| nvidia/nemotron-3.5-lightning (pago) | 3/3 | 3/3 | 1/3 | 1/3 |
| meta/muse-glimmer-30b | 3/3 | 3/3 | 2/3 | 2/3 |
| thinkingmachines/inkling-small | 1/3 | 3/3 | 2/3 | 2/3 |

## Categorias semânticas por braço (Matriz Y)

| Categoria | control | cli |
|---|---:|---:|
| implicit-agent | 3 | 5 |
| terminology | 4 | 6 |
| multiple-actions | 5 | 5 |
| ambiguous-reference | 0 | 3 |

## 5. Integridade

- Achados rejeitados sem trecho verificável: 2 (de 33 reportados).
- Erros de revisão: 0/24.
- `total_tokens ≫ in+out` nos usage-file com cache permanece flag (dimensão 1 herdada).
- `:free` do lightning mantido como histórico, sem exclusão.
- Painel de 1 revisor: concordância inter-revisores não disponível nesta bateria.

## Leitura

1. Clareza: tratamento não desloca a mediana. Três modelos empatam; lightning pago sobe CLI (puxado por case-012: 1→5); inkling cai (4→3,67).
2. Findings semânticos: CLI não reduz residual na Matriz Y. Só 2 de 12 pares melhoram findings; 4 pioram.
3. `implicit-agent` e `terminology` dominam nos dois braços: os modelos pequenos emitem imperativo sem agente e jargão sem qualificador.
4. O que derruba a leitura: painel de 1 revisor, 3 casos por modelo, variância alta (case-012 do lightning balança a média inteira).

