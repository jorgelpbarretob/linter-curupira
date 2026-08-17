# Rubrica semântica contável v1

Status: ativo  
Uso: avaliação **cega** de artefatos A/B (control e tratamento).  
Não substitui o gate operacional (`lint` + residual 0).  
Complementa `rubric-v1.md` (aceite) e a dimensão 4 do contrato 5D.

## Por que existe

O lint PONT-001 só conta ponto e vírgula.
Esta rubrica mede **sentido operacional** além da prosa.

## Regras de aplicação

1. Avalie **só** o artefato. Sem rótulo de condição.
2. Use as **mesmas** 4 categorias nos dois braços.
3. Não abra a KEY antes de gravar scores.
4. Não penalize ausência de Curupira. Curupira não é critério.
5. Erro crítico técnico → marque bloqueio. Soma semântica fica secundária.
6. Conte só o que o texto permite verificar. Não invente contexto de planta.

## As 4 categorias (escala 0–2)

Escala curta e contável:

| Nota | Significado |
|---|---|
| **0** | Falha material. Impede uso seguro ou correto sem reescrita. |
| **1** | Usável com ressalva. Falta clareza, ordem ou cobertura parcial. |
| **2** | Adequado. Operador experiente executa sem adivinhar o essencial. |

### C1 — Executabilidade

O leitor consegue **fazer** a tarefa na ordem certa?

Marque **0** se faltar ação crítica, ordem perigosa ou passo impossível.
Marque **1** se a sequência existe mas exige inferência frequente.
Marque **2** se cada passo é acionável (verbo + objeto + condição quando preciso).

Sinais de 0:
- “tratar o problema” sem ação
- liberar área antes de isolar
- comando CLI incompleto quando a tarefa exige comando

### C2 — Fidelidade e cobertura

O texto cobre o pedido e **preserva** fatos/tags/limites dados?

Marque **0** se faltar requisito obrigatório ou houver fato inventado material.
Marque **1** se cobrir o núcleo com omissão menor não crítica.
Marque **2** se checklist obrigatório estiver completo e fiel às fontes do caso.

Sinais de 0:
- tag obrigatória ausente
- setpoint inventado
- subcomando errado que muda o sentido (`curupira doc.md` no lugar de `curupira lint`)

### C3 — Estrutura e escaneabilidade

O formato ajuda leitura rápida no chão / plantão?

Marque **0** se for bloco denso sem ordem útil.
Marque **1** se houver lista/seções mas com ruído ou misturas.
Marque **2** se títulos/passos/listas permitirem scan em segundos.

Sinais de 2:
- seções sintoma → ação → verify → escala
- passos numerados curtos
- tags e limites fáceis de achar

### C4 — Ambiguidade residual

Quanto o operador ainda precisa **adivinhar**?

Marque **0** se houver ambiguidade crítica (quem, o quê, quando parar, o que é proibido).
Marque **1** se restarem vaguidões menores (“se necessário”, “conforme local”) sem risco alto.
Marque **2** se critérios de parada, proibições e referências externas estiverem explícitos o bastante.

Sinais de 0:
- “isole se precisar” sem gatilho
- “libere a área” sem condição
- dois caminhos SEV sem prioridade

## Score contável

Por artefato:

```
S = C1 + C2 + C3 + C4          # 0..8
```

| S | Leitura operacional |
|---|---|
| 0–2 | inadequado |
| 3–4 | frágil |
| 5–6 | aceitável com ressalvas |
| 7–8 | forte |

## Bloqueio (binário, fora da soma)

`critical_block = true` se **qualquer**:

1. erro técnico crítico (risco de segurança/processo)
2. requisito obrigatório do caso ausente
3. instrução que contradiz fonte fornecida de forma material

Se `critical_block = true`:
- classe de aceite = `bloqueado`
- ainda registre C1–C4 (para diagnóstico)
- a preferência A/B **não** pode escolher o lado bloqueado, salvo empate de bloqueio

## Classe de aceite (derivada, cega)

Aplique **depois** de C1–C4 e do bloqueio:

| Classe | Regra |
|---|---|
| `bloqueado` | `critical_block = true` |
| `rejeitado_retrabalho_maior` | S ≤ 4 **ou** qualquer Ci = 0 |
| `aceito_retrabalho_menor` | S ∈ {5,6} e nenhum Ci = 0 |
| `aceito` | S ≥ 7 e nenhum Ci = 0 e sem bloqueio |

