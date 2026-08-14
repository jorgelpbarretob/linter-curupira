# PT2 — avaliação de fonte independente para o holdout de PONT-001

Status: Proposed
Date: 2026-08-13

## Decisão proposta

Usar a localização oficial em português brasileiro da documentação do
Kubernetes como primeira fonte externa do holdout de `HERMES-PT-PONT-001`. O
repositório mantém a documentação em Markdown, identifica a localização
portuguesa e publica o conteúdo sob CC BY 4.0.[11][12]

Esta decisão ainda não autoriza gerar labels, executar o linter nem incorporar
texto do Kubernetes ao repositório Hermes. Ela fixa a fonte candidata, o
snapshot observado e um desenho de seleção que precisa de aprovação humana.

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
sha256("0dcdb1dda898de2bd4431a898f86c170e109063f\0" + caminho_relativo)
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

## Gates restantes

1. aprovação humana desta avaliação e das exclusões;
2. geração auditável do manifesto, sem labels e sem conteúdo copiado;
3. revisão humana integral das 336 ocorrências e dos 73 controles;
4. adjudicação, bytes canônicos e SHA-256 do ground truth;
5. congelamento do detector implementado em TDD;
6. autorização explícita para a primeira execução isolada;
7. abertura dos labels e cálculo das métricas do ADR-018.

Enquanto esses gates não forem concluídos, PT2 permanece em andamento e PT3
continua bloqueado.

## Sources

[11] https://github.com/kubernetes/website — Kubernetes website repository
[12] https://kubernetes.io/pt-br/docs/contribute/localization_pt-br — Kubernetes pt-BR localization guide
[13] https://devguide.python.org/documentation/translations/translating — Python documentation translations
[14] https://devguide.python.org/documentation/translations/coordinating — Python translation coordination
[15] https://docs.github.com/pt/enterprise-server@3.21/contributing/style-guide-and-content-model/style-guide — GitHub Docs pt-BR style guide
[16] https://github.com/github/docs — GitHub Docs repository and licenses
