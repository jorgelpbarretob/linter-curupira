# Piloto de variância — estudo Hermes × Curupira

Status: concluído
Data: 2026-08-17
Autor: Athena (perfil athena)

## Objetivo

Validar a captura de tokens na rota one-shot antes da grade completa e
estimar a variância intra-tarefa para calibrar o número de execuções por
célula.

## Desenho executado

- 2 casos: case-007 (revisao-dificil) e case-008 (incidente-dificil).
- 2 condições: controle (sem Curupira) e tratamento (com curupira-preflight).
- 3 execuções por célula. Total: 12 sessões. Modelo qwen3.8-max, reasoning low.
- Rota: `hermes -z PROMPT --usage-file U --in WORK --reasoning low --yolo`.
  O tratamento adiciona `--skills curupira-preflight`.

## Achado de infra [MEDIDO]

A rota `hermes chat -q ... --usage-file` não emite o arquivo de usage neste
build (0.20.1). A rota one-shot `hermes -z PROMPT --usage-file` emite uso
completo: input_tokens, output_tokens, reasoning_tokens, cache_read_tokens,
total_tokens, api_calls, model e session_id.

Consequência: o harness oficial `run_case_arm.py` usa `chat -q` e ficará sem
tokens enquanto não migrar para `-z`. O piloto valida `-z` como rota do estudo.

## Qualidade da captura [MEDIDO]

- 12/12 execuções com usage completo. Zero artefatos ausentes.
- Fonte: `pilot-runs.json`, campo `capture.ok = true`.

## Variância intra-tarefa (CV médio por condição) [MEDIDO]

| Métrica | Controle CV% | Curupira CV% |
|---|---:|---:|
| input_tokens | 45,9 | 14,5 |
| output_tokens | 34,5 | 27,1 |
| total_tokens | 11,8 | 7,8 |
| api_calls | 12,1 | 7,7 |
| wall_seconds | 18,0 | 15,7 |

O controle varia muito mais em input_tokens (CV 45,9%). Três execuções por
célula estão justificadas para estabilizar a mediana. Reduzir para 1 ou 2
inviabilizaria a comparação de tokens.

## Direção preliminar (medianas por caso) [MEDIDO]

case-007 (n=3 por célula):

| Métrica | Controle | Curupira |
|---|---:|---:|
| input_tokens | 3.592 | 7.144 |
| output_tokens | 3.399 | 4.631 |
| total_tokens | 103.261 | 211.841 |
| api_calls | 4 | 8 |
| wall_seconds | 83,6 | 118,0 |
| findings residuais | 0 | 0 |
| chars do artefato | 794 | 779 |
| palavras/sentença | 4,22 | 4,17 |

case-008 (n=3 por célula):

| Métrica | Controle | Curupira |
|---|---:|---:|
| input_tokens | 3.044 | 5.935 |
| output_tokens | 1.768 | 2.870 |
| total_tokens | 125.836 | 184.548 |
| api_calls | 5 | 7 |
| wall_seconds | 63,4 | 89,0 |
| findings residuais | 0 | 0 |
| chars do artefato | 636 | 619 |
| palavras/sentença | 5,92 | 5,00 |

## Achado crítico [MEDIDO]

O braço controle zerou findings residuais em todas as 6 execuções, sem
Curupira. O modelo em uso (qwen3.8-max, reasoning low) já corrige ponto e
vírgula por conta própria quando instruído a melhorar legibilidade.

Consequências para o estudo:

1. O desfecho primário aprovado (achados residuais) tem poder estatístico,
   mas pode ter poder de discriminação zero neste modelo: se ambos os braços
   convergem para 0, a hipótese primária vira empate por construção.
2. A diferença real fica em tokens e legibilidade. No piloto, o tratamento
   custou ~2x input_tokens e ~1,5x output_tokens com ganho marginal de
   legibilidade (chars -2%, palavras/sentença -5%).
3. O objetivo de produto declarado (baixar tokens de entrada e saída) está,
   no piloto, na direção contrária ao tratamento.

## Decisão

- Manter 3 execuções por célula: variância alta no controle exige isso.
- Manter a rota `-z` com `--usage-file`.
- Escalar o achado crítico ao mantenedor antes da grade completa de 96
  sessões. Opções: (a) aceitar findings como gate e mover tokens/legibilidade
  para primário; (b) criar casos onde o controle comprovadamente falha
  (modelo ou instrução mais fraca); (c) congelar o estudo como evidência de
  que o modelo já resolve a regra sem preflight.
- Não disparar a grade completa sem essa decisão.

## Limitações

- n=3 por célula e 2 casos: só piloto. Nenhum teste de hipótese aplicado.
- Um único modelo e um único nível de reasoning. Generalização não testada.
- total_tokens inclui reasoning_tokens; input/output são as métricas limpas.
