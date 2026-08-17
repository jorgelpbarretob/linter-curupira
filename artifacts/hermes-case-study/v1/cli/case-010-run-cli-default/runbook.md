# Runbook — preflight docs

## Objetivo
Garantir docs legíveis antes do PR. Não alterar código de produto neste fluxo.

## Passos

1. Instalar
   - Confirme a toolchain do time.
   - Se faltar, instale `curupira`.

2. Lint
   - Em cada PR de documentação, rode:
   - `curupira lint docs/**/*.md --enable-rule CURUPIRA-PT-PONT-001`
   - Checklist falha se exit != 0.

3. Corrigir
   - Se houver finding, ajuste só a prosa.
   - Repita o lint até limpar.

4. Anexar JSON
   - Salve a saída JSON no ticket.

5. Abrir PR
   - Abra o PR só com lint limpo e checklist marcado.
   - Se o documento for procedimento operacional, peça leitura em voz alta por um segundo revisor.

## Restrições
- Não commitar segredos.
- Não rodar semantic-review sem autorização explícita.
