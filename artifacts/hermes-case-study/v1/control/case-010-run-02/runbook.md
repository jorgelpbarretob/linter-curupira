# Runbook — preflight de docs

## Objetivo
Garantir docs legíveis no PR com a toolchain do time (Curupira).

## Fluxo

1. **Instalar**  
   Se faltar a toolchain, instale `curupira`.

2. **Lint**  
   Em cada PR de documentação:
   ```bash
   curupira lint docs/**/*.md --enable-rule CURUPIRA-PT-PONT-001
   ```
   Checklist falha se `exit != 0`.

3. **Corrigir**  
   Se houver finding, ajuste só a prosa (não altere código). Repita o lint até limpar.

4. **Anexar JSON**  
   Salve a saída JSON no ticket.

5. **Abrir PR**  
   Só depois do lint limpo e do checklist marcado.

## Extras
- Procedimento operacional: peça leitura em voz alta a um segundo revisor.
- Não commite segredos.
- Não rode semantic-review sem autorização explícita.
