# Resultados — protocolo v1

Status: **primeira rodada oficial registrada**

## Rodada oficial case-001-run-01 (2026-08-16)

| Métrica | Controle | Curupira | Delta |
|---|---:|---:|---:|
| Achados residuais PONT-001 | 0 | 0 | 0 |
| Tags preservadas | sim | sim | — |
| Chamadas de ferramenta | 10 | 4 | -6 |
| Mensagens | 16 | 9 | -7 |
| API calls | 5 | 4 | -1 |
| Tokens in/out | 31118/943 | 29216/401 | -1902/-542 |
| Wall time | 69 s | 19 s | -50 s |
| curupira invocado | não | sim (lint exit 0) | — |
| Aceite (auto) | aceito | aceito | — |

Sessões: controle `20260816_224657_f96c25` · tratamento `20260816_224828_f00058`.
Modelo: grok-4.5 · reasoning low · Hermes 0.20.1.
Detalhe: `artifacts/hermes-case-study/v1/case-001-run-01-summary.json`.

Interpretação curta: residual empatado em 0. Tratamento mais barato e com gate lint real.
Não generalizar (n=1).


Preencha só após congelar casos e executar o protocolo sem alterar regras no meio.

## Template de cabeçalho

- Casos: N
- Rodadas por condição: R
- Avaliações cegas: 2 por artefato
- Artefatos aceitos na 1ª revisão: controle a/b · Curupira c/d
- Mediana de achados residuais: controle X · Curupira Y
- Mediana de chamadas: controle X · Curupira Y
- Mediana de tempo até aceite: controle X · Curupira Y
- Erros técnicos críticos: controle X · Curupira Y
- Limitações: ...

## Casos em que Curupira não ajudou

Listar explicitamente. Obrigatório no relatório público.


## Batch 2026-08-16 (run-02/03 + case-003/004)

Fonte: `artifacts/hermes-case-study/v1/batch-2026-08-16-summary.json`

### case-001 (3 runs pareadas)

| Métrica (mediana) | Controle | Curupira |
|---|---:|---:|
| Achados residuais | 0 | 0 |
| Tool calls | 3 | 5 |
| Tokens totais | 28845 | 30267 |
| Wall s | 21.8 | 23.1 |
| Requisitos/tags | 3/3 ok | 3/3 ok |
| Lint invocado no tratamento | — | 3/3 sim |

Nota: run-01 do controle foi outlier (10 tools, 69 s) por exploração de cwd. A mediana de 3 runs é mais estável.

### case-003 run-01

| | Controle | Curupira |
|---|---:|---:|
| Residual | 0 | 0 |
| Tools | 3 | 4 |
| Tokens | 28624 | 29640 |
| Wall s | 21.2 | 22.5 |
| Requisitos (V-90/R-02/S-11) | ok | ok |
| Lint no tratamento | — | sim |

### case-004 run-01

| | Controle | Curupira |
|---|---:|---:|
| Residual | 0 | 0 |
| Tools | 3 | 4 |
| Tokens | 28562 | 29389 |
| Wall s | 16.8 | 19.3 |
| Migração CLI (sem hermes-lint) | ok | ok |
| Lint no tratamento | — | sim |

Observação case-004: controle escreveu `curupira doc.md` (faltou subcomando `lint`). Tratamento escreveu `curupira lint doc.md` (correto). Residual PONT-001 não pega esse erro de CLI.

### Leitura agregada

1. Residual PONT-001 empatou em 0 em todos os pares desta leva.
2. Tratamento custa cerca de +1 a +2 tool calls (o lint) e leve aumento de tokens/tempo.
3. Em tarefas óbvias o modelo já remove `;` sem ferramenta.
4. Valor do preflight nesta amostra: **gate verificável** e, no case-004, comando CLI mais fiel.
5. Ainda falta: repetições em 003/004, avaliação cega humana, cases onde o controle deixe residual >0.


