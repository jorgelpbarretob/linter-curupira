# PT4 — revisão Grok da abertura documental

Status: Accepted with conditions
Date: 2026-08-16

## Escopo autorizado

O mantenedor autorizou explicitamente o envio do bundle documental v1 e, após
dois esclarecimentos menores, autorizou separadamente o bundle v2. O pacote
continha somente `AGENTS.md`, `PLANS.md`, governança e replanejamento pt-BR, o
protocolo PT4, ADRs 002/014/017/019 e o índice de ADRs. Labels, exemplos FP/FN,
ground truth, segredos, código e dados privados do holdout foram excluídos.

O conteúdo foi reproduzido integralmente no prompt final. O revisor não recebeu
ferramentas, web, terminal, edição, memória ou subagentes.

## Execuções descartadas

A primeira tentativa falhou no egress HTTPS do sandbox e não produziu parecer.
A repetição com `max-turns=1` terminou antes da resposta. Uma tentativa seguinte
preencheu o schema com texto que apenas anunciava o início da revisão, sem
evidência dos arquivos; ela foi classificada como inconclusiva e preservada na
custódia externa, não como `rework`.

O primeiro parecer substantivo avaliou o bundle v1, SHA-256 canônico
`db6e4a2db0693c88e4def0fa6a031c850372182a3ff9fd5c5827ec2add1ebdcd`,
e retornou `approve_with_conditions` com dois achados `minor`: congelar a
projeção CoNLL-U/MWT e esclarecer que `spacy.Token.idx` é apenas pista de
adapter. Ambos foram incorporados sem alterar contrato, thresholds, pesos,
unidades, licença ou segurança. Para evitar aprovação vinculada a bytes antigos,
foi criado e autorizado o bundle v2.

## Execução final aceita

- bundle v2 SHA-256 canônico:
  `bc1b97644fa7f0d779dfcceddd99786dee90f3a87a9d3c7435dcb5bab8872186`;
- modelo solicitado: `grok-4.6`;
- modelo retornado: `grok-4.6-build`;
- request ID: `f5849c82-ee90-4df2-b15c-948598fc4d4d`;
- session ID: `01a0089c-8f42-7403-838c-4d6387a0859f`;
- template do prompt SHA-256:
  `f5591e6b3e17bb78bcf9aa182abecb90a3a7045c5857f1c9252af12b5d17c4b1`;
- prompt expandido SHA-256:
  `a6339ef2d730af778a5e86851fdf6b5f772d9c3d31928e6dee7ebdc14b3fbf47`;
- schema SHA-256:
  `8f656bd3df1aaa551f67717e5123309e906dd1253d2a7bcad3e4e6d95b41eb4f`;
- resposta SHA-256:
  `4b594dcb5405297cc597cfda4d3f7867ee054667d08d149970972f6e74299bc6`;
- tokens: 60.126 de entrada, 128 de cache, 15.629 de saída e 14.690 de
  raciocínio; total reportado de 75.883;
- custo reportado: US$ 0,0363953;
- latência de parede: aproximadamente 259 segundos;
- schema e lógica do gate: válidos.

A custódia canônica dos manifestos, prompts, schemas e respostas permanece fora
do repositório em `/home/jorge/.hermes/pt4-opening-review/20260816-v1` e
`/home/jorge/.hermes/pt4-opening-review/20260816-v2`.

## Parecer

O veredito final foi `approve_with_conditions`, o gate foi
`open_pt4_documentation` e os dois achados foram `minor`. Não houve achado
`major` ou `blocker`. O revisor confirmou as cinco fronteiras:

- nenhum backend foi escolhido;
- nenhum modelo ou dependência foi adquirido;
- o holdout `HERMES-PT-PONT-001` permanece fechado;
- a licença do candidato Stanza requer autoridade humana;
- PT5 não foi aberto.

O parecer aceita ADR-019 e `hermes-pt4-bakeoff/v1` como contrato e
pré-registro. Ele não autoriza Gate 0, aquisição, instalação, inferência, TDD da
porta ou implementação de regra.

## Condições vinculantes antes da primeira inferência

1. O manifesto do harness deve definir o envelope ouro da sentença como o menor
   intervalo Unicode entre a primeira e a última `SurfaceToken`, incluindo uma
   fixture hash-congelada.
2. Token, sentença, lemma, UPOS, FEATS, UAS e LAS são calculados somente nos
   casos com análise ouro alinhável. Abstenção contratual entra exclusivamente
   em `abstention/unsupported`; não altera pisos, unidade, corpus nem permite
   omitir casos difíceis.
3. Gate 0, licenças, manifestos dos candidatos, corpus autoral e ambiente de
   referência continuam obrigatórios antes de download ou execução.

Qualquer mudança dessas condições, dos floors, pesos, unidades, postura de
licença ou segurança exige novo gate; o Grok não pode resolver licença
condicional nem abrir PT5.
