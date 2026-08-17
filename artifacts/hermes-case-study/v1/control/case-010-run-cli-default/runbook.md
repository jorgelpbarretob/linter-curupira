# Runbook — preflight de documentação

## Objetivo
Garantir ambiente e lint de prosa antes de abrir PR de docs.

## Fluxo

1. **Instalar**  
   Confirme a toolchain do time. Se faltar, instale `curupira`.

2. **Lint**  
   Em cada PR de documentação:

   ```bash
   curupira lint docs/**/*.md --enable-rule CURUPIRA-PT-PONT-001
   ```

   Checklist falha se o exit code for diferente de 0.

3. **Corrigir**  
   Se houver finding, ajuste só a prosa (não altere código). Rode o lint de novo até limpar.

4. **Anexar JSON**  
   Salve a saída JSON no ticket.

5. **Abrir PR**  
   Abra o PR só com lint limpo e checklist marcado.

## Extras

- Se o documento for procedimento operacional, peça leitura em voz alta a um segundo revisor.
- Não commite segredos.
- Não rode semantic-review sem autorização explícita.
