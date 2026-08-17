# Matriz Y=4 — executores OpenRouter (cloud only)

Status: travado com ressalva  
Data: 2026-08-17  
Eixo Y do estudo barato/OSS.

## Seleção do usuário (4)

| # | Model ID OpenRouter | Papel no chat A/B | Probe |
|---|---|---|---|
| 1 | `qwen/qwen3.8-27b` | executor texto | **OK** chat |
| 2 | `nvidia/nemotron-3.5-asr-streaming-multilingual-0.6b` | substituído | ASR inelegível → `lightning:free` |
| 3 | `meta/muse-glimmer-30b` | executor texto | **OK** chat |
| 4 | `thinkingmachines/inkling-small` | executor texto | **OK** chat |

Evidência: `artifacts/hermes-case-study/matrix-y4-probe.json`

## Bloqueio de integridade

`Y2_ASR_NOT_CHAT`:
- o Nemotron linkado é modelo de **fala → texto**
- endpoint correto: `/api/v1/audio/transcriptions`
- **não** entra na grade de documentação pt-BR

Sem exclusão silenciosa: fica na lista Y com status `ineligible_chat`.

## Y efetivo (4) — confirmado

1. `qwen/qwen3.8-27b`
2. `nvidia/nemotron-3.5-lightning` (pago/standard. Troca do ASR e do :free)
3. `meta/muse-glimmer-30b`
4. `thinkingmachines/inkling-small`

## Candidatos Nemotron **chat** (só se você autorizar a troca)

Probe rápido OK em chat:

- `nvidia/nemotron-3.5-lightning` (e variante `:free`)
- `nvidia/nemotron-3-nano-30b-a3b`

Recomendado para manter “4 baratos”: **`nvidia/nemotron-3.5-lightning`**.

## Desenho da célula

```
X = cases (smoke: 007, 008, 012; full: 001–014 subset)
Y = modelos acima (cloud OpenRouter)
A/B = control × CLI-min Curupira
n = 1 smoke → 3 se CV exigir
```

Medição por célula = contrato 5D + `semantic-rubric-v1`.

## Revisores (não são Y)

Painel cego separado:

- Hermes-A (piloto)
- Kimi 2.7
- Maritaca sabia-4-thinking
- opcional Qwen revisor

## Próximo

1. Você confirma troca Y2 → `nvidia/nemotron-3.5-lightning`  
   **ou** outro Nemotron chat.
2. Smoke 3 casos × 3 (ou 4) modelos × A/B.
3. Score semântico cego C1–C4.

## Smoke run-01

Concluído: 24 runs / 12 pares.
SoT 5D: `artifacts/hermes-case-study/matrix-y4-smoke/report-5d.json`
Relatório: `docs/hermes-case-study/report-5d-matrix-y4-smoke.md`

## Y2 final

`nvidia/nemotron-3.5-lightning` (sem sufixo `:free`).
Smoke dedicado: `matrix-y4-smoke` pasta `nvidia_nemotron-3.5-lightning`.
