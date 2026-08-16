# PT4 — corpora pré-inferência

Status: Pending independent human review
Date: 2026-08-16

Este diretório contém somente insumos congelados antes da primeira inferência
do bake-off:

- o split oficial de teste UD Portuguese PetroGold `r2.18`, sem alteração;
- a licença upstream CC BY-SA 4.0;
- o manifesto de proveniência, integridade e contagens do split;
- a proposta autoral `pt4-offset-development-v1`, com 160 casos ainda
  `pending-human-review`;
- o ambiente de referência que será obrigatório para o futuro harness.

O SHA-256 da proposta serve para impedir alteração silenciosa durante a
revisão. Ele **não** é o hash canônico de um corpus aceito. Uma segunda pessoa
deve aprovar 100% dos casos sem consultar saída de candidato NLP; somente
depois disso um incremento separado poderá congelar o corpus canônico.

Nenhum arquivo deste diretório autoriza inferência, implementa harness ou
adapter, seleciona backend, abre PT5 ou reabre `HERMES-PT-PONT-001`.

O conteúdo PetroGold preserva sua licença original. Ao redistribuí-lo, mantenha
`LICENSE-UD-Portuguese-PetroGold.txt`, atribuição ao projeto Universal
Dependencies e as obrigações CC BY-SA 4.0.
