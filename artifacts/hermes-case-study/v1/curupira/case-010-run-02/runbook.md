# Runbook — preflight de docs

## Objetivo

Garantir ambiente e prosa PT-BR antes de abrir PR de documentação.

## Fluxo

1. **Instalar** — se faltar a toolchain do time, instale `curupira`.
2. **Lint** — em cada PR de documentação, rode:

```bash
curupira lint docs/**/*.md --enable-rule CURUPIRA-PT-PONT-001 --format json
```

3. **Falhar checklist** — se `exit != 0`, o checklist não passa.
4. **Corrigir** — com finding, ajuste a prosa sem alterar código. Repita o lint até limpar.
5. **Anexar JSON** — salve a saída JSON no ticket.
6. **Segundo revisor** — se o documento for procedimento operacional, peça leitura em voz alta a um segundo revisor.
7. **Abrir PR** — só depois do lint limpo e do checklist marcado.

## Restrições

- Não commitar segredos.
- Não rodar semantic-review sem autorização explícita.
