# ADR-018: protocolo de corpus, labels e avaliação do Hermes

Status: Accepted
Date: 2026-08-13

## Contexto

`HERMES-PT-PONT-001` é a primeira regra candidata. O detector ainda não existe
no produto Hermes, mas o repositório contém um detector inglês de ponto e
vírgula. Consultar sua saída antes de rotular criaria circularidade e poderia
transferir pressupostos da linha encerrada.

O corpus precisa separar verdade autoral, estado de revisão, partição e futura
saída do produto. Um lote sintético é útil para validar schema e guia, mas não é
evidência suficiente de utilidade ou generalização.

## Decisão

### Eixos separados

Cada caso registra:

- `truth`: `violation`, `non_violation`, `out_of_scope` ou `ambiguous`;
- `review_status`: `pending-human-review`, `approved` ou `rejected`;
- `expected_diagnostics`: inteiro somente quando a verdade permite expectativa
  categórica; `null` para `ambiguous`;
- `partition`: `development`, `challenge` ou `holdout`;
- proveniência e licença do texto.

Saída, versão, configuração ou diagnóstico do linter são proibidos no arquivo
de labels. Resultados ficam em artefato separado, ligado por `case_id` e hashes.

### Partições

- `development`: exemplos públicos usados para especificar e depurar;
- `challenge`: falhas consumidas e casos adversariais conhecidos;
- `holdout`: fonte e labels congeladas antes da primeira execução, sem uso em
  prompt, regra, fixture ou escolha de threshold.

Caso consumido nunca retorna ao holdout. Duplicatas e paráfrases próximas não
podem atravessar partições.

### Fluxo

```text
proposta -> validação estrutural -> revisão humana integral -> adjudicação
         -> bytes canônicos -> SHA-256 -> autorização -> execução isolada
```

O lote-piloto começa `pending-human-review`. A aprovação humana define os bytes
canônicos; depois disso qualquer mudança cria novo arquivo/versão e novo hash.

### Unidade e métricas de PONT-001

- unidade positiva: cada caractere literal `;` em prosa lintável;
- unidade fora do escopo: cada `;` em região excluída ou markup;
- controle negativo: documento sem `;` em prosa lintável;
- diagnóstico correto: exatamente o intervalo Unicode `[offset, offset + 1)`;
- métricas: TP/FP/FN, precisão, recall, Wilson 95%, FP por 1.000 palavras
  lintáveis, erro de região e erro de offset.

O piloto não promove regra. Para satisfazer limite inferior Wilson de 0,95 com
zero erro, a evidência de promoção precisa de pelo menos 73 unidades positivas
corretas; qualquer erro aumenta a amostra necessária. Challenge e holdout serão
dimensionados depois do piloto, antes de sua geração.

### Autoridade humana

Autor do lote pode propor `truth`, mas não aprová-la sozinho. Uma segunda
revisão humana examina texto, marcação, unidade e racional sem consultar o
detector. Modelo de linguagem pode ser comparador futuro, nunca aprovador único.

## Consequências

- O primeiro lote permanece proposta até decisão explícita do mantenedor.
- Métricas sintéticas serão publicadas como piloto, não como prova de produto.
- Holdout exige fonte/autoria independente ainda não definida.
- O linter inglês não será executado no corpus Hermes.
- TDD e migração continuam bloqueados até PT3.

## Aprovação e congelamento

ADR, guia e 40/40 labels aceitos explicitamente pelo mantenedor em 2026-08-13.
O arquivo canônico é `corpus/hermes/pont-001-development-v1.jsonl`, SHA-256
`51f52007848deaae5169171354d900488df9faedbf073a17a48b14d714703bfc`.

A aprovação autoriza o congelamento do piloto. Não autoriza execução do linter,
implementação, promoção ou uso como holdout.

## Primeiro holdout congelado

Em 2026-08-14, o mantenedor aceitou o snapshot pt-BR do Kubernetes, o manifesto
sem labels e a revisão delegada ao Grok registrada em
`docs/hermes-pt2-grok-review-protocol.md`. O modelo solicitado `grok-4.6`
respondeu como `grok-4.6-build`; todas as 409 unidades passaram bijeção e
validação estrutural, sem fila crítica declarada.

O mantenedor aprovou explicitamente os bytes candidatos e o SHA-256
`6cab9e0a4090df19fc5c3cc5a8e93122413160f523e032367ec25849567abab6`.
O ground truth com 409 registros foi congelado sob custódia externa, sem texto
do Kubernetes no arquivo e sem labels no Git. Esta aprovação fecha o lado de
corpus de PT2. Ela não autoriza implementar o detector, consultar labels durante
TDD nem executar o holdout.
