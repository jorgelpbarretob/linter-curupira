# Fase 0 — registro de prontidão

Status: concluída; Fase 1 autorizada
Checkpoint: F1, fundação do pacote
Atualizado em: 2026-08-12

## Escopo deste checkpoint

Este checkpoint transforma o plano em decisões auditáveis sem iniciar a Fase 1.
Ele não autoriza criar o pacote Python, implementar regras ou importar conteúdo
da ASD-STE100.

## Estado observado antes da Fase 1

- O diretório contém documentos de planejamento e ainda não é um repositório Git.
- Não existem pacote Python, testes, catálogo preenchido ou corpus.
- A página oficial consultada em 2026-08-12 identifica a edição vigente como
  Issue 9, de 2025-01-15.
- Nenhum arquivo normativo ou vocabulário oficial foi adicionado ao diretório.

## Reconciliação do plano v2 com o contrato do projeto

| Tema | Direção para F0 | Estado |
|---|---|---|
| Plano executável | `PLANS.md` permanece o gate canônico; o plano v2 fornece os mecanismos antifrágeis | aceito para F0 |
| Taxonomia pública | `deterministic`, `nlp`, `semantic`, `human-review` | obrigatório |
| `pure` e `pos_dependent` do v2 | capacidades internas de uma regra, não novos tipos públicos | proposta no ADR-005 |
| Ground truth | decisão humana; LLM pode somente gerar ou triar candidatos | obrigatório |
| Exemplos por regra | adotar inicialmente o gate mais forte do v2: 5 violações, 5 não violações e 3 edge cases | proposta |
| Harness antifrágil | contratos, corpus e eval antes da primeira regra; fuzz e mutation entram quando houver código executável | proposta |
| Tamanho do MVP | 3–5 regras estáveis; candidatas adicionais podem permanecer `planned` ou `preview` | proposta |

## Gate da Fase 0

- [x] Postura de compliance/copyright proposta.
- [x] Processo de revisão normativa proposto.
- [x] Schema preliminar do catálogo proposto.
- [x] ADRs 001–005 abertos como `Proposed`; ADR-006 aceito.
- [x] Uso pretendido declarado: open source.
- [x] Responsável humano pela seleção inicial identificado: mantenedor do projeto.
- [x] Acesso à cópia oficial da Issue 9 confirmado pelo site oficial; nenhum
  conteúdo normativo foi importado.
- [x] Estratégia BYO para vocabulário aceita.
- [x] Diretório definitivo escolhido: este diretório.
- [x] Remoto escolhido: `https://github.com/jorgelpbarretob/linter-ASD-STE100`.
- [x] Visibilidade temporária decidida: o remoto permanece privado durante o
  desenvolvimento, com revisão antes da abertura pública.
- [x] Cinco regras candidatas registradas com locators verificados e aprovadas
  para criação de fixtures.
- [x] Corpus inicial definido: exemplos sintéticos em inglês, escritos para o
  projeto e revisados por humano antes de se tornarem ground truth.
- [x] Corpus seed criado: 65 casos, com 5 violações, 5 não violações e 3 edge
  cases por candidata.
- [x] Labels dos 65 casos revisadas e aprovadas pelo mantenedor em 2026-08-12,
  com provenance registrada em cada fixture.
- [x] ADRs 001–006 aprovados pelo mantenedor em 2026-08-12.
- [x] Licença Apache-2.0 aprovada e adicionada ao projeto.
- [x] Aprovação explícita para iniciar a Fase 1 registrada em 2026-08-12.

## Decisões registradas

- Uso inicial: open source.
- Local do repositório: diretório atual; `git init` ainda não executado.
- Remoto: `jorgelpbarretob/linter-ASD-STE100`, vazio, branch padrão `main` e
  visibilidade privada na inspeção de 2026-08-12.
- Vocabulário: BYO, externo ao Git e às releases.

## Decisões ainda necessárias

### Revisor normativo

É a pessoa que consulta uma cópia legítima da Issue 9 e confirma, para cada
regra, se o locator e a interpretação estão corretos. Pode ser o próprio
mantenedor se ele tiver a cópia oficial e assumir essa revisão; código ou LLM
não substituem esse papel.

O mantenedor autorizou a consulta da cópia oficial e aprovou a lista em
`docs/rule-candidates.md` em 2026-08-12. Isso identifica o mantenedor como
revisor humano da seleção inicial; as labels individuais do corpus ainda exigem
revisão antes de se tornarem ground truth.

### Corpus inicial

É a coleção de frases e documentos em inglês usada para testar falsos positivos,
falsos negativos e precisão. Como o projeto será open source, o conteúdo também
precisa poder ser publicado. A estratégia aprovada é usar somente exemplos
sintéticos escritos para o projeto, sem copiar exemplos da norma ou manuais
confidenciais. Fixtures novas nascem `pending-human-review`.

## Critério de saída

F0 termina somente quando as pendências acima estiverem resolvidas. A ausência
de uma pendência não pode ser inferida de silêncio, acesso público ao PDF ou
resposta de LLM.
