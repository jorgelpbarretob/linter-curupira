# Gate documental da Fase 7

Status: approved
Data: 2026-08-13
Escopo: spec e ADR do fixer seguro; nenhuma implementação ou TDD
Approved by: project maintainer, 2026-08-13

## Artefatos revisados

- [`f7-fixer-spec.md`](f7-fixer-spec.md)
- [`ADR-015`](adr/0015-safe-fixer-contract.md)
- seção da Fase 7 em [`PLANS.md`](../PLANS.md)

## Revisão independente

O mantenedor autorizou o envio de um conjunto limitado de arquivos ao
`cursor-agent`. Duas rodadas foram executadas em modo `ask`, somente leitura,
com `composer-2.5-fast`.

A primeira rodada aprovou a direção, mas bloqueou o aceite até resolver:

1. categoria indefinida de conflito entre edits;
2. identidade de arquivo, hash de bytes crus e BOM;
3. perfil determinístico e testável do diff unificado;
4. diferença entre garantia runtime e regressões controladas pelo corpus.

A revisão foi atualizada para rejeitar qualquer overlap, exigir round-trip UTF-8
byte-exato, congelar headers/contexto/newlines do diff e separar remoção dos
alvos em runtime do gate de regressão da suíte. Também foram fechados flags de
CLI, output de apply, no-op sem backup, spans transformados e inventário
arquitetural.

A segunda rodada confirmou os quatro bloqueios resolvidos, não encontrou
bloqueio material remanescente e respondeu **YES** para aprovação documental.
Ela confirmou também que implementação e TDD permanecem bloqueados.

## Validações locais

- `git diff --check`;
- verificação de que nenhuma mudança pertence a `src/` ou `tests/`;
- scan dos paths alterados por extensões normativas/protegidas;
- revisão de consistência com ADR-002, ADR-004, ADR-010, ADR-011 e o invariante
  de `RuleMetadata.safe_autofix`.

Testes Python não são necessários para este gate puramente documental e não
foram executados. O checkout não tem `.venv`, e o `uv` global é 0.12.0 enquanto
o projeto exige 0.11.14; nenhum ambiente foi alterado para esta revisão.

## Decisão do mantenedor

O mantenedor aceitou a spec e o ADR-015 como contrato documental em 2026-08-13.
Esse aceite não autoriza TDD, que não começa enquanto não houver:

1. regra determinística promovida a `stable` com evidência suficiente;
2. precondição e substituição exata do primeiro provider aprovadas;
3. nova autorização explícita para iniciar TDD.

`STE-I9-LIST-001` é somente candidata para nova avaliação; não está promovida e
não recebeu autofix.
