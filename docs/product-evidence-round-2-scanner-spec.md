# Rodada 2 — especificação do scanner independente

Data: 2026-08-13

Status: inventário unitário `pending-review` gerado; revisão pré-label pendente

## Finalidade e independência

O scanner cria um inventário superinclusivo de unidades que um revisor pode
rotular antes da primeira execução do linter. Ele não decide diagnósticos, não
calcula métricas e não tenta reproduzir o parser de produção.

Implementação permitida: programa isolado com Python 3.12 e biblioteca padrão,
fora de `src/ste_lint`. São proibidos imports de `ste_lint`, leitura das
implementações em `src/ste_lint/rules`, execução da CLI, uso de fixtures e uso
de resultados anteriores para filtrar unidades. Labelers usam somente esta
spec, `docs/rule-candidates.md` e os documentos F7 públicos citados na seção de
lista.

Entrada: os 16 paths e commits canônicos do plano da Rodada 2. Arquivos são
lidos como UTF-8, sem normalizar newline ou Unicode. Offsets são índices de code
point no texto decodificado; linhas e colunas são 1-based. Cada unidade recebe
SHA-256 dos bytes UTF-8 exatos do seu recorte, mas o recorte não entra no Git.

Literais de fonte: `dapr` identifica o commit
`f337722b406a95ae9fab932f1294b09f824ca20f` e paths `daprdocs/`; `otel`
identifica o commit `8d47fa1c9303ae1e1807e1c7a122720ba62986ed` e paths `content/`.

Saída proposta: JSONL de metadados, ordenado por fonte, path, offset inicial,
tipo de unidade e `case_id`. Antes da revisão, `truth` e `review_status` ficam
`pending-review`.

Offsets, recortes, IDs, enums, campos, ordenação, serialização e invariantes do
JSONL são normativamente fechados no
[contrato byte-exato do inventário](product-evidence-round-2-inventory-contract.md).
Em conflito, esse contrato mais específico prevalece para o modo de inventário.

## Classificação mecânica de Markdown

O scanner separa `visible_prose`, `markup_or_code` e `uncertain`. A categoria
não é ground truth; ela somente fornece contexto ao revisor.

### Blocos fora de prosa

- front matter somente no início do arquivo, aberto por `---` e fechado por
  `---` ou `...`;
- fences com até três espaços e pelo menos três crases ou tils, até fence de
  fechamento compatível;
- blocos indentados por quatro espaços ou tab quando não forem continuação
  inequívoca de item;
- headings ATX/Setext, thematic breaks, definições de referência, tabelas
  Markdown e comentários HTML;
- linhas compostas somente por tag HTML ou shortcode Hugo/Docsy.

Esses blocos continuam inventariáveis para `STE-I9-PUNCT-001`, mas recebem
contexto `markup_or_code`. Um constructo sem fechamento ou cuja categoria não
seja inequívoca recebe `uncertain`; o scanner nunca o converte silenciosamente
em prosa.

### Markup inline

- texto de inline code, autolink, destino de link e imagem é
  `markup_or_code`;
- label visível de link é `visible_prose`;
- tags HTML e marcadores de shortcode são markup; texto visível entre tags ou
  entre shortcodes pareados permanece candidato a prosa;
- marcadores de lista e blockquote são markup; o corpo visível permanece
  candidato;
- entidade HTML é uma unidade incerta para contagem e nunca prova uma palavra.

Caracteres ou constructs que o scanner não reconhece permanecem no recorte e
fazem a unidade receber flag `has_uncertain_markup=true`. O revisor decide
`ambiguous` ou `out_of_scope`; o scanner não infere equivalência com o parser.

## Unidades por regra

### `STE-I9-SENT-001` e `STE-I9-SENT-002`

O scanner forma blocos visíveis sem atravessar linha em branco, heading, tabela,
fence, shortcode de bloco, item peer ou outro limite de bloco. Dentro de cada
bloco, cria candidatos superinclusivos terminados por `.`, `!` ou `?` quando o
terminal for seguido por whitespace, fechamento de aspas/parênteses ou fim do
bloco. Fragmento final sem terminal é inventariado como `incomplete`.

Abreviações, números decimais e terminais em nomes/URLs não são resolvidos pelo
scanner. Ele registra os fragments vizinhos no mesmo `ambiguity_group`; o
revisor pode aprovar merge, split ou `ambiguous` antes de congelar labels.

Para cada sentença aceita, a label segue a paráfrase pública:

- `violation`: sentença completa do tipo congelado cuja contagem conservadora
  permanece acima de 20 (`procedural`) ou 25 (`descriptive`);
- `non_violation`: sentença completa que permanece no limite ou abaixo;
- `ambiguous`: segmentação ou construção especial pode mudar o lado do limite;
- `out_of_scope`: não é prosa do tipo congelado.

O scanner pode registrar contagem bruta de tokens alfabéticos somente como
ajuda de navegação. Essa contagem não determina `truth`.

### `STE-I9-PARA-001`

Unidade: bloco top-level de prosa visível no frame `descriptive`, delimitado por
linha vazia ou constructo de bloco. Headings, tabelas, listas, blockquotes,
código e conteúdo procedural recebem `out_of_scope`; itens de lista nunca são
fundidos em parágrafo.