## Batch hard 2026-08-16 (case-007..010) — foco tokens + legibilidade

Fonte: `artifacts/hermes-case-study/v1/batch-hard-2026-08-16-summary.json`

Input residual PONT-001: 8–9 findings. Artefatos finais: residual 0 nos dois braços.

| Case | Δ tokens (T−C) | Winner tokens | Winner legibilidade | max_sent C→T | chars C→T |
|---|---:|---|---|---|---|
| 007 | +16376 | control | curupira | 16→14 | 774→771 |
| 008 | +884 | control | curupira | 12→11 | 574→543 |
| 009 | +528 | control | control | 14→16 | 500→597 |
| 010 | +949 | control | control | 12→15 | 794→816 |

### Leitura alinhada ao objetivo

1. **Tokens de sessão:** tratamento perdeu os 4 pares. A skill no contexto custa input.
2. **Legibilidade:** tratamento ganhou 007 e 008 (frases mais curtas / listas). Perdeu 009 e 010.
3. **Residual:** empatado em 0. O modelo já limpa `;` sem lint nestes casos.
4. **Implicação de produto:** para baixar tokens, enxugar a skill ou chamar só o binário `curupira` sem preload longo. O gate lint ainda valida legibilidade estrutural.

### Próximo experimento sugerido

A/B com tratamento **sem** `-s` preload. Só instrução curta para rodar o CLI. Medir se Δ tokens vira negativo mantendo legibilidade.


## Experimento 3 vias run-02 (control × skill × CLI)

Fonte: `artifacts/hermes-case-study/v1/batch-3way-cli-run-02-summary.json`

Hipótese: CLI-only (sem dump da skill) reduz tokens vs braço skill e mantém legibilidade.

### Por case

| Case | tok control | tok skill | tok CLI | winner tok | winner legib. | Δ CLI−skill | Δ input CLI−skill |
|---|---:|---:|---:|---|---|---:|---:|
| 007 | 29028 | 31532 | 31184 | control | **cli** | -348 | -591 |
| 008 | 22781 | 30104 | 30405 | control | **cli** | +301 | +268 |
| 009 | 29795 | 29971 | 29225 | **cli** | **cli** | -746 | -746 |
| 010 | 29384 | 30738 | 30022 | control | control | -716 | -670 |

Residual PONT-001: **0 em todos os 12 braços**.

### Agregado

- residual all zero: sim
- mean Δ tokens CLI vs skill: **-377**
- mean Δ input CLI vs skill: **-435**
- mean Δ tokens skill vs control: **+2839**
- mean Δ tokens CLI vs control: **+2462**
- token wins: control 3 · CLI 1 · skill 0
- readability wins: CLI 3 · control 1 · skill 0

### Conclusão operacional

1. **Skill preload é o pior em tokens** (0 wins). Custa contexto.
2. **CLI-only é melhor que skill em tokens** na média (−377 total, −435 input).
3. **Control ainda vence tokens** na maioria (3/4). O modelo limpa prosa sem lint.
4. **CLI-only vence legibilidade** (3/4). Gate lint + instrução curta ajuda o artefato.
5. Para o objetivo tokens↓ + legibilidade↑: preferir **CLI mínima**, não skill longa no contexto.
6. Para tokens mínimos absolutos: control às vezes ganha, mas sem gate verificável de lint na execução.

### Desenho recomendado de produto

- default: instrução curta + `curupira lint` (CLI)
- skill completa: só sob `/curupira-preflight` explícito ou docs longos
- não pré-carregar SKILL.md em toda sessão de edição curta

## Battery default CLI-min — run-cli-default

Default aplicado: **instrução curta + CLI** (sem skill preload).
Comparação control × cli: cases 001, 003, 004, 007–010.

Fonte: `artifacts/hermes-case-study/v1/battery-run-cli-default-summary.json`

