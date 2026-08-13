# Plano técnico: expansão de evidência de `STE-I9-LIST-001`

Status: Recall v2 evaluated; quantitative gates passed; promotion decision pending
Data: 2026-08-13
Regra: `STE-I9-LIST-001`
Escopo: evidência para decisão de promoção; nenhum fixer ou mudança de metadata
Approved by: project maintainer, 2026-08-13
Amendment 1 approved by: project maintainer, 2026-08-13
Amendment 2 and small challenge approved by: project maintainer, 2026-08-13
Full challenge and holdout approved by: project maintainer, 2026-08-13
Recall iteration 2 authorized by: project maintainer, 2026-08-13

## Escopo deste plano

Este plano responde como obter evidência suficiente e auditável para decidir se
a subclasse estreita já implementada pode sair de `preview`. Ele não decide a
promoção, não altera o detector, não habilita `safe_autofix` e não autoriza
`FixEdit`, provider ou `ste fix`.

Tese: atingir 73 emissões corretas é condição matemática necessária, mas uma
decisão defensável também exige diversidade, labels congeladas antes da
execução e um holdout técnico que não tenha orientado o detector.

## Contrato da decisão

Unidade de observação: um documento candidato com no máximo uma associação de
lead-in/lista avaliada para esta regra.

Source of truth: label humana registrada antes da execução avaliada. O output
do detector e pareceres de LLM não criam nem alteram ground truth.

Métrica primária: precisão por emissão, `TP / (TP + FP)`, com intervalo Wilson
bilateral de 95%. Métricas secundárias: recall, emissões ambíguas, abstenções
ambíguas e matriz de erros por família.

Uma proposta de promoção só pode chegar ao gate humano se, simultaneamente:

1. precisão pontual >= 0,95 e limite inferior Wilson >= 0,95;
2. zero falso positivo conhecido e zero emissão em caso rotulado ambíguo;
3. no mínimo 73 emissões corretas no conjunto aprovado combinado;
4. pelo menos 30 dessas emissões estiverem em holdout congelado antes da
   execução, distribuídas por no mínimo três famílias independentes de fonte;
5. nenhum head terminal se repetir nas tranches novas, nenhum head contribuir
   com mais de duas emissões no conjunto combinado e nenhum frame lexical de
   lead-in contribuir com mais de três emissões;
6. houver representação procedural e descritiva, cinco formas de marcador,
   LF/CRLF, casing e indentação de 0–3 espaços;
7. controles negativos e ambíguos cobrirem todas as condições de abstenção
   conhecidas;
8. a proveniência e o direito de redistribuição de cada caso estiverem
   registrados;
9. a suíte completa, gate offline e revisão independente estiverem verdes.

Os números 73 e 30 têm papéis diferentes. Setenta e três é o primeiro total
com zero FP cujo limite inferior Wilson alcança 0,95. Trinta casos de holdout
não atingem esse limite isoladamente; servem como guardrail mínimo contra medir
somente exemplos que já influenciaram o código. Portanto, nem 73 casos
correlacionados nem 30 casos de holdout isolados bastam.

## Partições e congelamento

### A. Regressão existente

- 29 casos aprovados;
- 11 emissões corretas, 0 FP, 3 FN e 6 abstenções ambíguas;
- preserva falhas já conhecidas, mas não prova validade externa.

### B. Challenge/development

- meta inicial: 32 violações elegíveis e pelo menos 32 controles;
- exemplos autorais e material técnico redistribuível podem entrar;
- pode revelar mudança necessária no detector;
- se uma label causar mudança de código, permanece regressão, mas deixa de ser
  evidência independente daquela versão.

### C. Holdout selado

- mínimo: 30 violações elegíveis e pelo menos 30 controles;
- labels aprovadas e arquivo hasheado antes da primeira execução;
- casos não são enviados ao revisor de implementação antes do congelamento;
- cada família de fonte corresponde a um produto/repositório e licença
  independentes; exemplos somente autorais não satisfazem esse mínimo;
- qualquer mudança de comportamento após abrir o holdout invalida seu papel de
  holdout para a nova versão e exige uma nova tranche selada.

Com o detector atual, `11 + 32 + 30 = 73` emissões corretas. Um FP bloqueia a
promoção mesmo que o Wilson ainda possa passar com uma amostra maior. Se esse FP
levar a mudança de código, a avaliação e o holdout são versionados novamente.

## Matriz mínima de diversidade

As violações elegíveis devem variar, sem replicar frases da norma:

- contexto: instrução procedural e descrição de sistema;
- relação: preparação, inspeção, registro, remoção, instalação, composição e
  localização;
