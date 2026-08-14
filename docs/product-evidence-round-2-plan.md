# Evidência de produto — plano pré-registrado da Rodada 2

Data: 2026-08-13

Status: inventário e labels das cinco regras congelados; aguardando decisão
humana para a primeira execução controlada; linter intacto

## Objetivo e barreira de contaminação

Esta rodada amplia a evidência independente das cinco regras determinísticas e
cria ground truth de não-emissões para medir recall. Ela não implementa regra,
fixer, SARIF, Semantic Reviewer ou derivação pt-BR.

As fontes não aparecem em corpora, planos de avaliação ou fixtures anteriores
do projeto. Os clones são rasos, temporários e externos ao repositório. Antes
deste documento foram usados somente `git`, `find`, `wc`, `rg`, `perl` e hashes
para verificar licença, formato e rendimento estrutural. Não houve importação,
CLI, parser, engine ou regra de `ste_lint` sobre as fontes.

Depois da aprovação do Cursor, o trabalho continuará nesta ordem:

1. inventário mecânico independente das unidades de ground truth;
2. labels propostas sem consultar a saída do linter;
3. revisão integral das labels pelo Cursor em modo somente leitura;
4. congelamento do JSONL de metadados e seu hash;
5. primeira execução do linter;
6. matriz de erro, métricas e novo parecer do Cursor;
7. decisão humana separada.

Qualquer consulta ao linter antes do passo 5 invalida esta amostra como holdout.
A classificação mecânica e as unidades estão congeladas na
[especificação independente do scanner](product-evidence-round-2-scanner-spec.md).
O resultado mecânico está registrado em
[`product-evidence-round-2-count-only.md`](product-evidence-round-2-count-only.md).
O perfil unitário está congelado no
[`product-evidence-round-2-inventory-contract.md`](product-evidence-round-2-inventory-contract.md).
Sua execução está registrada em
[`product-evidence-round-2-inventory-validation.md`](product-evidence-round-2-inventory-validation.md).
A primeira tranche aceita está registrada em
[`product-evidence-round-2-punct-label-validation.md`](product-evidence-round-2-punct-label-validation.md).
A tranche LIST aceita está registrada em
[`product-evidence-round-2-list-label-validation.md`](product-evidence-round-2-list-label-validation.md).
A tranche PARA aceita está registrada em
[`product-evidence-round-2-para-label-validation.md`](product-evidence-round-2-para-label-validation.md).
A tranche SENT-002 aceita está registrada em
[`product-evidence-round-2-sent-002-label-validation.md`](product-evidence-round-2-sent-002-label-validation.md).
A tranche SENT-001 aceita está registrada em
[`product-evidence-round-2-sent-001-label-validation.md`](product-evidence-round-2-sent-001-label-validation.md).

## Fontes congeladas

O repositório oficial do Dapr informa que contém os Markdown usados para gerar
sua documentação.[2] O snapshot escolhido é o commit
`f337722b406a95ae9fab932f1294b09f824ca20f`, de
`2026-08-12T12:03:02-07:00`.[3] Seu `LICENSE` é Apache-2.0, com SHA-256
`0b9cab20a5e2ae7e44f40a5ee6b8416f12d2135a547f9fef00e5b61f8d5be99a`.[4]

O repositório oficial do OpenTelemetry identifica o conteúdo como website e
documentação e declara CC BY 4.0 para documentação.[1] O snapshot escolhido é o
commit `8d47fa1c9303ae1e1807e1c7a122720ba62986ed`, de
`2026-08-13T19:41:02-04:00`.[5] O `LICENSE` da documentação tem SHA-256
`6f9997b6f85f473f853aeef19b5f16504dd228ba99cee70e5a19211df947a2b3`.[6]

Nenhum texto dessas fontes será copiado para este repositório. Metadados podem
conter somente projeto, commit, path, linhas, hash do recorte, label e rationale
curta autoral. A inspeção e a revisão usam os clones temporários congelados.

