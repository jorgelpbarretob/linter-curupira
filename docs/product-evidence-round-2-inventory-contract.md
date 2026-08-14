# Rodada 2 — contrato byte-exato do inventário unitário

Data: 2026-08-13

Status: aprovado no sexto gate Cursor; inventário `pending-review` gerado em
duas cópias externas e aguardando revisão pré-label

Este contrato completa B1–B7 da quarta revisão independente. Ele governa apenas
um inventário mecânico `pending-review`. Não autoriza labels, rationale,
execução do linter ou promoção de regra.

## Literais e perfil pré-label

- `schema_version`: `ste-lint-product-evidence-inventory/v1`;
- `round_id`: `round-2-2026-08-13`;
- `truth`: `pending-review`;
- `review_status`: `pending-review`;
- fontes, commits, paths, hashes e exclusão de `STE-I9-SENT-001`: os literais
  congelados no plano e no scanner;
- cópia A: `/tmp/ste-lint-product-evidence-round2-inventory-a.jsonl`;
- cópia B: `/tmp/ste-lint-product-evidence-round2-inventory-b.jsonl`.

Cada objeto omite, em vez de preencher com `null`, `rationale`, `reviewer` e
`reviewed_at`. É proibido qualquer campo de texto-fonte, contexto, excerpt,
preview ou versão limpa. Metadados de um caractere, como `terminal` e
`punctuation`, não são excerpts.

## Coordenadas e projeção de visibilidade

O arquivo é decodificado uma vez como UTF-8, sem normalizar Unicode ou newline.
Linhas aceitas terminam somente em LF ou CRLF; a auditoria aborta diante de CR
isolado ou dos separadores U+000B, U+000C, U+001C–U+001E, U+0085, U+2028 e
U+2029. Assim, `splitlines(keepends=True)` e os starts derivados de `\n`
produzem a mesma partição.
`start_offset` é inclusivo e `end_offset` exclusivo, ambos em code points Python
do texto decodificado. O recorte canônico é sempre `text[start_offset:end_offset]`;
`slice_sha256` é exatamente:

```text
SHA256(text[start_offset:end_offset].encode("utf-8")).hexdigest()
```

`start_line`, `start_column`, `end_line` e `end_column` são 1-based. O par final
representa a posição exclusiva `end_offset`; EOF é uma posição válida. Line
starts são calculados diretamente dos `\n` originais; em CRLF, `\r` permanece
um code point da linha anterior.

O algoritmo de posição forma `line_starts = [0] + [i + 1 para cada
text[i] == "\\n"]`. Para qualquer offset entre zero e `len(text)`, inclusive,
seleciona o maior line start menor ou igual ao offset. A linha é o índice
1-based desse start e a coluna é `offset - line_start + 1`. Portanto, EOF após
newline é linha final vazia, coluna 1; EOF sem newline é uma posição após o
último code point da última linha.

O extrator cria uma projeção com o mesmo comprimento em code points do arquivo:

- code point de prosa visível permanece na mesma posição;
- markup reconhecido vira um U+0020 por code point;
- newline original permanece newline;
- label visível de link permanece em sua posição original; marcadores e destino
  viram espaços;
- marcador de lista/blockquote vira espaços e o corpo visível permanece;
- linha estrutural inequivocamente ignorável vira espaços, preservando newline;
- constructo sem fechamento ou markup inline reconhecidamente incompleto não é
  descartado: seu conteúdo permanece projetado e recebe contexto/flag incerto.

Assim, toda posição projetada mapeia 1:1 para o arquivo bruto. Inserções para
unir linhas são proibidas. Sentence matching usa whitespace original da
projeção. A máscara estrutural e as regras de bloco são as mesmas do
`count-only`; qualquer refactor deve primeiro reproduzir seus totais congelados.

### Envelopes brutos de bloco

Linhas usam `splitlines(keepends=True)` e um vetor cumulativo de offsets. O
conteúdo físico de uma linha exclui somente seu terminador `\n`, `\r\n` ou
`\r`; espaços finais anteriores ao terminador permanecem.

`block_start_offset` é o início físico da primeira linha participante, incluindo
indentation, marcador de lista ou `>`. `block_end_offset` é a posição exclusiva
depois do último code point do conteúdo físico da última linha participante;
ele exclui o terminador dessa linha e inclui seus espaços finais. Os envelopes
são:

- `prose`: sequência máxima de linhas adjacentes não vazias e não estruturais
  que não começam novo item nem blockquote;
- `list-item body`: linha do marcador e suas linhas seguintes não estruturais
  com indentation maior que a do marcador; termina antes de item peer ou nested,
  linha vazia, blocker ou linha com indentation menor ou igual;
- `quote`: sequência máxima de linhas adjacentes reconhecidas pelo marcador
  blockquote; os marcadores permanecem no envelope e viram espaços na projeção.

Linha vazia ou estrutural faz flush. Novo item, inclusive nested, faz flush do
bloco de sentença anterior e abre bloco próprio. Uma linha indentada continua o
`list-item body` somente quando sua indentation é maior que a do marker que o
abriu. Fora desse caso, ela segue a classificação estrutural congelada.

## Contrato de recorte por unidade

| `unit_kind` | Regra | `[start_offset:end_offset)` bruto |
|---|---|---|
| `sentence_complete` | `STE-I9-SENT-001/002` | do primeiro code point visível não-whitespace depois do candidato anterior até depois do terminal `.`, `!` ou `?` e de aspas/parênteses de fechamento imediatamente contíguos |
| `sentence_incomplete` | `STE-I9-SENT-001/002` | do primeiro ao último code point visível não-whitespace da cauda sem terminal do bloco |
| `paragraph` | `STE-I9-PARA-001` | do primeiro ao último code point visível não-whitespace do bloco top-level de prosa, incluindo markup bruto intermediário e excluindo whitespace delimitador externo |
| `semicolon` | `STE-I9-PUNCT-001` | somente o caractere literal `;`, portanto `end_offset = start_offset + 1` |
| `list_run` | `STE-I9-LIST-001` | do início físico da linha do primeiro peer até depois do último code point não-newline da continuação do último peer; inclui indentation, markers, itens nested e markup bruto internos |

Blocos de sentença nunca atravessam linha vazia, heading, tabela, fence,
shortcode de bloco, item peer ou outro limite já congelado na scanner-spec. Cada
item, inclusive nested, é bloco próprio para sentença. O fechamento permitido
após terminal é o conjunto literal `"'’”)]`.

O matcher Python 3.12, sem flags adicionais, é exatamente:

```text
re.compile(r"[.!?](?=[\"'’”\)\]]*(?:\s|$))")
```

Para cada envelope, varrer `projection[block_start:block_end]` com `finditer`,
sem concatenar ou inserir espaços. Um cursor relativo começa em zero. Para cada
match, localizar o primeiro code point projetado não-whitespace entre o cursor e
o terminal, inclusive. Se existir, emitir `sentence_complete` desse offset bruto
até depois do terminal e de todos os caracteres imediatamente contíguos do
conjunto `"'’”)]`; depois mover o cursor para esse fim. O campo `terminal` é
somente o `.`, `!` ou `?` encontrado.

Após o último match, calcular a cauda exata
`projection[cursor:block_end].strip(" \\t\\r\\n\\\"'’”)]")`. Se ela contém
`\w` segundo `re.search` sem flags, emitir exatamente um `sentence_incomplete`.
Seus limites são o primeiro e o último code point da cauda depois desse strip,
mapeados diretamente ao arquivo bruto. Match sem code point não-whitespace antes
do terminal não emite registro. Todos os candidatos do envelope usam seus
`block_start_offset` e `block_end_offset` físicos acima.

O recorte de `list_run` não inclui o lead-in. Quando houver candidato a lead-in,
seus offsets exclusivos e seu hash seguem a mesma receita e entram em campos
separados. Sem lead-in, offsets são `-1` e hash é string vazia.

## IDs, unicidade e ordenação

Inteiros entram em decimal ASCII sem sinal `+` e sem zeros à esquerda. O payload
de `case_id` concatena, nessa ordem, os valores abaixo separados por um byte NUL
e sem NUL final:

```text
round_id, rule_id, source_id, path, start_offset, end_offset, unit_kind
```

`case_id` é `r2-` seguido de
`SHA256(payload.encode("utf-8")).hexdigest()`. A chave de deduplicação é a tupla
dos mesmos campos exceto `round_id`; repetição da chave ou de `case_id` aborta a
geração inteira.

