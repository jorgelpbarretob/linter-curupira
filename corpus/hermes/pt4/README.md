# PT4 — corpora pré-inferência

Status: Offset corpus frozen by unanimous model panel
Date: 2026-08-16

Este diretório contém somente insumos congelados antes da primeira inferência
do bake-off:

- o split oficial de teste UD Portuguese PetroGold `r2.18`, sem alteração;
- a licença upstream CC BY-SA 4.0;
- o manifesto de proveniência, integridade e contagens do split;
- a proposta autoral v2 com 160 casos e seu hash de submissão;
- o corpus canônico `pt4-offset-development-v1`, aprovado em 160/160 por
  Maritaca, Grok e Kimi 2.7;
- o ambiente de referência que será obrigatório para o futuro harness.

O SHA-256 da proposta impede alteração silenciosa durante o painel. O hash
canônico do corpus aceito é
`45716b0581ae7c90897a3d088953ac8efde13882e6c4ef7ecfa87c6764928f5d`.
O painel não recebeu saída de candidato NLP nem dados PONT-001.

Este congelamento autoriza implementar e validar o harness PT4. Ele não autoriza
adapter de produto, escolha de backend, PT5 nem reabertura de
`HERMES-PT-PONT-001`; inferência segue o gate próprio do protocolo.

O conteúdo PetroGold preserva sua licença original. Ao redistribuí-lo, mantenha
`LICENSE-UD-Portuguese-PetroGold.txt`, atribuição ao projeto Universal
Dependencies e as obrigações CC BY-SA 4.0.