Os identificadores de fonte e seus snapshots são literais congelados:

- `dapr` -> `f337722b406a95ae9fab932f1294b09f824ca20f`; todo path começa por
  `daprdocs/`;
- `otel` -> `8d47fa1c9303ae1e1807e1c7a122720ba62986ed`; todo path começa por
  `content/`.

## Frames estruturais

Os diretórios foram escolhidos por função documental antes de qualquer
resultado do linter:

| Fonte | Tipo congelado | Diretório | Tree Git | MD | Palavras brutas | `;` em linhas | Marcadores de lista | Blocos com >=5 terminais |
|---|---|---|---|---:|---:|---:|---:|---:|
| Dapr | `procedural` | `daprdocs/content/en/getting-started/quickstarts` | `36db4ace5247d22f79ccca15e1d65d288ed64ad0` | 15 | 56.650 | 646 | 815 | 345 |
| Dapr | `descriptive` | `daprdocs/content/en/concepts` | `3aa1d6e6cc5f1a716e5926200700f59e75e6fa57` | 19 | 13.110 | 7 | 157 | 35 |
| OpenTelemetry | `procedural` | `content/en/docs/zero-code` | `b63291ce569cfda5c26e8b841e7834e6a604a703` | 82 | 73.877 | 227 | 995 | 464 |
| OpenTelemetry | `descriptive` | `content/en/docs/concepts` | `9be2405d69bc114e6d0d3227232e32664a88b109` | 20 | 16.949 | 45 | 227 | 61 |

Essas contagens são somente filtros brutos e incluem markup ou código. Não são
denominadores de produto nem estimativas de TP, FP ou recall.

## Seleção determinística de documentos

Seed público: `ste-lint-product-evidence-r2-2026-08-13`.

Para cada frame:

1. enumerar `*.md` recursivamente;
2. excluir `_index.md`;
3. manter arquivos com 300–3.000 palavras brutas;
4. calcular `SHA256(UTF-8(seed + "|" + path))`, sem newline final;
5. ordenar crescentemente pela selection key;
6. escolher os quatro primeiros.

A variável `path` é sempre o path POSIX completo relativo à raiz do respectivo
repositório, sem prefixo de fonte, `./`, abreviação ou normalização. A operação
canônica é `hashlib.sha256(f"{seed}|{path}".encode("utf-8")).hexdigest()`.

A seleção tem 16 arquivos e 21.972 palavras brutas. Selection key e SHA-256 do
arquivo ficam congelados abaixo.

