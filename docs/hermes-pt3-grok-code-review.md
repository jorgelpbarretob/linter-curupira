# PT3 — revisão Grok e congelamento de HERMES-PT-PONT-001

Status: Accepted
Date: 2026-08-14

## Escopo autorizado

O mantenedor autorizou explicitamente `APROVADO ENVIO GROK PT3`. A revisão foi
executada sobre um diretório temporário isolado contendo somente:

- `src/hermes_lint/**`;
- `tests/hermes/**`;
- `pyproject.toml` e `uv.lock`;
- `corpus/hermes/pont-001-development-v1.jsonl`;
- `tools/hermes/freeze_pont_001_detector.py`.

O bundle tinha SHA-256 canônico
`6b5a321a6c3fa4a4dcffb76816838ec39bc60415b36872ca2af4de7d9fae5aac`.
Manifesto e labels do holdout, ground truth e todo `/home/jorge/.hermes` foram
excluídos. O revisor recebeu somente ferramentas de leitura local, sem busca
web, MCP, subagentes ou edição.

## Execução aceita

- modelo solicitado: `grok-4.6`;
- modelo retornado: `grok-4.6-build`;
- response/request ID:
  `f412055e-4140-4cf6-9d62-31b9151cfe9c`;
- session ID: `01a0017d-240e-7970-a0dc-2789ed0c007f`;
- prompt corretivo SHA-256:
  `d27684d65e4be7676d4333c21b3358225a851b996d56e1acf00b1b32568d936f`;
- schema SHA-256:
  `36c70cc37feb6e1c378a74bab46dc2d5baa1e6dc70bc6aea49018e38cf7f8bf1`;
- tokens: 68.924 de entrada, 116.352 de cache, 12.089 de saída e 11.385 de
  raciocínio; total reportado de 197.365;
- custo reportado: US$ 0,04565486;
- latência de parede da continuação aceita: aproximadamente 164 segundos;
- schema estruturado: válido.

A primeira geração foi interrompida antes de um parecer porque enumerou paths
inexistentes. Ela não foi aceita como evidência. A continuação recebeu um
contrato mais estrito: reler cada path real, omitir hipóteses não demonstráveis
e retornar no máximo seis achados. Somente o campo `structuredOutput` validado
da continuação é o parecer arquivado; texto intermediário não é decisão.

## Parecer

O veredito estruturado foi `approve`, com zero achados `blocker`, `major` ou
`minor`. O revisor confirmou a regra como `preview/info`, sem autofix, o
isolamento de `ste_lint`, a preservação de CRLF/Unicode e a composição do
manifesto de congelamento.

O parecer listou quatro riscos residuais: os quatro casos ambíguos não são
assertados; o pareamento de matemática não consultava a máscara de regiões já
ignoradas; TXT trata todo o conteúdo como prosa; e o manifesto congelado ainda
não existia. O primeiro e o terceiro são contratos deliberados do corpus e do
adapter TXT. O quarto foi resolvido pela materialização descrita abaixo.

O segundo risco era reproduzível: um `$` dentro de inline code podia ocultar o
ponto e vírgula de prosa e deixar o ponto e vírgula matemático lintável. A
correção seguiu TDD em `tests/hermes/test_pont_001.py`, sem consultar o holdout
e sem mudar interface pública.

## Congelamento

Após a correção e as validações offline, o detector foi congelado em:

- manifesto: `corpus/hermes/pont-001-detector-freeze-v1.json`;
- SHA-256 do manifesto:
  `29bfebaeab126a33d7d0f4aaae44f83d53dd22f03496e30758693d0d9212bae8`;
- SHA-256 canônico do detector:
  `972a1c67e14d4316afc388df523838f4338a60d5866ab13710d19bda1fc016b9`;
- corpus de desenvolvimento:
  `51f52007848deaae5169171354d900488df9faedbf073a17a48b14d714703bfc`.

No momento deste congelamento, o holdout ainda não tinha sido aberto nem
executado e dependia de autorização separada. Essa autorização foi concedida
posteriormente em 2026-08-14; a execução e a decisão `preview` estão registradas
em `docs/hermes-pont-001-holdout-evaluation-v1.md`.
