# PT2 — avaliação de fonte independente para o holdout de PONT-001

Status: Accepted
Date: 2026-08-14

## Decisão

Usar a localização oficial em português brasileiro da documentação do
Kubernetes como primeira fonte externa do holdout de `HERMES-PT-PONT-001`. O
repositório mantém a documentação em Markdown, identifica a localização
portuguesa e publica o conteúdo sob CC BY 4.0.[11][12]

Esta decisão não autoriza gerar labels, executar o linter nem incorporar texto
do Kubernetes ao repositório Hermes. Ela fixa a fonte, o snapshot observado e o
desenho de seleção aceito pelo mantenedor em 2026-08-14.

## Requisitos de seleção

A primeira fonte externa precisa:

- conter prosa técnica identificada como pt-BR;
- estar em formato aceito sem conversão pelo parser atual (`.md` ou `.txt`);
- permitir snapshot por commit e verificação por SHA-256;
- possuir licença redistribuível e atribuição rastreável;
- ser independente do lote sintético de desenvolvimento;
- oferecer ocorrências suficientes para que o tamanho seja decidido antes dos
  labels e da primeira execução.

## Fontes avaliadas

| Fonte | Resultado | Fundamentação |
|---|---|---|
| Kubernetes `website/content/pt-br` | **recomendada** | fonte oficial, Markdown versionado, localização pt-BR explícita e CC BY 4.0.[11][12] |
| documentação Python pt-BR | **reserva para tranche futura** | projeto oficial e ativo, mas o fluxo de tradução usa primariamente arquivos PO; consumi-lo agora exigiria transformação e um novo contrato de parser.[13][14] |
| GitHub Docs pt-BR | **comparador, não holdout inicial** | o conteúdo do projeto é CC BY 4.0; na inspeção realizada, o repositório público versiona a fonte Markdown em inglês e não oferece o mesmo snapshot bruto da localização exibida no site.[15][16] |

Python e GitHub Docs continuam úteis para uma futura avaliação entre famílias
de fonte. Não devem ser convertidos silenciosamente para texto: qualquer
extração de PO ou HTML precisa de especificação, testes de offsets e um
pré-registro próprio.

## Snapshot `count-only`

Inventário feito sem abrir diagnósticos e sem executar detector:

- repositório: `https://github.com/kubernetes/website`;
- commit: `0dcdb1dda898de2bd4431a898f86c170e109063f`;
- data do commit: `2026-08-13T14:45:38Z`;
- SHA-256 do arquivo `LICENSE`:
  `9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411`;
- arquivos Markdown em `content/pt-br`: 368;
- exclusões propostas: `docs/sitemap.md` e
  `docs/reference/setup-tools/kubeadm/generated/**`;
- arquivos elegíveis depois das exclusões: 326;
- arquivos elegíveis com ao menos um `;` literal: 90;
- ocorrências literais de `;` nos arquivos elegíveis: 336.

As 336 ocorrências são somente um teto de candidatos. A contagem inclui
frontmatter, markup, código e outras regiões que podem estar fora do escopo; ela
não informa quantas violações existem. Nenhum conteúdo ou caminho foi escolhido
com base na saída do linter.

## Pré-registro proposto

### Universo positivo e de escopo

O inventário incluirá todas as 336 ocorrências literais nos 90 arquivos
elegíveis. Uma revisão humana cega ao detector classificará cada ocorrência de
acordo com o guia aceito, incluindo região, `truth`, offset e racional.

Não haverá parada ao atingir uma quantidade favorável. Se a revisão integral
encontrar menos de 73 unidades `violation`, este snapshot não poderá satisfazer
sozinho o gate Wilson definido no ADR-018; a equipe deverá aprovar outra fonte
antes de qualquer execução.

### Controles sem ponto e vírgula

Dos arquivos elegíveis sem `;`, selecionar 73 documentos pela menor ordenação
lexical de:

```text
sha256("0dcdb1dda898de2bd4431a898f86c170e109063f\0" + caminho_relativo_ao_repositório_em_UTF-8)
```

O procedimento é determinístico, não depende do conteúdo ou do detector e deve
ser implementado por script auditável. Esses documentos medirão emissões
espúrias fora da unidade literal esperada; não substituem a anotação das 336
ocorrências candidatas.

### Separação e sigilo antes da primeira execução

- o manifesto público registra commit, licença, exclusões, caminhos e hashes;
- os labels ficam sob custódia humana separada do código até o congelamento do
  detector;
- texto externo não entra no wheel, fixtures, prompts ou testes;
- nenhum caso do holdout pode orientar implementação, threshold ou exceção;
- depois da primeira execução, resultados são ligados a `case_id` e hashes,
  nunca gravados no arquivo de ground truth.

## Resultado da materialização

Após a aprovação humana da fonte, das duas exclusões e do método de seleção,
o manifesto foi gerado de forma independente do produto:

- manifesto:
  `corpus/hermes/pont-001-kubernetes-holdout-manifest-v1.jsonl`;
- SHA-256:
  `3eaf4069017593c4f9e0d0c573736899ccbf137e3792ba97161e94d0663f86e7`;
- registros: um cabeçalho, 336 unidades `literal_semicolon` e 73 documentos
  `zero_semicolon_control`;
- metadados por unidade: `case_id`, caminho relativo ao repositório, SHA-256 do
  arquivo e coordenadas ou chave de seleção aplicável;
