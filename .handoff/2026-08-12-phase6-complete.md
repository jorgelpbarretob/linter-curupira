# Handoff — Phase 6 complete

**Proxima sessao:** preparar o gate da Fase 7 sem implementar antes de aprovação
**Data:** 2026-08-12
**Status:** aguardando decisão do humano

## Goal

Construir `ste-lint` incrementalmente como linter local-first e rastreável para
preocupações detectáveis da ASD-STE100 Issue 9. As Fases 1–6 estão concluídas;
o próximo incremento possível é o fixer seguro da Fase 7.

## Current state

- A implementação da Fase 6 está ancorada em
  `aa227c842b23496ad7b8ad21c4e42878157b3c9b` (`Complete phase 6 optional NLP`);
  o commit deste handoff vem depois sem alterar código.
- Fase 6 passou com 204 testes base e 3 skips NLP esperados; o ambiente NLP
  pinado passou 208 testes, Ruff, mypy e o gate offline.
- As sete regras permanecem `preview/info` e desabilitadas por padrão.
- `.serena/` é artefato local não rastreado, preexistente e fora do escopo; não
  stagear nem remover.

## Reference artifacts

- plano: `PLANS.md` — Fases 1–6 concluídas; Fase 7 aguarda aprovação.
- decisão: `docs/adr/0014-optional-nlp-backend-and-model.md` — contrato NLP aceito.
- métricas: `docs/f6-evaluation.md` — matriz, Wilson e abstenções das regras NLP.
- validação: `docs/f6-validation.md` — comandos, resultados e riscos restantes.
- commit: `https://github.com/jorgelpbarretob/linter-ASD-STE100/commit/aa227c842b23496ad7b8ad21c4e42878157b3c9b`.

## Decisions made this session

- spaCy 3.8.15 e `en_core_web_sm` 3.8.0 são opcionais, locais e pinados; o
  caminho base não possui dependência runtime obrigatória. ADR: `docs/adr/0014-optional-nlp-backend-and-model.md`.
- `STE-I9-VOICE-001` e `STE-I9-NOTE-001` permanecem `preview`: o seed teve zero
  FP/FN, mas os limites inferiores Wilson de 0.510 e 0.610 são insuficientes
  para promoção.
- Revisão independente usa `cursor-agent --mode ask --model composer-2.5-fast`;
  a rodada final aprovou lógica, abstenção e offsets.
- O fluxo solicitado pelo mantenedor é commit e push automáticos ao concluir
  cada fase, diretamente em `main`; não abrir PR sem novo pedido.

## Decisions pending

| Decisão | Quem decide | Bloqueia? |
|---|---|---|
| Autorizar início da Fase 7 e o trabalho de contrato/ADR do fixer | mantenedor | sim |

## Failed attempts

- Embutir todos os arquivos em uma única chamada do Cursor excedeu o limite de
  argumentos do Windows; dividir revisão de arquitetura e regras em prompts
  menores funcionou.
- `uv tree --no-dev` mostrou o grafo opcional do lock mesmo após sync base; para
  provar isolamento, usar probe de módulos instalados e inspecionar METADATA do
  wheel.

## Next step (WIP=1)

**Acao unica:** obter aprovação explícita do mantenedor para iniciar a Fase 7 e
então propor o contrato/ADR mínimo do fixer seguro.

**Pre-condicoes:** nenhuma implementação, ID de fixer, schema de edição ou
comando `ste fix` antes do GO humano.

**Definition of done:** escopo da Fase 7 e decisões difíceis de reverter
documentados e aprovados; só então iniciar TDD.

## Suggested skills

- `spec-driven-development` — formalizar DoR, invariantes e gate humano do fixer
  antes de tocar no contrato de edições.