Clareza legada 1–5 (opcional, compat):

| S | clarity_1to5 sugerida |
|---|---:|
| 0–1 | 1 |
| 2–3 | 2 |
| 4 | 3 |
| 5–6 | 4 |
| 7–8 | 5 |

## Preferência A vs B (cego)

1. Descarte lado com `critical_block` se o outro não tiver.
2. Prefira maior **S**.
3. Empate em S: prefira menos Ci = 0.
4. Empate: prefira maior C1, depois C2, depois C4, depois C3.
5. Empate total: `tie`.

Justificativa: 1 frase, ≤ 240 chars, citando a categoria decisiva.

## O que esta rubrica **não** mede

- tokens de sessão ou custo
- se o agente rodou `curupira lint`
- residual PONT-001
- beleza tipográfica pura sem impacto operacional

Esses ficam nas dimensões 1, 2, 3 e 5 do contrato 5D.

## JSON de score (por artefato)

```json
{
  "case_id": "case-007",
  "label": "A",
  "reviewer_id": "kimi-k2.7",
  "C1_executability": 2,
  "C2_fidelity_coverage": 2,
  "C3_structure_scan": 1,
  "C4_ambiguity": 1,
  "S": 6,
  "critical_block": false,
  "accept_class": "aceito_retrabalho_menor",
  "clarity_1to5_compat": 4,
  "justification": "C3=1 por seções misturadas. Sem bloqueio.",
  "scored_at": "ISO-8601"
}
```

## JSON de preferência (por par)

```json
{
  "case_id": "case-007",
  "reviewer_id": "kimi-k2.7",
  "preferred_label": "B",
  "S_A": 6,
  "S_B": 7,
  "critical_block_A": false,
  "critical_block_B": false,
  "tie_break_rule": "higher_S",
  "justification": "B vence em C1 e C4 com passos de parada explícitos."
}
```

## Prompt curto para revisor-modelo (cega)

Use este bloco. Não acrescente a condição experimental.

```
Avalie o artefato com a rubrica semântica v1.
Categorias C1 executabilidade, C2 fidelidade/cobertura, C3 estrutura/scan, C4 ambiguidade.
Cada Ci ∈ {0,1,2}. S=C1+C2+C3+C4.
critical_block true só se risco técnico crítico ou requisito obrigatório ausente.
accept_class pelas regras da rubrica.
Responda SÓ JSON do score por artefato.
Não mencione Curupira, controle ou tratamento.
```

## Amostras de calibração (âncoras)

### Âncora baixa (S esperado ≤ 3)

Texto: “Se a pressão subir, resolva e depois siga.”
- C1=0 (sem ação)
- C2=0 (sem tags/limites)
- C3=0
- C4=0
- block provável

### Âncora média (S esperado 5–6)

Lista numerada com tags certas, mas “se necessário chame supervisão” sem gatilho de tempo.
- C1=2, C2=2, C3=2, C4=1 → S=7 ou C4=1 e C3=1 → S=6

### Âncora alta (S esperado 7–8)

Seções claras, tags, proibição explícita, tempo de escalada, verify mensurável.
- todos Ci=2 → S=8

## Concordância entre revisores

Para painel multi-modelo:

| Métrica | Como contar |
|---|---|
| Acordo de classe | % pares com mesma `accept_class` |
| Acordo de preferência | % com mesmo `preferred_label` (ou ambos tie) |
| ΔS médio | média \|S_r1 − S_r2\| por artefato |
| Acordo grosso de S | % com \|ΔS\| ≤ 1 |

Divergência de `critical_block` ou de classe com \|ΔS\| ≥ 3 → flag `integrity.reviewer_disagreement` (não dropar).

## Integração no report 5D

Dimensão **4 Qualidade**:

- por artefato: C1..C4, S, accept_class, critical_block
- por par: preferred_label + justification
- agregado: mediana S por braço, win-rate de preferência, taxa de bloqueio

Gate (dimensão 3) e tokens (1–2) ficam fora desta soma.

## Versionamento

- `semantic-rubric-v1` é SoT desta escala.
- Mudança de âncora ou regra de classe → `v2` e bateria nova.
- Não recalcular v1 sealed com v2.