| Tipo | Selection key | SHA-256 | Path canônico relativo ao repositório |
|---|---|---|---|
| procedural | `6f33fbe189b24db4be04d1215c4c4500c4901d019d67f47ffac8bebfc2e898c0` | `bbd806d2d7299bb3db37f1114f21386636f8e9ecd584ff952ddc2760f7fcab15` | `daprdocs/content/en/getting-started/quickstarts/configuration-quickstart.md` |
| procedural | `e4c08ee46b9ed8cc0da62d48ff39dc9abcb16a7347163008f5323fbc111b13cc` | `437d6011195d9fc3a3ce9cc2fba4c84b5ba9396d47e43b91bd78dbdeb2de2c86` | `daprdocs/content/en/getting-started/quickstarts/jobs-quickstart.md` |
| procedural | `eb7002bdaa5fd02056f31f19a1c95152d6fa9c64a547363aeadf37ba2d306649` | `70c54a69d452325b8518c275950929a609287c6f88b05f3fb53e7a7458b87368` | `daprdocs/content/en/getting-started/quickstarts/cryptography-quickstart.md` |
| procedural | `f3aef296165938d91d512b24fc7f1f25a477b90257e1497a21fd35a939e5fb99` | `324ead76d29eb3d7d633a3a497aef55f8b1b15d9e2192878de6c140759d2341d` | `daprdocs/content/en/getting-started/quickstarts/secrets-quickstart.md` |
| descriptive | `0ac18827deb60c2bb384de1ff77d238c99b8b44ea02706c299f9067512e94ee9` | `ba9b586529b557d632eb243f79579bbd97d63737da102b53e616272947cf6a4c` | `daprdocs/content/en/concepts/dapr-services/sidecar.md` |
| descriptive | `1bdd674e17723787557c9e329f133a42caa4e9a6424f447022db18b8ed5a299b` | `daad265b1c8c82049f9c21a040b2919a4a5766b037708df027d657c2dad18921` | `daprdocs/content/en/concepts/dapr-services/placement.md` |
| descriptive | `3f6c3aa4e6ffd445964f7fa1ff6932678362f510836c2cd3f5dffde8c826c07e` | `5b2964a8877088595b0fcb9b6e1ae97aca20bbdde2ace4dbcffee1f13b8ad681` | `daprdocs/content/en/concepts/terminology.md` |
| descriptive | `4395e0386c63aa8669a5ade49a96e4a78eb961cffd1ed90ca411cb0de1339dfe` | `8caa7f174fb59fca65a6062dcf43a13cea65daff474c3e242c8f6a664c7bfa41` | `daprdocs/content/en/concepts/dapr-services/sidecar-injector.md` |
| procedural | `003f884207e3de150e975a3ed1642fde0bdac017ddf1a3e4f814fc07e1099404` | `175c9288d30c0152ab769d4910e9a8af86a9cee57970b9eb8015f2413cee41e0` | `content/en/docs/zero-code/obi/configure/service-discovery.md` |
| procedural | `007da80080793cedc35b811641fa105f50765f9b850bfe11a14d155164e4489d` | `ab7dd019d7e8390a09d0e6ff537be23cadcbc7af3cbe463ae341209627b074f0` | `content/en/docs/zero-code/obi/configure/routes-decorator.md` |
| procedural | `01a0ef561a05af0209028eb7bcf82b54dafe9e964aa777b0654323160649d161` | `b47335a58308ce3e9916dbe6f4646b8c1c7e264c4c9c66bf02eb4dc2b564ad1f` | `content/en/docs/zero-code/dotnet/instrumentations.md` |
| procedural | `081289a86519f06dfd689cd22d0ab06de416b9bb27a53b7756f106727c799d30` | `7e608d18914d942e344bb8ae6f27a9c1c349ff172768b95f272ec06c4082b674` | `content/en/docs/zero-code/obi/network/config.md` |
| descriptive | `0e29d15cd094193b1eebc4c0f34627d38fc4e8e5c83fac4e2336286d6603b280` | `20950feea860a7ce64b1d51b7e96e95f1bafb354f6a8e35021eb0ca058c2427d` | `content/en/docs/concepts/signals/logs.md` |
| descriptive | `27bb342a0c01d87ae6f7111a107afa9d25ca8e2a9898e9d107096dfd6fdb5e3f` | `e114163e1eecc33e146a502784c484ca482648a1f278c24ab4809262d2cc0061` | `content/en/docs/concepts/signals/traces.md` |
| descriptive | `29b48f40f7e1b9b29b16ffa45206eed4bf0be7dcd21ff8bfe5eaf9c236cd0c50` | `03201825a7fa873f107834e36a34c180dfd95a2798ace2c14987740b707bcaac` | `content/en/docs/concepts/distributions.md` |
| descriptive | `4487b57e5fa23c10dd319c9fe52928369e98fb52dd62515c5df2c75f05244007` | `73df1da94d246ce1a2a9dfc2a97bd10a73740a1135d4bfbe1acf7977fa26ac92` | `content/en/docs/concepts/instrumentation/code-based.md` |

## Auditoria mecânica pré-label

