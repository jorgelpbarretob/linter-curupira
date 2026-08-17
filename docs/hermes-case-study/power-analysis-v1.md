# Power analysis v1 — estudo Hermes × Curupira

Status: pré-registro proposto
Data: 2026-08-17
Autor: Athena (perfil athena)
Base: protocolo pareado A/B recebido em 2026-08-17 (Documento de Desenho do Estudo),
piloto `docs/curupira-hermes-agent-pilot-v1.md`, ferramenta
`tools/curupira/hermes_agent_ab.py`.

## Pergunta

O desenho proposto tem poder estatístico para detectar o efeito do preflight
Curupira?

Resposta curta: depende do desfecho. Achados residuais têm poder de sobra em
16 tarefas. Rubrica e aceite não têm poder suficiente nesse tamanho.

## Métodos

- Alfa 0,05 bicaudal, poder 0,80, testes pareados.
- Rubrica: teste t pareado sobre diferença por tarefa (statsmodels `TTestPower`).
- Aceite e achados residuais: teste de McNemar sobre pares discordantes.
- Cálculo executado em 2026-08-17 com scipy 1.x e statsmodels.

## Resultados [ESTIMADO]

Premissas declaradas em cada tabela.

### Rubrica (desfecho contínuo pareado)

| n tarefas | d_z mínimo detectável |
|---:|---:|
| 12 | 0,89 |
| 16 | 0,75 |
| 20 | 0,66 |
| 30 | 0,53 |

Com n=16 o desenho detecta apenas efeito grande. Efeito médio (d_z ≈ 0,5)
exige ~30 tarefas.

### Aceite na primeira revisão (McNemar)

| p01 | p10 | delta | n pares exigido |
|---:|---:|---:|---:|
| 0,25 | 0,06 | 19 pp | 65 |
| 0,20 | 0,10 | 10 pp | 234 |

p01 = probabilidade de controle falhar e tratamento passar. p10 = o inverso.
Delta de 19 pontos percentuais vem do exemplo do próprio documento (22/48 vs
31/48). 16 tarefas não têm poder para aceite.

### Achados residuais (McNemar, prevalência no controle 70%)

| p01 | p10 | n pares exigido |
|---:|---:|---:|
| 0,63 | 0,02 | 12 |

Premissas: 70% das tarefas com pelo menos um achado no controle e o
tratamento limpa 90% deles. 16 tarefas têm sobra para esse desfecho.

### Esforço (premissas do próprio documento)

```
sessões de agente: 96 (16 tarefas × 2 braços × 3 execuções)
mediana por sessão: 15 min
tempo de agente: ~24 h
revisões cegas: 192 (2 revisores por artefato)
```

## Recomendações

1. Desfecho primário: achados residuais habilitados. Único com poder
   suficiente em 16 tarefas.
2. Multiplicidade: pré-registrar 1 primário e aplicar correção de Holm nos
   secundários. O desenho lista 10 métricas. Sem correção, falso positivo infla.
3. Unidade de análise: a tarefa. As 3 execuções por condição medem variância
   interna. O teste usa a mediana por tarefa. n efetivo = nº de tarefas.
4. Piloto de variância antes da grade: 3 execuções em 2 tarefas. Estimar
   variância intra-tarefa. Usar 3 execuções só se o agente variar de fato.
5. Banco de tarefas: pelo menos um terço sem ponto e vírgula no insumo. Sem
   isso, o estudo mede tautologia: tratamento vence por construção.

## O que derruba o estudo

- Todas as tarefas construídas para acionar PONT-001: efeito por construção.
- Efeito menor que o assumido nas premissas: exigir mais tarefas.
- Variância intra-tarefa alta do agente: medianas por tarefa com 3 execuções
  ainda podem ser ruidosas.

## Lacunas

- Tokens de modelo: [DESCONHECIDO]. A superfície interativa do Hermes 0.20.1
  não expõe usage. O piloto v1 registra a mesma lacuna.
- Aceite e rubrica: poder insuficiente em 16 tarefas. Ou aceitar efeito grande,
  ou subir para 30+ tarefas, ou tratar como exploratório.

## Script de pré-registro

`tools/curupira/power_analysis_preregister.py` calcula os mesmos números e
emite JSON de pré-registro. Rode antes de coletar qualquer dado:

```bash
python3 tools/curupira/power_analysis_preregister.py \
  --n-tasks 16 --output docs/hermes-case-study/prereg-v1.json
```
