# Evidência de produto — Rodada 2 `count-only`

Data: 2026-08-13

Status: redução revisada e segundo `count-only` concluído; todas as tranches
dentro dos limites; nenhum label, JSONL ou resultado do linter foi produzido

## Gate e comando

A segunda revisão independente do Cursor autorizou somente implementar o
scanner e executar `count-only`. O scanner fica fora de `src/ste_lint`, usa
apenas a biblioteca padrão e aborta antes da contagem se qualquer snapshot,
tree, licença, arquivo, selection key, manifesto ou total de palavras divergir.

Comando executado duas vezes, com comparação byte a byte de stdout e stderr:

```text
.venv/bin/python tools/product_evidence/round2_scanner.py --count-only \
  --dapr-root /tmp/ste-round2-dapr-docs \
  --otel-root /tmp/ste-round2-opentelemetry-docs
```

As duas execuções terminaram com código zero e saída idêntica.

## Auditoria obrigatória

- source IDs: `dapr` e `otel`;
- commits: ambos coincidiram com o plano;
- quatro tree hashes: todos coincidiram;
- dois hashes de licença: ambos coincidiram;
- 16 selection keys e 16 hashes de arquivo: todos coincidiram;
- palavras brutas por whitespace: 21.972;
- SHA-256 do manifesto canônico:
  `4f09744c7eb7e1f460e68f4185b478037a4ee4500fb329bd5a62dc74cddd73a3`.

Nenhum conteúdo-fonte foi gravado no repositório ou incluído na saída.

## Resultado por documento

`S` soma candidatos completos e incompletos; `P` conta parágrafos descritivos;
`;` conta todo caractere literal; `L` conta runs de lista com dois ou mais peers.

| Fonte | Tipo | Path | S | P | `;` | L |
|---|---|---|---:|---:|---:|---:|
| `dapr` | procedural | `daprdocs/content/en/getting-started/quickstarts/configuration-quickstart.md` | 134 | 0 | 20 | 14 |
| `dapr` | procedural | `daprdocs/content/en/getting-started/quickstarts/jobs-quickstart.md` | 72 | 0 | 7 | 8 |
| `dapr` | procedural | `daprdocs/content/en/getting-started/quickstarts/cryptography-quickstart.md` | 62 | 0 | 19 | 6 |
| `dapr` | procedural | `daprdocs/content/en/getting-started/quickstarts/secrets-quickstart.md` | 127 | 0 | 13 | 18 |
| `dapr` | descriptive | `daprdocs/content/en/concepts/dapr-services/sidecar.md` | 31 | 14 | 0 | 1 |
| `dapr` | descriptive | `daprdocs/content/en/concepts/dapr-services/placement.md` | 26 | 13 | 0 | 0 |
| `dapr` | descriptive | `daprdocs/content/en/concepts/terminology.md` | 1 | 1 | 0 | 0 |
| `dapr` | descriptive | `daprdocs/content/en/concepts/dapr-services/sidecar-injector.md` | 17 | 10 | 0 | 0 |
| `otel` | procedural | `content/en/docs/zero-code/obi/configure/service-discovery.md` | 130 | 0 | 0 | 11 |
| `otel` | procedural | `content/en/docs/zero-code/obi/configure/routes-decorator.md` | 54 | 0 | 0 | 2 |
| `otel` | procedural | `content/en/docs/zero-code/dotnet/instrumentations.md` | 39 | 0 | 2 | 0 |
| `otel` | procedural | `content/en/docs/zero-code/obi/network/config.md` | 67 | 0 | 0 | 1 |
| `otel` | descriptive | `content/en/docs/concepts/signals/logs.md` | 74 | 35 | 8 | 2 |
| `otel` | descriptive | `content/en/docs/concepts/signals/traces.md` | 115 | 51 | 0 | 6 |
| `otel` | descriptive | `content/en/docs/concepts/distributions.md` | 43 | 13 | 0 | 4 |
| `otel` | descriptive | `content/en/docs/concepts/instrumentation/code-based.md` | 22 | 7 | 0 | 0 |

## Limites pré-label

| Tranche | Unidades | Limite | Resultado |
|---|---:|---:|---|
| `STE-I9-SENT-001` | 685 | 650 | **excedeu** |
| `STE-I9-SENT-002` | 329 | 650 | dentro |
| `STE-I9-PARA-001` | 144 | 300 | dentro |
| `STE-I9-PUNCT-001` | 69 | 200 | dentro |
| `STE-I9-LIST-001` | 73 | 200 | dentro |

Como `STE-I9-SENT-001` excedeu o limite, a execução parou no gate
pré-label. Não existe inventário rotulável nem ground truth desta rodada.

## Redução determinística proposta

Para a tranche `STE-I9-SENT-001`, ordenar os oito documentos procedurais pela
selection key em ordem decrescente e retirar um por vez, pulando qualquer
retirada que deixaria menos de dois documentos de uma fonte. Parar na primeira
contagem dentro do limite. Esse procedimento depende somente do manifesto
congelado e do volume mecânico, não de labels ou resultado do linter.

A primeira retirada é
`daprdocs/content/en/getting-started/quickstarts/secrets-quickstart.md`, cuja
selection key é a maior da tranche. A amostra proposta preserva três documentos
`dapr`, quatro `otel` e cai de 685 para 558 unidades. O arquivo retirado de
`STE-I9-SENT-001` permanece nas tranches exaustivas de pontuação e lista.

Essa redução exigiu nova revisão Cursor antes de alterar o scanner; o gate foi
obtido antes da segunda execução. Inventário e labels permaneceram bloqueados.

## Segundo `count-only` após revisão

O Cursor aprovou a exclusão específica no terceiro gate. O scanner passou a
aplicá-la somente à agregação de `STE-I9-SENT-001`, preservando a auditoria dos
16 arquivos e as contagens de pontuação e lista. Duas novas execuções produziram
saída byte a byte idêntica:

| Tranche | Unidades finais | Limite | Resultado |
|---|---:|---:|---|
| `STE-I9-SENT-001` | 558 | 650 | dentro |
| `STE-I9-SENT-002` | 329 | 650 | dentro |
| `STE-I9-PARA-001` | 144 | 300 | dentro |
| `STE-I9-PUNCT-001` | 69 | 200 | dentro |
| `STE-I9-LIST-001` | 73 | 200 | dentro |

O manifesto permaneceu com 16 arquivos, 21.972 palavras e SHA-256
`4f09744c7eb7e1f460e68f4185b478037a4ee4500fb329bd5a62dc74cddd73a3`.
O próximo gate pode autorizar o inventário unitário com
`truth=pending-review`; labels e execução do linter permanecem bloqueados.