- head: substantivos regulares distintos, inclusive hifenizados, sem repetir o
  token terminal nas tranches novas;
- lista: `-`, `+`, `*`, `1.` e `1)`; indentação de 0–3 espaços;
- arquivo: `.md` e `.markdown`; LF e CRLF; casing normal e caixa alta;
- entorno: início, meio e fim de documento, heading anterior, parágrafo anterior
  e conteúdo posterior não associado.

Os controles devem incluir ao menos:

- pronome nu, postmodifier, head multiword e plural irregular;
- prefixo incompleto ou com gap não-whitespace, sentença incompleta e
  pontuação diferente;
- linha em branco antes da lista, item único e run interrompido;
- lista aninhada, tab ou mais de três espaços, blockquote e plain text;
- heading, fence, inline code, link, tabela e região ignorada;
- lead-in já terminado por dois-pontos e lista semanticamente não associada.

## Proveniência e labels

Cada caso novo deve registrar:

- `case_id`, partição e família de diversidade;
- texto e formato, inteiramente autoral ou redistribuível;
- `truth`, `expected_diagnostics` e `expected_replacement`;
- origem (`project-authored` ou referência de licença/proveniência);
- `review_status`, revisor e data;
- rationale curta e autoral.

Todo caso começa como `pending-human-review`. Para material real, registrar
licença, URI de origem, data de acesso e hash do recorte autorizado. Conteúdo
corporativo confidencial não entra no Git.

## Fontes selecionadas e descoberta de amostragem

O mantenedor autorizou selecionar fontes públicas permissivas em 2026-08-13.
Três famílias foram congeladas em clones rasos temporários, fora do repositório:

