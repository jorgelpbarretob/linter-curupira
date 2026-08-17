# Report 5D — smoke matriz Y=4 OpenRouter

Status: smoke concluído  
Run: `run-01`  
SoT: `artifacts/hermes-case-study/matrix-y4-smoke/report-5d.json`  
Tratamento: **CLI-min**  
Rota: `hermes -z --provider openrouter --usage-file`

## Y travado

1. `qwen/qwen3.8-27b`
2. `nvidia/nemotron-3.5-lightning:free` (troca do ASR)
3. `meta/muse-glimmer-30b`
4. `thinkingmachines/inkling-small`

Cases smoke: `007`, `008`, `012`  
Células: **24** runs · **12** pares A/B

## 1. Sessão do executor

Mediana CLI − control (n=12):

| Δ input | Δ output | Δ total |
|---:|---:|---:|
| **−3925,5** | **+379** | **+77563,5** |

Leitura: input do CLI costuma cair.  
Total sobe por cache/reasoning embutido no `total_tokens`.  
Use **input/output** como métrica limpa. Marque total anômalo.

### Por modelo (mediana Δ)

| Modelo | Δin | Δout | Δtot | residual0 C/CLI |
|---|---:|---:|---:|---|
| qwen/qwen3.8-27b | −7703 | +3111 | +100464 | 3/3 · 3/3 |
| nvidia/nemotron-3.5-lightning:free | +848 | +57 | +114747 | 3/3 · 3/3 |
| meta/muse-glimmer-30b | −44253 | +378 | +96355 | 3/3 · 3/3 |
| thinkingmachines/inkling-small | −148 | −67 | +58245 | **1/3 · 3/3** |

## 2. Painel revisor

Status: **ainda não** rodado nos artefatos Y4.  
Painel Kimi/Maritaca existente é da bateria v2 (Grok).  
Próximo passo: painel cego C1–C4 nos 24 artefatos.

## 3. Gate operacional

| Métrica | Valor |
|---|---:|
| residual CLI = 0 | **12/12** |
| residual control = 0 | 10/12 |
| lint invocado (log) | **6/12** |
| gate pass (lint log + residual 0) | **6/12** |

Achado: em 6 CLI o agent zerou residual e citou lint, mas o log não mostrou o comando.  
Flag: `cli_lint_not_observed_in_logs` (sem drop).

## 4. Qualidade (rubrica semântica v1)

Método: piloto heurístico Hermes-A (não painel humano).  
Rubrica: C1–C4, S=0..8.

| Agregado | Valor |
|---|---:|
| mediana S control | 5 |
| mediana S CLI | **8** |
| preferência CLI | **7** |
| preferência control | 1 |
| tie | 4 |

Destaque: **inkling-small**  
Control deixou residual em 008 (5) e 012 (1).  
CLI zerou residual e venceu S nos 3 pares.

## 5. Integridade

Flags mantidas no agregado:

| Código | n |
|---|---:|
| `total_much_greater_than_in_plus_out` | 16 |
| `cli_lint_not_observed_in_logs` | 6 |

ASR original Nemotron permanece documentado como inelegível.  
Y2 efetivo = `lightning:free`.

## Conclusão smoke

1. Y=4 cloud está operacional no Hermes.
2. CLI-min **não** explode input. Mediana de input cai.
3. Total bruta engana. Separe input/output de cache.
4. Primeira discriminação residual real: **inkling** control falha, CLI limpa.
5. Qualidade semântica piloto favorece CLI (S 8 vs 5).
6. Falta painel cego multi-revisor nos artefatos Y4.

## Artefatos

- lock: `artifacts/hermes-case-study/matrix-y4-lock.json`
- runs: `artifacts/hermes-case-study/matrix-y4-smoke/`
- report: `artifacts/hermes-case-study/matrix-y4-smoke/report-5d.json`
- runner: `tools/curupira/run_matrix_y4_smoke.py`
- piloto Athena 5D: `artifacts/hermes-case-study/pilot-variance/report-5d.json`