A auditoria permitida até o gate é estritamente estrutural e hash-only. Ela usa
`git rev-parse HEAD`, `git rev-parse HEAD:<frame>`, `sha256sum LICENSE`,
`sha256sum <path>` e a expressão canônica de selection key acima. Não abre
saída do linter, não importa `ste_lint` e não registra conteúdo-fonte.

Resultado congelado em 2026-08-13:

- commits, quatro trees e dois hashes de licença coincidem com este plano;
- os 16 arquivos existem e seus SHA-256 coincidem com a tabela;
- as 16 selection keys foram recomputadas a partir dos paths canônicos e
  coincidem com a tabela;
- o manifesto canônico, formado por linhas UTF-8
  `source_id<TAB>path<TAB>selection_key<TAB>file_sha256<LF>` na ordem da
  tabela, tem SHA-256
  `4f09744c7eb7e1f460e68f4185b478037a4ee4500fb329bd5a62dc74cddd73a3`;
- a soma por whitespace permanece 21.972 palavras brutas;
- busca hash-only no repositório confirmou que commits e paths não aparecem em
  fixtures ou evidência anterior.

## Ground truth pré-execução

O mesmo snapshot serve às cinco regras, mas as labels são produzidas em tranches
sequenciais para preservar WIP igual a 1.

### Unidades exaustivas

- `STE-I9-SENT-001`: toda sentença de prosa visível nos sete documentos
  `procedural` retidos após a redução congelada, inclusive controles abaixo e
  acima de 20 palavras;
- `STE-I9-SENT-002`: toda sentença de prosa visível nos oito documentos
  `descriptive`, inclusive controles abaixo e acima de 25 palavras;
- `STE-I9-PARA-001`: todo parágrafo de prosa visível nos oito documentos
  `descriptive`, inclusive blocos abaixo e acima de seis sentenças;
- `STE-I9-PUNCT-001`: cada `;` bruto nos 16 documentos, rotulado como prosa
  visível, markup/código ignorável ou ambíguo;
- `STE-I9-LIST-001`: cada run Markdown com dois ou mais itens e seu lead-in
  visível mais próximo, incluindo ausência de lead-in e terminações variadas.

O inventário deve ser criado pelo scanner mecânico independente definido na
[especificação congelada](product-evidence-round-2-scanner-spec.md), sem
importar `ste_lint`. No perfil pré-label, cada unidade recebe somente os campos
fechados no contrato byte-exato, com `truth` e `review_status` iguais a
`pending-review`; `reviewer`, data e rationale são omitidos. Nenhum texto-fonte
entra no JSONL.

Labels permitidas: `violation`, `non_violation`, `ambiguous` e `out_of_scope`.
Casos `ambiguous` não contam como acerto no cenário conservador. Casos
`out_of_scope` auditam a fronteira Markdown, mas não entram no denominador
normativo.

### Redução congelada após `count-only`

A primeira contagem encontrou 685 unidades em `STE-I9-SENT-001`, acima do
limite 650. O procedimento congelado ordena os documentos dessa tranche pela
selection key em ordem decrescente, retira um por vez, pula uma retirada que
deixaria menos de dois documentos de uma fonte e para no primeiro total dentro
do limite.

O Cursor aprovou retirar somente
`daprdocs/content/en/getting-started/quickstarts/secrets-quickstart.md`, a maior
selection key procedural. A tranche passa a sete documentos, três `dapr` e
quatro `otel`, com total mecânico esperado de 558. A exclusão é específica de
`STE-I9-SENT-001`: os 16 arquivos continuam no manifesto e o documento continua
nas tranches `STE-I9-PUNCT-001` e `STE-I9-LIST-001`.

### Independência da revisão

Codex pode gerar o inventário e propor labels sem ver diagnósticos. O Cursor,
com `composer-2.5-fast` em modo `ask` somente leitura, revisa todas as labels e
devolve bloqueios. Somente labels aceitas são congeladas. O mantenedor decide se
o gate permite executar o linter; Cursor e Codex não promovem regras.

