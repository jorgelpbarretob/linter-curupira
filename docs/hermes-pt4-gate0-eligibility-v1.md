# PT4 — Gate 0 de elegibilidade dos candidatos v1

Status: Accepted with conditions
Date: 2026-08-16
Protocol: `hermes-pt4-bakeoff/v1`

## Escopo

Este incremento executa somente o Gate 0 autorizado: licença, proveniência,
integridade, resolução completa de wheels, instalação offline e carga sem
texto. Não cria corpus, harness, adapter ou regra; não calcula métrica
linguística; não escolhe backend; não abre PT5. O holdout consumido de
`HERMES-PT-PONT-001` e seus erros permaneceram fechados.

Ambiente de referência desta revisão: CPython 3.12.13, Linux x86_64, glibc
2.41. O lock exige wheels compatíveis com glibc 2.28 ou superior e foi
resolvido por `pip==25.0.1` somente com binários.

## Candidato spaCy

O PyPI publica `spacy==3.8.15` sob MIT, com suporte a Python 3.12 e wheel Linux
x86_64 para CPython 3.12.[1] O manifesto oficial de compatibilidade associa a
linha spaCy 3.8 ao modelo `pt_core_news_sm==3.8.0`.[3]

O release oficial do modelo declara compatibilidade `>=3.8.0,<3.9.0`, licença
CC BY-SA 4.0, treinamento em UD Portuguese Bosque v2.8 e WikiNER e os
componentes necessários para morfologia, lema, dependência e sentenças.[2] O
SHA-256 oficial e recomputado do wheel é
`c304fa04db3af73cd08a250feacf560506e15a2ec2469bd1b09f06847f6b455c`.[2]

### Wheelhouse congelado

- 45 wheels, todos binários;
- 87.308.970 bytes;
- cada arquivo possui nome, versão, URL oficial exata, tamanho e SHA-256 em
  `artifacts/hermes/pt4-gate0/spacy-wheelhouse-v1.json`;
- manifesto SHA-256:
  `d6dc6d3afec7c1890fdde50124e4dfdbf365adb61fc7be1a2aa73d857b311af5`;
- lista `sha256sum` SHA-256:
  `399b0c1cd88024991d8cdf87116e5bad02bad1571a7ef211e3bdbf2366c7d728`;
- lock `--require-hashes` SHA-256:
  `c3f80b40ba45575c6f4fcf2931e1110c886f7745fa52634f864d49359f558a82`.

O wheel principal `spacy==3.8.15` tem 32.695.414 bytes e SHA-256
`fa9df68fc8887c0a6440b84d1d307980e594d99b45f19a37d733e58caa9a6682`.
O wheel do modelo tem 12.985.007 bytes e seu hash coincide com o release
oficial.

### Licenças e redistribuição

Todos os 45 wheels contêm declaração de licença e arquivo de licença ou
NOTICE. A auditoria congelada tem SHA-256
`8e57cfd7f9695c10246271e3b7978490c0fdb3b0cce72c2979d0a6f52f8ebf96`.
Ela não substitui aconselhamento jurídico e exige, em qualquer redistribuição:

- preservar licenças e notices de todos os wheels;
- atribuir `pt_core_news_sm` e as fontes de treino declaradas;
- preservar CC BY-SA 4.0, indicar modificações e revisar share-alike antes de
  distribuir modelo adaptado;
- preservar os notices e obrigações aplicáveis a arquivos MPL-2.0 modificados.

O candidato é `eligible-with-redistribution-obligations`; não houve
relicenciamento de modelo ou dados.

### Instalação e carga offline

A instalação foi repetida em virtualenv vazio com `--no-index`,
`--find-links`, `--require-hashes`, proxies apontados para loopback inválido e
checagem de dependências. `pip check` retornou `No broken requirements found`.

A carga usou guard explícito sobre resolução DNS e conexões de socket, excluiu
NER e não processou texto. Resultado:

- spaCy 3.8.15 e modelo 3.8.0;
- componentes `tok2vec`, `morphologizer`, `parser`, `lemmatizer` e
  `attribute_ruler`;
- zero tentativa de rede;
- carga em 0,651893 s;
- pico de RSS 143.104 KiB;
- prova SHA-256:
  `db35e8ba00cfd3d174d9d15f8a28a8c33bd6e7738f82f367820652cf840e1cab`.

Nada foi adicionado ao `pyproject.toml`, nenhum tipo spaCy entrou em
`hermes_lint.domain` e nenhum adapter foi implementado. O parecer operacional
delegado aceitou o candidato como `eligible` para o bake-off, sem selecioná-lo
como backend.

## Candidato Stanza

O PyPI publica `stanza==1.14.0` sob Apache-2.0 e com suporte a Python 3.12.[4]
O manifesto 1.14.0 oferece `default_fast` em português com Bosque para
tokenização/MWT e variantes `nocharlm` para lema, POS e dependências.[6]

Isso não resolve a licença dos pesos. A documentação oficial afirma que a
licença dos modelos treinados com UD é incerta e oferece ODC-By somente na
medida em que Stanford possua os direitos relevantes.[5] Como a governança
reserva dúvida de licença à autoridade humana e nenhuma resolução específica
foi fornecida, o candidato fica `ineligible-license`.

Stanza, language packs e dependências não foram baixados, instalados ou
carregados. O manifesto separado está em
`artifacts/hermes/pt4-gate0/stanza-candidate-v1.json`. Ele só pode retornar após
resolução humana explícita e novo Gate 0.

## Decisão aceita

Gate 0 v1 produz um único candidato elegível: spaCy + `pt_core_news_sm`. Isso
não o torna vencedor nem backend aceito. O protocolo permite prosseguir por uma
trilha de candidato único somente se todos os gates linguísticos, operacionais
e quantitativos futuros passarem sem relaxar floors, corpus, pesos ou
segurança.

O Grok confirmou os manifests, o lock, a licença, a prova offline e as
fronteiras de escopo com `approve_with_conditions` e `accept_gate0`. O parecer,
hashes e condições estão em `docs/hermes-pt4-gate0-grok-review-v1.md`.

O próximo WIP pode criar, revisar e congelar os corpora pré-registrados e o
ambiente de referência. Continuam fora de escopo: adicionar dependência ao
produto, implementar adapter, executar inferência de bake-off ou abrir PT5.

## Sources

[1] https://pypi.org/project/spacy — spaCy PyPI
[2] https://github.com/explosion/spacy-models/releases/tag/pt_core_news_sm-3.8.0 — pt_core_news_sm 3.8.0 release
[3] https://raw.githubusercontent.com/explosion/spacy-models/master/compatibility.json — spaCy model compatibility manifest
[4] https://pypi.org/project/stanza — Stanza PyPI
[5] https://stanfordnlp.github.io/stanza/performance.html — Stanza model performance and licensing
[6] https://raw.githubusercontent.com/stanfordnlp/stanza-resources/main/resources_1.14.0.json — Stanza resources 1.14.0 manifest
