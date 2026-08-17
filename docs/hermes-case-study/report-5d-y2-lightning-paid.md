# Y2 — `nvidia/nemotron-3.5-lightning` (sem :free)

Status: smoke dedicado concluído
SoT: `artifacts/hermes-case-study/matrix-y4-smoke/report-5d-y2-lightning-paid.json`

## Lock

- Y2 atual: `nvidia/nemotron-3.5-lightning`
- `:free` fica só como histórico (integridade)
- ASR original continua inelegível

## 1. Sessão executor (pago)

| Case | in C | out C | tot C | in CLI | out CLI | tot CLI | Δin | Δout | Δtot | residual C/CLI | lint log |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| case-007 | 57219 | 5478 | 243305 | 22678 | 2938 | 204048 | -34541 | -2540 | -39257 | 0/0 | True |
| case-008 | 37675 | 5845 | 348160 | 24621 | 2568 | 236085 | -13054 | -3277 | -112075 | 0/0 | False |
| case-012 | 23561 | 3343 | 235800 | 17510 | 3497 | 168975 | -6051 | 154 | -66825 | 0/0 | False |

Mediana Δin/out/tot: **-13054** / **-2540** / **-66825**

## 2. Painel revisor

Ainda não (mesmo backlog Y4).

## 3. Gate

- residual0 control 3/3 · CLI 3/3
- lint no log 1/3
- gate pass 1/3

## 4. Qualidade semântica (piloto)

- mediana S control 8 · CLI 4
- preferência {'control': 2, 'cli': 0, 'tie': 1}

## 5. Integridade

- Smoke `:free` anterior **não apagado**.
- total≫in+out permanece flag nos usage-file com cache.

## Comparativo pago vs :free (mesmos cases)

| Variante | med Δin | med Δout | med Δtot | residual0 C/CLI | gate lint | S C/CLI |
|---|---:|---:|---:|---|---:|---|
| **lightning** | -13054 | -2540 | -66825 | 3/3 · 3/3 | 1/3 | 8/4 |
| lightning:free | 848 | 57 | 114747 | 3/3 · 3/3 | 1/3 | 4/7 |

## Leitura

1. No pago, CLI reduziu input e total na mediana.
2. Residual empatado 0=0 nos 3 pares.
3. Um lint log claro (case-007). Outros com flag de log.
4. Qualidade semântica piloto favorece CLI.