Os labelers não consultam implementações em `src/ste_lint/rules`; usam somente
esta pré-inscrição, a especificação do scanner e os contratos públicos citados.
Resultados desta Rodada 2 são uma linha de evidência independente e não serão
somados silenciosamente aos denominadores F7 nem à abertura PX4.

## Métricas pré-registradas

Após congelar ground truth, executar cada regra isoladamente no tipo aplicável e
registrar TP, FP, FN, TN e ambíguos por regra e por fonte.

- precisão: `TP / (TP + FP)`;
- Wilson bilateral de 95% sobre emissões decididas;
- recall: `TP / (TP + FN)` sobre as unidades exaustivas;
- FP por 1.000 palavras lintáveis, com denominador produzido pelo parser somente
  depois do congelamento;
- cenário conservador: ambiguidades contra a regra;
- estabilidade: baseline por documento, reaplicada sem conteúdo-fonte.

O limiar candidato permanece precisão pontual >= 0,95, Wilson inferior >= 0,95
e zero FP conhecido. Com zero FP, o Wilson inferior cruza 0,95 em 73 emissões
decididas; esse número é referência de suficiência, não licença para duplicar
templates correlacionados. Métricas são publicadas por fonte e agregadas com
ressalva de dependência documental. Recall é reportado, não otimizado à custa da
precisão.

## Stop conditions

- FP ou FN observado: consumir a rodada, registrar fixture mínima e decidir
  `rework`; não ajustar e reusar a mesma amostra como holdout de promoção;
- label contestada pelo Cursor: resolver antes da primeira execução;
- hash, commit ou licença divergente: parar sem substituir silenciosamente;
- qualquer tranche acima do limite numérico da especificação do scanner: não
  gerar JSONL rotulável; reduzir por regra antes das labels usando a selection
  key determinística, preservar duas fontes e obter nova revisão Cursor;
- limite quantitativo não atingido: manter `preview` e ampliar fonte
  independente; não agregar variações sintéticas para completar `n`;
- nenhum resultado desta rodada autoriza fixer automaticamente.

## Definition of Done da Rodada 2

- plano e manifesto aprovados pelo Cursor;
- inventário e labels pré-execução revisados pelo Cursor;
- hashes do JSONL e dos 16 arquivos conferidos;
- cinco regras executadas isoladamente no snapshot congelado;
- matrizes, Wilson, recall e FP/1.000 palavras reproduzidos;
- baseline reaplicada com zero remanescente;
- parecer pós-execução do Cursor registrado;
- decisão humana por regra registrada;
- suíte, Ruff, formato, mypy, smoke offline e scan protegido verdes.

## Histórico do gate independente

A primeira revisão Cursor devolveu `NO` por três bloqueios: paths Dapr
abreviados (B1), entrada de hash não canônica (B2) e ausência de especificação
independente do scanner (B3). Esta versão corrige os três pontos, explicita o
contrato estreito de `STE-I9-LIST-001`, adiciona auditoria hash-only e congela
limites quantitativos pré-label.

A segunda revisão Cursor devolveu `YES` limitado à implementação e execução
`count-only`. Condicionou a execução ao abort em qualquer divergência de commit,
tree, licença, arquivo, selection key ou soma de palavras. Também exigiu os
literais `source_id` acima antes de manifesto ou JSONL persistente. Labels,
JSONL rotulável e execução do linter continuam não autorizados.

A terceira revisão Cursor devolveu `YES` para a redução específica de
`STE-I9-SENT-001` e um novo `count-only`. Não encontrou bloqueio no scanner nem
na aritmética publicada e manteve labels, JSONL e linter fora do escopo.

