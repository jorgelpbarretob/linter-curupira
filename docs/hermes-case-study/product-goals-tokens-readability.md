# Objetivos de produto — tokens e legibilidade

Status: ativo no estudo a partir do lote case-007+
Data: 2026-08-16

## KPI primários (ordem)

1. **Tokens de sessão** (input + output do Hermes). Menor é melhor no pareamento.
2. **Legibilidade do artefato** para o usuário ou operador. Ver score automático abaixo.
3. **Residual lint** das regras do aceite. É gate de qualidade. Não é o único sucesso.

## KPI secundários

- tool calls e wall time
- requisitos técnicos (tags, fatos)
- fidelidade de comandos CLI quando aplicável

## Score de legibilidade (automático, v1)

Calculado no artefato final:

- `chars` e `words`
- `semicolon_count` em prosa (proxy. No aceite deve ser 0)
- `avg_sentence_words`
- `max_sentence_words`
- `bullet_or_numbered_ratio` (linhas de lista / linhas totais)
- `delta_chars_vs_input` (negativo = encolheu)

Heurística de “mais legível” no pareamento (sem humano):

1. residual menor ou igual
2. se residual empatado: menor `max_sentence_words`
3. depois maior ratio de lista
4. depois menor `chars`

Humano continua soberano na rubrica cega 1–5 de clareza.

## Implicação no tratamento

O braço Curupira deve otimizar para:

- frases curtas e passos explícitos
- lint exit 0
- evitar prosa longa desnecessária

O controle não recebe a skill nem o gate de lint.

## Achado operacional (batch hard 2026-08-16)

Com skill pré-carregada (`-s curupira-preflight`), o tratamento tende a **aumentar tokens de input** de sessão.
Para o KPI de tokens, o desenho de produto precisa de skill enxuta ou lint sob demanda sem despejar o SKILL inteiro no contexto.
Legibilidade do artefato pode melhorar mesmo com tokens de sessão piores.


## Experimento 3 vias (run-02)

Comparou control × skill preload × CLI-only nos cases 007–010.

Resultado principal: CLI-only reduz tokens vs skill (média ≈ −435 input).
Control ainda costuma ser o mais barato em tokens.
CLI-only venceu legibilidade em 3/4.


## Default de runtime (decidido 2026-08-16)

**Default = instrução curta + CLI `curupira lint`.**
Skill longa não é pré-carregada.
Skill completa só sob pedido explícito ou coleta improve.
