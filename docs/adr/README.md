# Architecture Decision Records

Os ADRs deste diretório usam os estados `Proposed`, `Accepted`, `Superseded` e
`Rejected`. Os ADRs 001–006 foram aceitos explicitamente pelo mantenedor em
2026-08-12. Os ADRs 007, 008, 009 e 011 foram aceitos explicitamente pelo
mantenedor no gate inicial da Fase 3, na mesma data. O ADR-010 foi aceito
explicitamente pelo mantenedor no checkpoint de baseline da Fase 4.

O ADR-013 foi aceito explicitamente pelo mantenedor no checkpoint inicial da
Fase 5, após revisão independente com `cursor-agent` e `composer-2.5-fast`.

O ADR-014 foi aceito explicitamente pelo mantenedor no checkpoint inicial da
Fase 6, após duas revisões independentes com `cursor-agent` e
`composer-2.5-fast`.

O ADR-015 foi aceito explicitamente pelo mantenedor em 2026-08-13 após duas
revisões independentes com `cursor-agent` e `composer-2.5-fast`. Ele preserva o
fixer como somente `stable`; implementação/TDD continuam bloqueados até promoção
de uma regra, aprovação do primeiro provider e nova autorização explícita.

O ADR-016 foi aceito explicitamente pelo mantenedor em 2026-08-13. Ele encerra
a evolução da linha inglesa, torna pt-BR a única direção de produto e separa
`sabiazinho-4` como motor semântico de `sabia-4-thinking` como
avaliador rigoroso. As decisões inglesas anteriores permanecem históricas; seus
contratos independentes de idioma só podem migrar após novo gate.

O ADR-017 foi aceito explicitamente pelo mantenedor em 2026-08-13. Ele define a
identidade Hermes, o namespace `HERMES-PT-*`, Apache-2.0 para código e CC BY 4.0
para a especificação e conteúdo autoral identificado, sem relicenciar corpus de
terceiros.

O ADR-018 foi aceito explicitamente pelo mantenedor em 2026-08-13, junto com o
guia e 40/40 labels do piloto de `HERMES-PT-PONT-001`. Ele separa verdade,
revisão humana e saída do detector e mantém a primeira execução bloqueada até
gate próprio.

O ADR-019 foi aceito em 2026-08-16 pelo gate operacional delegado ao Grok, com
condições vinculantes pré-inferência registradas em
`docs/hermes-pt4-grok-opening-review.md`. Ele separa tokens de superfície de
palavras sintáticas, fixa o contrato de offsets e pré-registra um bake-off antes
da escolha de backend. Licença condicional continua sendo gate humano.

Uma mudança difícil de reverter não pode ser implementada enquanto o ADR
correspondente não estiver `Accepted`.