Todo candidato de sentença recebe `ambiguity_group`. O payload usa os literais
`round_id`, `ambiguity`, `source_id`, `path`, `block_start_offset` e
`block_end_offset`, também separados por NUL. O valor é `ag-` seguido do SHA-256
hexadecimal. Sentenças do mesmo bloco compartilham o grupo; grupos não atravessam
arquivo nem bloco.

Ordem global de linhas JSONL:

1. fonte pela ordem literal `dapr`, `otel`;
2. `path` por ordem crescente de code point Unicode;
3. `start_offset`, depois `end_offset`, crescentes;
4. regra pela ordem literal `STE-I9-SENT-001`, `STE-I9-SENT-002`,
   `STE-I9-PARA-001`, `STE-I9-PUNCT-001`, `STE-I9-LIST-001`;
5. `unit_kind` pela ordem da tabela de recortes;
6. `case_id` crescente.

Sobreposição de spans entre regras é esperada e não é deduplicada.

## Enums e campos obrigatórios

Enums fechados:

- `text_type`: `procedural`, `descriptive`;
- `unit_kind`: os cinco valores da tabela de recortes;
- `structural_context`: `visible_prose`, `markup_or_code`, `uncertain`;
- `sentence_status`: `complete`, `incomplete`;
- `marker_family`: `bullet`, `ordered`;
- `lead_in_status`: `found`, `not_found`, `uncertain`;
- `list_terminal`: `period`, `colon`, `other`, `absent`;
- blocker LIST: `heading`, `fence`, `thematic_break`, `blockquote`,
  `more_than_one_blank_line`.

Campos comuns, presentes em todo objeto e sem extras livres:

- `schema_version`, `round_id`, `case_id`, `rule_id`;
- `source_id`, `commit`, `path`, `text_type`;
- `start_offset`, `end_offset`, `start_line`, `start_column`, `end_line`,
  `end_column`;
- `unit_kind`, `structural_context`, `has_uncertain_markup` booleano;
- `slice_sha256`, `truth`, `review_status`.

Campos adicionais obrigatórios:

| Regra | Campos |
|---|---|
| `STE-I9-SENT-001/002` | `sentence_status`, `terminal` (`.`, `!`, `?` ou string vazia), `raw_alpha_token_count`, `ambiguity_group`, `block_start_offset`, `block_end_offset` |
| `STE-I9-PARA-001` | `candidate_terminal_count`, `block_start_offset`, `block_end_offset` |
| `STE-I9-PUNCT-001` | `punctuation` com valor literal `;` |
| `STE-I9-LIST-001` | `marker_family`, `indentation`, `peer_count`, `blank_lines_before`, `lead_in_status`, `lead_in_start_offset`, `lead_in_end_offset`, `lead_in_slice_sha256`, `list_terminal`, `blockers` |

`blockers` é lista sem duplicatas na ordem do enum acima. `raw_alpha_token_count`
conta runs Unicode para os quais `str.isalpha()` é verdadeiro, separados por
qualquer outro code point, dentro da projeção do recorte; é navegação, nunca
label. `candidate_terminal_count` usa o mesmo matcher superinclusivo de sentença.

`structural_context` de sentença e parágrafo é `visible_prose` ou `uncertain`.
Para `semicolon`, ele pode assumir os três valores. Para lista, é
`visible_prose` ou `uncertain`. Qualquer constructo incerto sobreposto define
`has_uncertain_markup=true` e força `structural_context=uncertain`.

## LIST e associação de lead-in

Existe um objeto por run mecânico com dois ou mais peers do mesmo nível e
família; nested runs são objetos próprios. O span do run inclui continuações e
nested content, mas `peer_count` conta somente peers diretos.

O marcador é reconhecido, sem flags, por
`r"^( *)(?P<marker>(?:[-+*])|(?:\d+[.)]))\s+(?P<body>.*)$"`.
`indentation` é a quantidade de U+0020 no primeiro grupo e `marker_family` é
`ordered` quando o primeiro code point de `marker` é dígito, senão `bullet`.

Uma run ativa tem chave `(indentation, marker_family)`. Marker peer da mesma
chave incrementa `peer_count`; marker mais profundo é conteúdo da run pai e pode
abrir run nested própria. Marker menos profundo termina runs mais profundas;
marker da mesma indentation com outra família termina a run anterior. Linha
estrutural ou blockquote termina todas as runs. Linha não vazia sem marker
termina uma run quando sua indentation é menor ou igual à da run; indentation
maior é continuação. Linha vazia não termina nem aumenta o span.