- campos proibidos no manifesto: texto-fonte, `truth`, labels, racional,
  diagnósticos, estado de revisão e expectativas do detector.

Comando de reprodução, executado sobre um checkout no commit aceito:

```text
.venv/bin/python tools/hermes/generate_pont_001_holdout_manifest.py \
  /caminho/para/kubernetes-website \
  corpus/hermes/pont-001-kubernetes-holdout-manifest-v1.jsonl
```

O gerador verifica commit, hash da licença e todas as contagens
pré-registradas antes de escrever o artefato. Ele não importa código do produto
nem classifica região, escopo ou violação.

## Pacote para revisão humana

O script `tools/hermes/prepare_pont_001_human_review.py` verifica o snapshot e
o manifesto congelados e prepara, fora do repositório, uma planilha CSV com
janela de contexto para as ocorrências e campos de decisão vazios. Ele recusa
gravar o pacote dentro do repositório e não importa nem executa código do
produto.

O pacote operacional v2 foi materializado sob custódia separada em
`/home/jorge/.hermes/holdout-custody/pont-001-human-review-v2`:

- 409 `case_id` únicos: 336 ocorrências e 73 controles;
- 409 estados `pending-human-review`;
- zero `truth`, expectativas ou racionais preenchidos;
- SHA-256 do CSV:
  `b3fcb6214c5fc2eff295b4b7906d558f00770f1159a079648a64ac081e30fad4`.

O v2 acrescenta os campos `domain` e `reviewer_role`, exigidos pelo guia. Ele
substitui o modelo v1 ainda vazio; nenhuma decisão humana foi descartada. O
mantenedor aceitou o pacote e autorizou a continuidade em 2026-08-14. Como o
CSV permaneceu byte a byte sem `truth`, o aceite registra o processo e não
aprova labels inexistentes.

O pacote não é ground truth. O CSV só se torna proposta rotulada depois do
preenchimento integral por revisor humano; adjudicação e congelamento continuam
gates posteriores e separados.

O script `tools/hermes/validate_pont_001_human_review.py` fica pronto para
validar bijeção, campos imutáveis, identidade e papel do revisor, data e
coerência entre `truth` e `expected_diagnostics`. Ele falha enquanto qualquer
caso permanecer `pending-human-review` e não importa nem executa o produto.

## Revisão delegada e candidato de ground truth

O mantenedor autorizou em 2026-08-14 o Grok como revisor delegado e pediu
somente aprovações críticas. A emenda, o isolamento, o contrato e os gates
estão em `docs/hermes-pt2-grok-review-protocol.md`.

A execução cega foi concluída sob custódia separada:

- modelo solicitado: `grok-4.6`;
- modelo retornado: `grok-4.6-build`;
- cobertura e bijeção: 409/409 `case_id`;
- fila crítica declarada e validada: zero;
- prompt SHA-256:
  `95c23525ea1c3416fb94148dde507df3e73cb399a558c3d899e4caba17727e91`;
- schema SHA-256:
  `419eec0a6178eaa9ed19d2b81d8fa6943cbf11f3a105bb0cbd58028b89751f73`;
- propostas SHA-256:
  `0f47850e2d8cf44d2019fa516a41d213b06d438e4e646f9236a70ab7e36ed9ce`;
- custo reportado pelo Grok CLI: US$ 0,695188.

O ground-truth candidato foi gerado sem `text`, contexto, diagnóstico ou saída
bruta de modelo e reproduzido byte a byte:

- caminho de custódia:
  `/home/jorge/.hermes/holdout-custody/pont-001-ground-truth-candidate-v1/`;
- registros: 409;
- SHA-256:
  `6cab9e0a4090df19fc5c3cc5a8e93122413160f523e032367ec25849567abab6`.

O mantenedor aprovou explicitamente esse hash em 2026-08-14. Os mesmos bytes
foram congelados sob
`/home/jorge/.hermes/holdout-custody/pont-001-ground-truth-v1/`, acompanhados de
registro separado de aprovação. Labels e respostas continuam fora do Git e não
podem orientar o detector.

## Execução e fechamento dos gates

O mantenedor autorizou a primeira execução isolada em 2026-08-14 e delegou ao
Grok as aprovações operacionais seguintes. O detector congelado foi executado
antes da abertura dos labels. Depois de verificar hashes, isolamento e
resultados sem texto-fonte, o Grok retornou `approve_open_labels`. O score e uma
recomputação independente produziram 148 TP, 4 FP, 15 FN e 242 TN, com precisão
0,973684, limite inferior Wilson 95% de 0,934296 e recall 0,907975.

O parecer pós-holdout foi `preview`: falharam o limite inferior Wilson de 0,95
e o gate de zero falso positivo conhecido. O holdout está consumido e não pode
orientar ajustes no detector neste ciclo. Relatório, hashes e regras para os 19
casos de erro estão em `docs/hermes-pont-001-holdout-evaluation-v1.md`.

## Sources

[11] https://github.com/kubernetes/website — Kubernetes website repository
[12] https://kubernetes.io/pt-br/docs/contribute/localization_pt-br — Kubernetes pt-BR localization guide
[13] https://devguide.python.org/documentation/translations/translating — Python documentation translations
[14] https://devguide.python.org/documentation/translations/coordinating — Python translation coordination
[15] https://docs.github.com/pt/enterprise-server@3.21/contributing/style-guide-and-content-model/style-guide — GitHub Docs pt-BR style guide
[16] https://github.com/github/docs — GitHub Docs repository and licenses
