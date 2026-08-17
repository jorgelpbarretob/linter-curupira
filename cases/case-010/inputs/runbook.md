# Runbook legado — preflight docs

O revisor deve garantir o ambiente com a toolchain do time; instalar hermes-lint se faltar; em cada PR de documentação rodar hermes-lint docs/**/*.md --enable-rule HERMES-PT-PONT-001 e falhar o checklist se exit != 0; quando houver finding, ajustar a prosa sem alterar código e repetir até limpar; salvar a saída JSON no ticket; se o documento for procedimento operacional, pedir leitura em voz alta por um segundo revisor; abrir PR só depois do lint limpo e do checklist marcado; não commitar segredos; não rodar semantic-review sem autorização explícita.