- `violation`: mais de seis sentenças completas e não ambíguas;
- `non_violation`: de uma a seis sentenças completas e não ambíguas;
- `ambiguous`: qualquer dúvida de segmentação pode atravessar o limite de seis;
- `out_of_scope`: bloco excluído pelo contrato público.

### `STE-I9-PUNCT-001`

Unidade: cada caractere literal `;` dos 16 arquivos, inclusive dentro de markup,
código, URL, entidade ou shortcode. O scanner registra um contexto estrutural,
sem descartar ocorrências.

- `violation`: `;` em prosa visível;
- `non_violation`: caractere em região que deve ser ignorada pelo linter;
- `ambiguous`: fronteira estrutural incerta;
- `out_of_scope`: reservado para bytes que não representam texto documental,
  caso surja algum constructo incorporado não textual.

Assim, uma emissão em code/markup mapeia para FP e uma ausência em ponto e
vírgula visível mapeia para FN.

### `STE-I9-LIST-001`

O scanner encontra toda sequência Markdown com pelo menos dois itens peer no
mesmo nível e registra: marcador, indentação, número de itens, linhas vazias,
lead-in visível mais próximo e blockers intermediários. Nested lists são
unidades próprias; heading, thematic break, fence ou blockquote entre lead-in e
run é registrado, nunca removido.

Ground truth desta rodada cobre somente a subclasse pública estreita validada em
`docs/f7-list-provider-readiness.md` e
`docs/f7-list-recall-v2-validation.md`, não toda a Rule 4.3:

- lista direta com pelo menos dois peers e indentação Markdown de até três
  espaços;
- zero ou uma linha somente de whitespace entre lead-in e lista;
- lead-in inteiramente visível, associado à lista e terminado por
  `these <head>.`;
- `<head>` é um único token alfabético ou hifenizado, plural regular terminado
  em `s`;
- frases prefixas são permitidas, mas o padrão terminal permanece na mesma
  linha do lead-in;
- nenhuma heading, fence, thematic break ou blockquote rompe a associação.

Labels:

- `violation`: todas as precondições acima passam e o terminal é `.`;
- `non_violation`: a mesma subclasse está corretamente terminada por `:`;
- `ambiguous`: associação, visibilidade ou head não pode ser decidido;
- `out_of_scope`: qualquer outro run, inclusive pronome nu, head multiword ou
  irregular, lista indireta, mais de uma linha vazia ou blocker estrutural.

O labeler não amplia a semântica por considerar que uma lista “parece precisar”
de dois-pontos.

## Schema mínimo do inventário

Campos comuns:

- `schema_version`, `round_id`, `case_id`, `rule_id`;
- `source_id`, `commit`, `path`, `text_type`;
- `start_offset`, `end_offset`, linhas/colunas 1-based;
- `unit_kind`, `structural_context`, flags de ambiguidade;
- `slice_sha256`, sem campo de texto;
- `truth`, `review_status`, `reviewer`, `reviewed_at`, `rationale`.

O conjunto exato de campos específicos e a política de ausência são fechados no
contrato byte-exato. Nenhum campo pode carregar prosa da fonte.

## Volume e stop condition pré-label

O scanner executa primeiro em modo `count-only`, ainda sem `truth`. Limites
máximos de revisão:

| Tranche | Máximo de unidades |
|---|---:|
| `STE-I9-SENT-001` | 650 |
| `STE-I9-SENT-002` | 650 |
| `STE-I9-PARA-001` | 300 |
| `STE-I9-PUNCT-001` | 200 |
| `STE-I9-LIST-001` | 200 |

Estimativas brutas pré-scanner nos 16 arquivos: 2.462 caracteres terminais,
1.147 blocos separados por linhas vazias, 69 ocorrências de `;` e 128 inícios
aproximados de runs de lista. Código e markup explicam grande parte dos dois
primeiros números; as estimativas não são labels.

Se qualquer contagem pós-classificação exceder o limite, nenhum JSONL rotulável
é criado. O gate retorna ao plano para congelar um subconjunto menor por regra,
usando o mesmo selection key e mantendo ao menos dois documentos por fonte. A
redução exige nova revisão Cursor e acontece antes de qualquer label ou saída do
linter.

Para `STE-I9-SENT-001`, a revisão aprovou ordenar selection keys em ordem
decrescente e retirar documentos até o primeiro total dentro do limite, sem
deixar menos de dois documentos por fonte. A exclusão congelada é somente
`daprdocs/content/en/getting-started/quickstarts/secrets-quickstart.md`. Ela não
altera o manifesto de 16 arquivos nem as tranches de pontuação e lista.

## Validações do scanner

Antes de produzir inventário:

- imprimir e conferir commits, trees, licenças, hashes dos 16 arquivos,
  selection keys e total de 21.972 palavras; abortar antes da contagem em
  qualquer divergência;
- fixture autoral mínima para cada fronteira de bloco/inline acima;
- invariantes de offsets, hash, ordenação e IDs únicos;
- round-trip de cada recorte contra o clone congelado;
- teste que falha se `ste_lint` estiver importado ou executado;
- nenhum acesso de rede;
- saída `count-only` e JSONL determinísticos em duas execuções limpas.

Falha ou constructo não reconhecido aumenta ambiguidade; nunca autoriza o
scanner a eliminar a unidade.