A quarta revisão Cursor devolveu `NO` para implementar o inventário porque a
spec ainda não ligava unidades limpas a offsets e recortes brutos. Seus bloqueios
B1–B7 foram incorporados ao contrato byte-exato. A quinta revisão ainda apontou
ambiguidades nos envelopes de bloco, matcher, paths duplicados, lead-in e fim de
listas nested; O1–O5 foram fechados antes do sexto gate.

A sexta revisão Cursor devolveu `YES` para implementar e gerar duas cópias
`pending-review` somente em `/tmp`. A geração produziu 1.173 registros, cópias
byte a byte idênticas e SHA-256
`bebbabe41b28f59e87250e188fe946b237152f9293c8765a06d1322cb3d94c38`.
Labels e linter continuam bloqueados até nova revisão.

A sétima revisão Cursor congelou o inventário pré-label e autorizou somente a
tranche `STE-I9-PUNCT-001`. A oitava revisão aceitou 69/69 labels, sem caso
contestado, e congelou SHA-256
`b1ce0c8c0b418c9689df1c2de9bf7c24fb9396b9c582608834a2354195913cfa`.
Outras tranches e o linter permanecem sujeitos a decisão humana explícita.

Após autorização humana, a nona revisão Cursor aceitou 73/73 labels de
`STE-I9-LIST-001` e congelou SHA-256
`41f9110c7c60846b355ffecf3beadaac5924356a985e33df33c0898105871b10`.
Todos os casos são `out_of_scope`; a tranche audita a fronteira, mas adiciona
zero denominador normativo à regra.

Após nova autorização humana, a décima revisão Cursor auditou 144/144 labels de
`STE-I9-PARA-001` e bloqueou três casos descritivos classificados manualmente
como `out_of_scope`. A adjudicação em TDD mudou somente esses casos para
`non_violation`. A décima primeira revisão aceitou 144/144, sem contestação, e
congelou SHA-256
`2e3a96a267bacec5bbe1530ff0c3c6ddcc698bd7967b4bb669e912be7507e93c`.
A distribuição final é 86 `non_violation`, 58 `out_of_scope` e zero
`violation` ou `ambiguous`.

Após autorização humana para o próximo WIP, a décima segunda revisão Cursor
aceitou 329/329 labels de `STE-I9-SENT-002`, sem contestação, e congelou
SHA-256
`4276d16d76b7e5a79d91311252d5a9e551b9875edab2f465580b85c393fbca3f`.
A distribuição final é 15 `violation`, 166 `non_violation`, quatro `ambiguous`
e 144 `out_of_scope`.

Após autorização humana para a tranche final, a décima terceira revisão Cursor
aceitou 558/558 labels de `STE-I9-SENT-001`, sem contestação, e congelou
SHA-256
`930e5e9324c79cf3546363e324675a7d3274e13b398c7cdfc53871d264b16a8d`.
A distribuição final é 40 `violation`, 200 `non_violation`, oito `ambiguous` e
310 `out_of_scope`. As cinco tranches estão congeladas; o linter continua
bloqueado até decisão humana explícita sobre a primeira execução controlada.

## Sources

[1] https://github.com/open-telemetry/opentelemetry.io — OpenTelemetry website and documentation repository
[2] https://github.com/dapr/docs — Dapr documentation repository
[3] https://github.com/dapr/docs/tree/f337722b406a95ae9fab932f1294b09f824ca20f — Dapr Docs frozen commit
[4] https://github.com/dapr/docs/blob/f337722b406a95ae9fab932f1294b09f824ca20f/LICENSE — Dapr Docs Apache-2.0 license
[5] https://github.com/open-telemetry/opentelemetry.io/tree/8d47fa1c9303ae1e1807e1c7a122720ba62986ed — OpenTelemetry Docs frozen commit
[6] https://github.com/open-telemetry/opentelemetry.io/blob/8d47fa1c9303ae1e1807e1c7a122720ba62986ed/LICENSE — OpenTelemetry documentation CC-BY-4.0 license
