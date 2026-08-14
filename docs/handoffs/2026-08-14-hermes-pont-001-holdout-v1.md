# Handoff — Hermes após o holdout v1 de PONT-001

**Próxima sessão:** abrir PT4 com aprovação operacional delegada ao Grok
**Data:** 2026-08-14
**Status:** PONT-001 fechado em `preview`; próximo WIP ainda não aberto

## Goal

Continuar o Hermes como linter pt-BR local-first depois de encerrar a primeira
avaliação independente de `HERMES-PT-PONT-001`. A regra permanece utilizável
por opt-in em `preview`, enquanto o próximo WIP avança para PT4 sem usar os
erros do holdout para ajustar o detector.

## Current state

PT3 foi implementado, revisado pelo Grok e congelado antes da primeira execução
no holdout. A execução cega foi selada antes da abertura dos labels; o Grok,
atuando por delegação do mantenedor, aprovou a abertura e decidiu `preview`
depois do score. O resultado foi 148 TP, 4 FP, 15 FN e 242 TN: precisão
0,973684, limite inferior Wilson 95% 0,934296 e recall 0,907975.

A recomputação independente confirmou todas as métricas agregadas com deltas
zero. A suíte final passou com 307 testes e 4 skips NLP esperados; Ruff,
formatação, mypy, smoke offline, hashes e `git diff --check` passaram. O bundle
temporário do Grok foi removido.

## Reference artifacts

- avaliação canônica:
  `/home/jorge/linter-ASD-STE100/docs/hermes-pont-001-holdout-evaluation-v1.md`;
- governança e delegação:
  `/home/jorge/linter-ASD-STE100/docs/hermes-governance.md`;
- plano vigente: `/home/jorge/linter-ASD-STE100/PLANS.md`;
- replan pt-BR:
  `/home/jorge/linter-ASD-STE100/docs/pt-br-product-replan.md`;
- revisão e freeze PT3:
  `/home/jorge/linter-ASD-STE100/docs/hermes-pt3-grok-code-review.md`;
- executor, scorer e auditor:
  `/home/jorge/linter-ASD-STE100/tools/hermes/`;
- manifesto congelado do detector:
  `/home/jorge/linter-ASD-STE100/corpus/hermes/pont-001-detector-freeze-v1.json`.

Artefatos privados continuam em
`/home/jorge/.hermes/holdout-custody/`. Hashes principais:

- detector: `972a1c67e14c4316afc388df523838f4338a60d5866ab13710d19bda1fc016b9`;
- execução: `eac833da22cf7c6d81a53a273cd067e32bbb734af075d0bb92f5b766db142333`;
- métricas: `ec38740c65dd2c5d081f8e1080f637264f237e121580fd29c322d1a971144e37`;
- auditoria: `195baf37109a4db937ce40ff1707cbfa851548a79bb433110e6aa0d727306fed`;
- aprovação para abrir labels:
  `fba62fb4d1f87336e9b721c406b26dee7a97591e588599120589611cee424eb8`;
- decisão pós-holdout:
  `b0e6f0c62ef7656a053dbd6222492267a322dfb4b17d32130acb59039009f623`.

## Decisions made this session

- Grok aprova gates operacionais rotineiros em nome do mantenedor → o agente
  prossegue sem pedir confirmação humana a cada etapa quando o parecer
  estruturado for favorável e os artefatos forem auditáveis.
- `HERMES-PT-PONT-001` permanece `preview` → o ponto de precisão passou, mas o
  limite Wilson e o gate de zero falso positivo falharam.
- O holdout v1 está consumido → os 4 FP e 15 FN não entram em implementação,
  fixtures, prompts ou thresholds neste ciclo.
- Uma futura abertura desses 19 erros exige decisão explícita de `rework` → eles
  viram challenge e qualquer promoção posterior exige novo holdout independente.

## Limites da delegação

Não interromper o mantenedor para gates rotineiros aprovados pelo Grok. Parar
somente diante de licença ou segredo não resolvido, novo tipo de egress,
ampliação de orçamento externo, ação irreversível/publicação, mudança normativa
ou divergência técnica substancial. O Grok não cria ground truth sozinho nem
muda regra, threshold ou gates.

## Failed attempts — não repetir

- Executar o runner como arquivo direto falhou antes de ler documentos por
  `ModuleNotFoundError: tools`; executar como módulo a partir da raiz do repo.
- `uv run` está bloqueado porque o ambiente possui uv 0.12.0 e o projeto fixa
  0.11.14; enquanto não alinhar versões, usar o virtualenv com `PYTHONPATH=src`
  para smoke e `.venv/bin/python` para checks.
- `prime-quant` e `prime-quant-sync` não estão instalados; a auditoria existente
  usa somente stdlib, é independente do scorer e possui testes próprios.

## Próximos passos

### WIP=1 — ação imediata

**Ação:** abrir formalmente PT4, definindo o contrato mínimo da análise
linguística local pt-BR e o protocolo de bake-off, sem implementar uma regra
nova no mesmo incremento.

**Pré-condições:** reler `PLANS.md`, `docs/pt-br-product-replan.md` e os limites
de dependência/licença; manter PONT-001 e seu holdout fechados.

**Definition of done:** documento/ADR de PT4 especifica porta interna,
tokenização/sentenças/morfologia/dependências necessárias, mapeamento exato de
offsets, candidatos de backend, licenças, checksums, runtime sem download e
critérios quantitativos; parecer estruturado do Grok aprova o gate operacional.

### Sequência após o WIP=1

1. executar o bake-off somente com corpus pt-BR autorizado e separar evidência
   de desenvolvimento de qualquer futuro holdout;
2. escolher e pinar um backend somente se ele cumprir licença, offsets,
   reprodução offline e critérios quantitativos pré-registrados;
3. implementar a porta local em TDD, mantendo tipos do backend fora do domínio;
4. abrir uma única candidata PT5 depois do aceite de PT4, com novo corpus e
   gates próprios;
5. usar o Grok para as aprovações operacionais intermediárias e registrar cada
   parecer por hashes, modelo retornado, request/session IDs, tokens e custo.

## Suggested skills

- `tdd` — implementar a futura porta PT4 começando por contratos e offsets
  falhando, sem acoplar o domínio ao backend.
- `quantitative-review` — pré-registrar e auditar o bake-off antes de escolher
  o pipeline linguístico.
- `grounded-citations` — sustentar licença, capacidades e limitações dos
  backends avaliados em fontes primárias.
