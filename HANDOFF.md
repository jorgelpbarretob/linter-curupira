# Handoff — gate de promoção de `STE-I9-LIST-001`

**Próxima sessão:** concluir a revisão independente de promoção sem alterar a regra
**Data:** 2026-08-13
**Status:** aguardando autorização explícita de egress para o revisor externo

## Goal

Decidir se `STE-I9-LIST-001` pode sair de `preview` após a iteração de recall
v2. A decisão deve permanecer separada de `safe_autofix` e da implementação do
fixer da Fase 7.

## Current state

- `main` está ancorada em `dd4c467` (`Complete phase 7 recall evaluation`).
- O holdout v2 congelado passou com 30 TP, 0 FP, 0 FN e 30 TN; o combinado tem
  104 TP, 0 FP, 9 FN e 82 TN, Wilson inferior 0,964 e zero emissões ambíguas.
- O mantenedor autorizou a revisão independente de promoção, mas nenhuma revisão
  externa foi executada: o controle de segurança bloqueou o envio do diff,
  código, testes, corpus e documentação ao Cursor sem autorização explícita do
  payload e destino.
- `STE-I9-LIST-001` continua `preview/info`, desabilitada por padrão e com
  `safe_autofix = false`; provider e TDD do fixer continuam bloqueados.

## Reference artifacts

- plano: `PLANS.md` — gates da Fase 7 e separação entre promoção e fixer.
- contrato de evidência: `docs/f7-list-evidence-expansion-plan.md` — Emenda 3 e
  critérios quantitativos.
- avaliação v2: `docs/f7-list-recall-v2-validation.md` — execução, tentativas
  abortadas, matriz, Wilson, caveats e validações.
- corpus congelado: `corpus/f7/vertical-list-holdout-v2.jsonl` e
  `corpus/f7/vertical-list-holdout-v2.sha256`.
- implementação a revisar: `src/ste_lint/rules/vertical_list_colon.py`.
- escopo do diff: `7bfd610..dd4c467`.

## Decisions made this session

- A avaliação quantitativa v2 foi aceita apenas como habilitadora da revisão;
  não promove automaticamente a regra.
- A revisão deve priorizar falsos positivos, abstenções, regiões Markdown,
  offsets, vazamento de evidência, aritmética e lacunas de teste.
- O fixer não faz parte desta revisão e exige gates e autorização próprios.

## Decisions pending

| Decisão | Quem decide | Bloqueia? |
|---|---|---|
| Autorizar o envio ao Cursor do diff `dd4c467`, código, testes, corpus e documentação relacionados, usando `composer-2.5-fast`, somente para revisão de promoção | mantenedor | sim |
| Promover `STE-I9-LIST-001` após o parecer independente | mantenedor | sim |

## Failed attempts

- `cursor-agent --mode ask --model composer-2.5-fast` não iniciou: o controle de
  segurança rejeitou o egress porque a autorização anterior não nomeava o
  payload exato nem o destino. Nenhum conteúdo foi enviado e nenhum arquivo foi
  alterado.

## Next step (WIP=1)

**Ação única:** obter autorização explícita de egress e executar a revisão
independente read-only do diff `7bfd610..dd4c467` no Cursor.

**Pré-condições:** o mantenedor autorizar nominalmente o Cursor, o payload e o
uso exclusivo para revisão de promoção.

**Definition of done:** parecer com findings por severidade e linhas exatas,
veredito de promoção e separação explícita do fixer; nenhuma mudança de metadata
antes de nova decisão humana.

## Suggested skills

- `codex-code-review` — aplicar o contrato de findings por severidade e riscos
  ao usuário ao parecer externo.