| Família | Commit congelado | Licença do conteúdo | SHA-256 da licença |
|---|---|---|---|
| [`github/docs`](https://github.com/github/docs) | `9892636d38c5eede39d44ca55f203f8f83ecc045` | CC BY 4.0 | `12d3a82a7d1378e6f597ec23d63a081aeb6ec4bc8de2a76ee9dc96c34c6d7a1b` |
| [`dotnet/docs`](https://github.com/dotnet/docs) | `d29798b211622fd8581b4f49fa98ab8dabf40035` | CC BY 4.0 | `243f341367f0ee35271c8924aaf5d075157c62538042e2f3c11ff9a1fcc5539c` |
| [`microsoft/vscode-docs`](https://github.com/microsoft/vscode-docs) | `4e43ccbe67991ad881b3a37e25f73c313664122e` | CC BY 3.0 US | `df6898b7f1c1d50a220f29be50fabd03e80150b619bd2ead7ee711c19e7108a2` |

A triagem estrutural pesquisou texto Markdown, sem importar ou executar
`ste_lint`. O primeiro scan amplo justificou a Emenda 1, mas a filtragem posterior
por todas as precondições revelou que `kubernetes/website` não fornece os oito
heads elegíveis e semanticamente independentes exigidos por fonte. Por isso,
`dotnet/docs` é a substituição proposta: no snapshot acima há 77 ocorrências
estruturais com uma linha vazia e 38 heads terminais distintos antes da revisão
humana. GitHub Docs e VS Code Docs também permanecem acima do mínimo de dez
casos selecionáveis cada.

O Rust Book, as documentações Node.js e Docker Docs foram avaliados e
descartados antes do congelamento por insuficiência de candidatos estruturais.
Kubernetes permanece apenas como tentativa rejeitada, não como fonte do
holdout. Nenhum conteúdo dos clones temporários foi executado pelo detector ou
copiado ao corpus até este ponto.

### Emenda 2 aprovada — substituir Kubernetes por .NET Docs

Substituir somente a família `kubernetes/website` por `dotnet/docs`, mantendo
inalterados o mínimo de três famílias, a faixa de 8–14 violações por fonte e
todos os demais gates. A motivação é de amostragem, não de resultado do linter:
o detector continuou sem ser executado. Esta substituição e as labels do
challenge exigem aprovação humana conjunta antes do primeiro Red/Green.

## Gate atual: challenge pequeno antes do TDD

O arquivo
[`vertical-list-blank-line-challenge.jsonl`](../corpus/f7/vertical-list-blank-line-challenge.jsonl)
contém 17 labels autorais aprovadas pelo mantenedor em 2026-08-13: oito
violações dentro da nova subclasse e nove controles com emissão zero. A tranche cobre linha
vazia sem caracteres, somente espaço e somente tab; os cinco marcadores;
LF/CRLF; casing; indentação de três espaços; e as barreiras de duas linhas
vazias, conteúdo, thematic break, heading, fence, blockquote, item único e
indentação por tab.

A aprovação conjunta da Emenda 2 e dessas 17 labels autoriza somente o TDD
incremental da associação com uma linha vazia enquanto a regra permanece
`preview`. Não aprova o holdout, promoção, provider, fixer ou `safe_autofix`.

## Gate aprovado: challenge completo e holdout congelado

Após o Red/Green do challenge pequeno, foram preparados sem executar o detector:

- `vertical-list-evidence-challenge.jsonl`: 24 violações e 23 controles
  autorais adicionais, completando 32/32 no challenge combinado;
- `vertical-list-holdout.jsonl`: 30 mutações mínimas e 30 controles naturais,
  com dez pares por fonte e 30 heads positivos distintos;
- `corpus/f7/SOURCES.md`: atribuição, licença, snapshots e declaração das
  alterações.

As 107 labels novas deste gate foram aprovadas pelo mantenedor em 2026-08-13.
Antes da primeira execução, o holdout foi congelado com SHA-256
`30d30b0ab2377983f33329a032286ed6f31cfab7b92cd168fc335a66d34b1cc7`.
A aprovação autoriza a avaliação congelada, mas não promove a regra nem
autoriza fixer.

Resultado: o challenge passou após um Red/Green pré-holdout para não contar
sublista indentada como item peer. O holdout congelado produziu 13 TP, 0 FP, 17
FN e 30 TN. No conjunto combinado, TP = 56 e o Wilson inferior = 0,936. Assim,
os mínimos de 73 emissões, Wilson 0,95 e 30 emissões no holdout falharam. A
decisão reproduzível está em
[`f7-list-frozen-evaluation.md`](f7-list-frozen-evaluation.md).

## Emenda 3 — recall após consumo do holdout v1

O mantenedor autorizou em 2026-08-13 uma nova iteração de recall com holdout
independente. O holdout v1 permanece imutável e seus 17 FN passam a ser
challenge conhecido; seus resultados históricos continuam vinculados ao commit
`7bfd610`.

O diagnóstico pré-implementação separou os 17 FN em duas famílias:

1. doze listas têm marcador Markdown válido, mas o primeiro conteúdo do item é
   markup (`**`, link ou inline code); existe prosa visível lintável depois do
   delimitador;
2. cinco lead-ins são segmentados em mais de uma sentença pelo parser: dois por
   `.NET` e três por uma frase completa antes da frase terminal que introduz a
   lista.

Comportamento aprovado para esta iteração:

- um item conta para o run quando, depois do marcador, existe ao menos um code
  point não-whitespace em região lintável na mesma linha; markup inicial não
  invalida o item, mas uma linha sem prosa visível lintável continua fora;
- todos os itens peer continuam obrigados a ter a mesma indentação;
- o lead-in pode conter uma ou mais sentenças completas quando seus spans
  cobrem todo o conteúdo aparado da linha, com somente whitespace entre spans,
  e o fim da linha preserva `these <head>.`;
- permanecem iguais: Markdown somente, zero ou uma linha vazia, ao menos dois
  itens peer, head regular único/hifenizado, linha inteiramente lintável e
  ponto final como único span diagnosticado.

TDD será vertical: primeiro markup inicial de item; depois segmentação múltipla
do lead-in. O holdout v1 vira regressão somente depois dos dois ciclos verdes.
Nenhuma falha do futuro holdout v2 poderá orientar tuning da mesma versão.

O holdout v2 deve conter pelo menos 30 violações mutadas e 30 controles
naturais, usar ocorrências não presentes no v1, preservar três famílias de
fonte e ter heads positivos distintos dos casos anteriores. Labels começam
`pending-human-review`, são aprovadas e hasheadas antes da primeira execução.

Trade-off: a cobertura de Markdown real aumenta ao custo de aceitar frases
prefixas completas. O guardrail é estrutural — linha integralmente lintável,
terminal estreito e lista peer direta — e a decisão de promoção continua
exigindo zero FP natural e o gate quantitativo completo.

Non-goals: alterar o parser global, aceitar head multiword/irregular, inferir
semântica do item, promover a regra ou implementar qualquer parte do fixer.

### Holdout v2 aprovado e congelado, ainda não executado

`corpus/f7/vertical-list-holdout-v2.jsonl` contém 60 labels aprovadas pelo
mantenedor em 2026-08-13: 30 mutações mínimas e seus 30 controles naturais. A
distribuição é GitHub Docs 4, Kubernetes Website 4, VS Code Docs 1, .NET Docs
11 e Pulumi Docs 10. Essa distribuição troca tamanho mínimo por estrato por
maior número de produtos independentes; nenhum estrato excede 11 positivos.

Os 30 heads e as 30 referências `repo/path/line` são novos em relação ao corpus
anterior. A seleção foi feita por estrutura e licença, sem executar
`STE-I9-LIST-001`. Antes da primeira execução, o arquivo foi congelado em
`b91d6c6c1bd7f5955332e86e80504c1890e3437531ce352781084ab74cd07ca2`.

## Emenda 1 aprovada — uma linha vazia e mutação mínima

Antes de T2/T3, alterar o contrato de evidência e a subclasse `preview` assim:

1. admitir zero ou exatamente uma linha somente de whitespace entre o lead-in
   e o primeiro item da lista;
2. continuar abstendo com duas linhas vazias, thematic break, heading, fence,
   blockquote ou qualquer conteúdo intermediário;
3. preservar todas as precondições restantes: sentença única completa, terminal
   lexical estreito, span totalmente lintável e run de ao menos dois itens;
4. preparar primeiro uma tranche challenge pequena e humana aprovada, e só
   então aplicar TDD incremental ao detector ainda `preview`;
5. construir positivos de holdout de duas classes, reportadas separadamente:
   ocorrências naturais terminadas por ponto e mutações mínimas de exemplos
   corretamente terminados por dois-pontos, alterando somente `:` para `.`;
6. manter itens, linha vazia, contexto e provenance do recorte inalterados; a
   mutação nunca pode reescrever a sentença ou fabricar associação semântica;
7. distribuir as 30 violações esperadas pelas três fontes, com no mínimo oito e
   no máximo 14 por fonte, e acrescentar pelo menos 30 controles naturais;
8. congelar paths, linhas, texto, labels, hashes e mutações antes da primeira
   execução da versão avaliada.

Métricas naturais e mutadas não serão misturadas silenciosamente. O Wilson
combinado continua sendo o gate convencional, mas o relatório também apresenta
a matriz natural isolada e classifica a validade externa com caveat. Qualquer FP
natural ou ambíguo bloqueia promoção, mesmo se a amostra mutada fizer o limite
Wilson passar.

Essa emenda troca uma subclasse menor e rara por suporte a uma convenção comum
de Markdown. O custo é uma superfície de associação maior, controlada pelo
limite de uma única linha vazia e por novos casos negativos. Por SDD, nenhuma
label, teste ou implementação dessa mudança começou antes da aprovação
explícita da emenda, registrada em 2026-08-13.

## Alternativas consideradas

1. **Adicionar 62 variações de um template:** chega ao piso aritmético rápido,
   mas produz pseudorreplicação e foi rejeitada.
2. **Usar somente documentos reais encontrados depois de rodar o detector:** é
   mais realista, mas seleciona exemplos pelo próprio output e infla precisão;
   foi rejeitada como fonte única.
3. **Challenge autoral + holdout técnico selado:** custa mais revisão e pode
   atrasar a promoção, mas separa desenvolvimento de confirmação. É a escolha.

Trade-off: privilegiamos validade e auditabilidade em vez de velocidade. O
custo é exigir material técnico redistribuível e, possivelmente, uma nova
tranche de holdout depois de qualquer correção.

## Estratégia de testes e avaliação

- corpus: teste pela API pública da regra, count e span exato `.`;
- invariantes: IDs únicos, JSON válido, labels completas, heads novos únicos e
  caps de head/frame/família verificados automaticamente;
- integração: CLI com regra explicitamente habilitada, `.md`/`.markdown`, LF e
  CRLF;
- regressão: suíte completa, Ruff, formatação, mypy e smoke offline;
- quantitativo: matriz global e por partição, Wilson, recall e abstenções;
- revisão: consistência de labels e implementação por revisor independente,
  sem converter parecer de LLM em ground truth.

## Rollout e rollback

Este plano produz somente uma recomendação. Se o gate passar, uma mudança
separada e aprovada promove a regra para `stable`, inicialmente ainda com
`safe_autofix = false`. Como regras `stable` são habilitadas por default, essa
promoção exige teste explícito do delta de CLI e documentação de release.

Rollback da promoção: retornar a regra a `preview`, mantendo todas as fixtures
de regressão. O provider continua inexistente até outro gate aprovar
precondição/replacement e autorizar seu TDD.

## Riscos e mitigação

| Risco | Probabilidade | Impacto | Mitigação |
|---|---:|---:|---|
| pseudorreplicação lexical | alta | alto | heads únicos, cap de frames e reporte por família |
| seleção pelo output do detector | média | alto | labels e hash antes da execução |
| fonte sem direito de redistribuição | média | alto | provenance/licença obrigatórias; não admitir caso duvidoso |
| vazamento do holdout | média | médio | arquivo selado e novo holdout após mudança de código |
| zero FP sintético não generaliza | alta | alto | mínimo de três famílias técnicas independentes |
| promoção muda o lint default | alta | médio | mudança separada, teste CLI e gate humano |

## Tasks e critical path

### T1 — aprovar o contrato de evidência

- DoD: critérios, partições e fontes aceitáveis aprovados pelo mantenedor.
- Bloqueada por: nenhuma.
- Estimativa: até 0,5 dia.
- Owner: project maintainer.

Status: concluída em 2026-08-13.

### T1A — aprovar a emenda de linha vazia

- DoD: comportamento de zero/uma linha vazia, mutação mínima e reporte separado
  aprovados pelo mantenedor.
- Bloqueada por: descoberta de amostragem após T1.
- Estimativa: até 0,5 dia.
- Owner: project maintainer.

Status: concluída em 2026-08-13.

### T2 — preparar challenge/development

- DoD: 32 violações, pelo menos 32 controles, schema e invariantes verdes;
  todos ainda `pending-human-review`.
- Bloqueada por: T1A.
- Estimativa: 1–2 dias.
- Owner: Codex.

Status: concluída em 2026-08-13; challenge combinado 32/32 aprovado.

### T3 — obter e congelar holdout

- DoD: fontes aprovadas, no mínimo 30 violações e 30 controles, labels humanas,
  hash e provenance registrados antes da execução.
- Bloqueada por: T1A.
- Estimativa: 1–2 dias após acesso às fontes.
- Owner: maintainer para fontes/labels; Codex para preparação mecânica.

Status: concluída em 2026-08-13; 60 labels aprovadas e SHA-256 congelado.

### T4 — executar avaliação congelada

- DoD: matriz global/partição, Wilson, recall, abstenções, gates de qualidade e
  relatório reproduzível.
- Bloqueada por: T2 e T3.
- Estimativa: até 1 dia.
- Owner: Codex.

Status: concluída em 2026-08-13; gate falhou sem tuning pós-output.

### T5 — revisar e decidir promoção

- DoD: revisão independente concluída e decisão humana registrada. Se aprovada,
  abrir mudança separada `stable` com `safe_autofix = false`.
- Bloqueada por: T4.
- Estimativa: até 1 dia.
- Owner: project maintainer.

Status: promoção bloqueada pelos critérios quantitativos; revisão de promoção
não iniciada.

### T6 — consumir FN e executar recall TDD

- DoD: Emenda 3 registrada; duas famílias de FN cobertas por ciclos Red/Green;
  nenhuma mudança de parser global ou metadata.
- Bloqueada por: autorização humana da iteração 2.
- Estimativa: 0,5–1 dia.
- Owner: Codex.

Status: concluída em 2026-08-13; 16/17 FN recuperados, um abstido por itens
somente em inline code.

### T7 — preparar e aprovar holdout v2

- DoD: 30 pares novos, provenance/licença, labels humanas e hash antes da
  primeira execução.
- Bloqueada por: T6.
- Estimativa: 1–2 dias.
- Owner: maintainer para labels; Codex para preparação mecânica.

Status: concluída em 2026-08-13; 60 labels aprovadas e hash congelado antes da
primeira execução.

### T8 — executar avaliação v2

- DoD: hash verificado, matriz por fonte e combinada, Wilson, recall e zero
  tuning pós-output.
- Bloqueada por: T7.
- Estimativa: até 1 dia.
- Owner: Codex.

Status: concluída em 2026-08-13; v2 = 30 TP, 0 FP, 0 FN e 30 TN; combinado =
104 TP, 0 FP, 9 FN e 82 TN; Wilson inferior combinado = 0,964.

### T9 — decidir promoção v2

- DoD: revisão independente e decisão humana separada.
- Bloqueada por: T8 e todos os gates quantitativos.
- Estimativa: até 1 dia.
- Owner: project maintainer.

Status: pronta para revisão independente e decisão humana separada; nenhuma
metadata foi alterada.

Critical path: T1 → T1A → T3 → T4 → T5. T2 pode avançar em paralelo com a
preparação do holdout depois de T1A.

## Definition of Done

- contrato e labels aprovados por humano;
- partições congeladas e reproduzíveis;
- critérios matemáticos e de diversidade satisfeitos ou falha explicitamente
  registrada;
- nenhum conteúdo protegido/confidencial no repositório;
- decisão `stable` separada de qualquer decisão de fixer.
