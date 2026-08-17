# Runbook — preflight de docs

## Objetivo
Garantir ambiente e lint de prosa PT-BR antes de abrir PR de documentação.

## Fluxo

1. **Instalar**
   - Confirme a toolchain do time.
   - Se faltar, instale `curupira`.

2. **Lint**
   - Em cada PR de documentação, rode:
     ```bash
     curupira lint docs/**/*.md --enable-rule CURUPIRA-PT-PONT-001 --format json
     ```
   - Checklist falha se exit != 0.

3. **Corrigir**
   - Com finding: ajuste só a prosa (não altere código).
   - Repita o lint até limpar.

4. **Anexar JSON**
   - Salve a saída JSON no ticket.

5. **Abrir PR**
   - PR só com lint limpo e checklist marcado.
   - Se o doc for procedimento operacional, peça leitura em voz alta a um segundo revisor.

## Restrições
- Não commitar segredos.
- Não rodar semantic-review sem autorização explícita.