| Case | res C/T | tok C | tok CLI | Δ tok | Δ in | Δ out | winner tok | winner legib. | lint CLI |
|---|---|---:|---:|---:|---:|---:|---|---|---|
| case-001 | 0/0 | 29106 | 29616 | 510 | 458 | 52 | control | tie | True |
| case-003 | 0/0 | 28776 | 29246 | 470 | 356 | 114 | control | control | True |
| case-004 | 0/0 | 29124 | 29161 | 37 | 51 | -14 | control | control | True |
| case-007 | 0/0 | 29547 | 29730 | 183 | 130 | 53 | control | control | True |
| case-008 | 0/0 | 23624 | 29857 | 6233 | 6184 | 49 | control | control | True |
| case-009 | 0/0 | 29457 | 14033 | -15424 | -15566 | 142 | cli | control | True |
| case-010 | 0/0 | 29789 | 52234 | 22445 | 22405 | 40 | control | cli | True |

### Agregado

- pares: 7
- residual all zero: True
- mean Δ tokens CLI−control: **2064.9**
- mean Δ input: **2002.6**
- mean Δ output: **62.3**
- mean Δ chars artefato: **39.1**
- token wins: {'control': 6, 'cli': 1, 'tie': 0}
- readability wins: {'control': 5, 'cli': 1, 'tie': 1}
- CLI invocou lint: 7/7

### Leitura

1. Default CLI-min está ativo nas skills e no runner.
2. Residual permanece 0=0 nestes cases.
3. Custo extra de tokens vs control é o preço do gate lint verificável.
4. Legibilidade favorece CLI quando o score automático ganha.
5. Skill preload continua fora do default (pior em tokens no experimento 3 vias).


## Ações das recomendações operacionais (2026-08-16)

1. CLI-min mantido como default (skills + runner).
2. Skill preload **não** restaurado como default.
3. Split gate×qualidade documentado: `success-criteria-split.md`.
4. Outliers 008/009/010 investigados: `outlier-investigation-008-010.md` (+ JSON). Permanecem no agregado v1.
5. Release v1 **fechada**: `releases/v1-cli-default-2026-08-16.json` e `artifacts/hermes-case-study/v1-sealed/`.
6. Bateria v2 aberta: `protocol-v2.md` + `artifacts/hermes-case-study/v2/battery-run-v2-01-summary.json`.
7. Pacote cego: `artifacts/hermes-case-study/v2/blind/` (A/B + template + key).

### Outliers (síntese)

| Case | Δ tok | Achado |
|---|---:|---|
| 008 | +6233 | tools parecidos; input CLI maior; 2 terminais no CLI (ls+lint) |
| 009 | -15424 | CLI mais barato; control explorou mais; artefato CLI até maior |
| 010 | +22445 | tools 4=4; input CLI ~1.77× com tool bytes similares (contexto/accounting) |

### Battery v2-01 (control × CLI-min, n=11)

- residual all zero: True
- gate operacional CLI pass: 11/11
- mediana Δ tokens: **5914**
- mediana Δ input: **6087**
- mediana Δ output: **-16**
- token wins: {'control': 10, 'cli': 1, 'tie': 0}
- readability auto wins: {'control': 4, 'cli': 6, 'tie': 1}

Revisão cega humana: pendente (`v2/blind/scores-template.json`).

### Blind pilot reviewer A

Scores gravados em `artifacts/hermes-case-study/v2/blind/scores-reviewer-A-pilot.json`.
Relatório: `docs/hermes-case-study/blind-review-pilot-A.md`.
Preferência pós-unblind: ver agregado no relatório (CLI vs control em clareza/classe).

### Painel Kimi 2.7 + Maritaca (com tokens)

- JSON: `artifacts/hermes-case-study/v2/blind/scores-panel-kimi-maritaca.json`
- Relatório: `docs/hermes-case-study/panel-kimi-maritaca-tokens.md`
- Cada preferência A/B inclui tokens de sessão control/cli e tokens do revisor.

