# PT4 — revisão Grok do Gate 0 v1

Status: Accepted with conditions
Date: 2026-08-16

## Escopo autorizado

O mantenedor autorizou explicitamente o envio do bundle Gate 0 ao Grok. O
pacote continha 18 arquivos textuais: governança e planos necessários, ADR-019,
relatório de elegibilidade, manifests dos candidatos, lock, hashes, metadados
dos wheels, auditoria de licenças e prova offline. Wheels, ambientes virtuais,
código, segredos, labels e erros do holdout foram excluídos.

O conteúdo foi reproduzido integralmente no prompt. O revisor não recebeu
ferramentas, web, terminal, edição, memória ou subagentes.

## Execução aceita

- bundle SHA-256 canônico:
  `9feaf0d1c0e105b68727b52c3477ebf90f1dbba1b77e8bdc3b3275c8995c23f4`;
- lista pública de artefatos SHA-256:
  `5d502fed37d44366aa4e2670059b49b70530771e9578f4ee1c7af65cecda6228`;
- modelo solicitado: `grok-4.6`;
- modelo retornado: `grok-4.6-build`;
- request ID: `9e16438f-8d58-4c6e-b809-eea5566975f7`;
- session ID: `01a008cb-f124-7583-bd5f-030be0607896`;
- template do prompt SHA-256:
  `1ea83c266ed6c19dc0a4355996a190083300c2d9c86c2af256d4775a93d89ff0`;
- prompt expandido SHA-256:
  `7f58f3bc5150430d435e254a2bb34da04e81dc6c0a8c3f06baabf87735573af0`;
- schema SHA-256:
  `86b7f0845a8d780c35eb64cda2ea41827a953d1f06edf07e3a05226625f43e54`;
- resposta SHA-256:
  `db57f65cff2e5649c1703aae47c9ab8e7344c72835f928b9c72e10f0d39ec257`;
- tokens: 99.986 de entrada, 128 de cache, 14.773 de saída e 13.727 de
  raciocínio; total reportado de 114.887;
- custo reportado: US$ 0,04907458;
- latência de parede: aproximadamente 211 segundos;
- schema e lógica do gate: válidos.

A custódia de input, prompt, schema e resposta permanece fora do repositório em
`/home/jorge/.hermes/pt4-gate0-review/20260816-v1`.

## Parecer

O veredito foi `approve_with_conditions` e o gate foi `accept_gate0`. O Grok
aceitou `spacy-pt_core_news_sm` como `eligible` para o bake-off e manteve
`stanza-pt-default_fast` como `ineligible-license`. Houve dois achados `minor` e
nenhum `major` ou `blocker`.

O parecer confirmou as seis fronteiras:

- nenhum backend foi escolhido;
- nenhuma dependência entrou no projeto;
- nenhuma inferência de bake-off foi executada;
- o holdout `HERMES-PT-PONT-001` permanece fechado;
- PT5 não foi aberto;
- Stanza não foi adquirido.

## Condições vinculantes

1. Qualquer redistribuição futura preserva notices e licenças dos 45 wheels,
   atribui modelo e fontes de treino, mantém CC BY-SA 4.0, indica modificações e
   revisa share-alike antes de distribuir modelo adaptado.
2. O bake-off usa somente o wheelhouse congelado com `--no-index`,
   `--find-links` e `--require-hashes`, rede negada e NER excluído.
3. O próximo incremento de evidência deve congelar a saída de `pip check` em
   artefato próprio ou log de instalação hash-congelado.
4. O futuro harness deve falhar diante de qualquer tentativa de socket/DNS,
   inclusive por dependências capazes de I/O remoto.
5. spaCy e o modelo não entram em `pyproject.toml`, wheel base, domínio ou
   adapter antes dos gates posteriores; elegibilidade não seleciona backend.
6. Stanza só retorna após resolução humana explícita da licença e novo Gate 0.
7. Envelope ouro de sentença e denominadores de métricas continuam sujeitos às
   condições pré-inferência do gate documental.
8. PONT-001, corpus/harness ainda não autorizados, inferência, PT5 e os erros do
   holdout permanecem fechados.

O próximo WIP pode criar, revisar e congelar os corpora pré-registrados e o
ambiente de referência. Não pode implementar adapter nem executar inferência do
bake-off.