O `start_offset` da run é o início físico da linha do primeiro peer, incluindo
indentation. O `end_offset` avança após cada peer e após cada linha não vazia de
continuação ou nested content pertencente à run pai; ele é sempre a posição
exclusiva após o conteúdo físico, sem terminador de linha. Ao terminar, blanks
finais não entram no span. Se o último peer contém uma run nested, o span pai
termina no mesmo ponto ou depois do span filho; o objeto filho mantém seus
próprios offsets sobrepostos. Run com menos de dois peers não emite objeto.

O candidato a lead-in é o bloco visível imediatamente anterior. Seu
`lead_in_start_offset` é o primeiro code point projetado não-whitespace do bloco
e `lead_in_end_offset` fica depois do último; o recorte bruto inclui todo markup
e newline intermediário. Seus campos são
preenchidos mesmo quando a distância ou um blocker o coloca fora da subclasse
normativa; isso permite `out_of_scope` posterior sem perder o caso. Headings,
fences, thematic breaks e blockquotes entre lead-in e run entram em `blockers`.
Mais de uma linha vazia adiciona `more_than_one_blank_line`.

`blank_lines_before` é o número exato de linhas whitespace-only entre o fim do
lead-in e o início do run; usa `-1` quando não há candidato. `list_terminal`
deriva do último code point visível do lead-in: `period`, `colon`, `other` ou
`absent`. O inventário não decide se o lead-in corresponde a `these <head>`.

Tabela de decisão:

| Condição | `lead_in_status` | Offsets/hash | `blank_lines_before` | `list_terminal` |
|---|---|---|---:|---|
| nenhum bloco visível anterior no arquivo | `not_found` | `-1`, `-1`, `""` | `-1` | `absent` |
| bloco anterior e nenhum constructo incerto sobreposto ao bloco ou intervalo | `found` | span/hash válidos | contagem exata | derivado |
| bloco anterior com constructo incerto sobreposto ao bloco ou intervalo | `uncertain` | span/hash válidos | contagem exata | derivado |

Para `not_found`, a validação de round-trip do lead-in é pulada e exige
exatamente os sentinels da tabela. Para `found` e `uncertain`, offsets devem ser
válidos, o recorte não pode ser vazio e o round-trip/hash é obrigatório.
`blockers=[]` quando nenhum blocker ocorre.

## JSONL canônico, hash e invariantes

Cada objeto é serializado por Python 3.12 com:

```text
json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
```

Cada serialização recebe exatamente um `\n`; o arquivo termina em `\n` e é
codificado UTF-8. O scanner monta e valida todos os bytes em memória antes de
escrever atomicamente por arquivo temporário irmão e `os.replace`.

A geração inicial escreve uma vez na cópia A e outra na cópia B nomeadas acima.
Bytes e SHA-256 devem ser idênticos. O hash aprovado é então registrado no plano; reproduções
posteriores exigem `--expected-output-sha256` e abortam antes de substituir o
artefato se houver divergência.

Hash gerado e reproduzido em 2026-08-13:
`bebbabe41b28f59e87250e188fe946b237152f9293c8765a06d1322cb3d94c38`.

Antes de escrever, abortar se qualquer condição falhar:

- auditoria O2 completa dos 16 arquivos;
- round-trip de cada `text[start_offset:end_offset]` e de cada lead-in contra o
  hash registrado no objeto, exceto o sentinel `not_found` definido acima;
- offsets em range, spans não vazios e coordenadas linha/coluna reproduzíveis;
- schema sem campo desconhecido, enum inválido ou campo proibido;
- unicidade de chave e `case_id`;
- ordenação global canônica;
- contagem exata por regra: 558, 329, 144, 69 e 73, total 1.173;
- `STE-I9-SENT-001` ausente somente no documento excluído; todas as demais
  tranches mantêm o universo congelado;
- nenhuma ocorrência textual de `ste_lint` nos imports ou subprocessos do
  scanner.

Falha não produz nem substitui JSONL. O relatório terminal contém somente
contagens, SHA-256 e paths; nunca contém recortes.

Para classificar cada `;`: `uncertain` vence quando o offset sobrepõe intervalo
incerto; caso contrário, linha estrutural ignorável ou code point mascarado na
projeção produz `markup_or_code`; o próprio `;` preservado na projeção produz
`visible_prose`.
