# ADR-013: contrato do recurso de vocabulário

Status: Accepted
Data: 2026-08-12

## Contexto

O ADR-006 exige um vocabulário BYO externo e versionado, mas não define o
contrato serializado, a identidade de uma entrada, a resolução de ambiguidades
nem o limite entre importação e cache. Publicar esses detalhes sem decisão
explícita tornaria futuras migrações arriscadas e poderia incentivar a cópia de
material protegido para o repositório.

## Decisão proposta

Adotar dois documentos JSON UTF-8, estritos e sem dependência de runtime. Ambos
contêm `format`, `schema_version`, `standard`, `issue` e `entries`:

1. fonte autorizada: `format = "ste-lint-vocabulary-source"` e
   `schema_version = 1`; é o único formato aceito pelo importador da Fase 5;
2. recurso canônico: `format = "ste-lint-vocabulary"` e
   `schema_version = 1`; é o único formato consumido pelo linter e acrescenta
   `provenance`.

Na versão 1, `standard` deve ser a string JSON `"ASD-STE100"` e `issue` deve
ser a string JSON `"9"`. Outra norma, issue, tipo ou versão falha sem fallback.
As entradas da fonte e do recurso canônico têm o mesmo contrato.

Cada entrada contém:

- `term`, Unicode não vazio e sem whitespace externo;
- `part_of_speech`, identificador não vazio;
- `meaning_id`, identificador opaco não vazio;
- `case_sensitive`, booleano explícito.

Todas as strings devem estar em Unicode NFC; o loader rejeita outra
normalização em vez de alterar silenciosamente o conteúdo. `casefold` significa
o resultado de `str.casefold()` no Python 3.12 pinado pelo projeto.

Definições, exemplos normativos e texto fonte não fazem parte do schema. Chaves
JSON repetidas, chaves de objeto desconhecidas e entradas semanticamente
duplicadas são rejeitadas. Para o mesmo `part_of_speech` e `meaning_id`, duas
entradas colidem quando os termos são idênticos ou quando seu `casefold` é igual
e ao menos uma delas não é case-sensitive. Diferentes classes ou meanings podem
produzir múltiplos matches intencionais.

Antes do parse, fonte e recurso canônico ficam limitados a 16 MiB. A versão 1
aceita no máximo 100.000 entradas, `term` com até 256 code points e
`part_of_speech`/`meaning_id` com até 128. Estrutura, tipos, limites, versão,
norma, issue e integridade são validados por inteiro antes do uso.

O lookup preserva `part_of_speech` e `meaning_id` e retorna um estado fechado:
`technical`, `matched`, `ambiguous` ou `missing`. Entradas case-sensitive exigem
igualdade exata; as demais usam `casefold`. O overlay técnico é
case-insensitive, tem precedência sobre o recurso e retorna `technical`,
explicitamente identificado como política local. Depois de filtros opcionais de
classe e meaning, zero match retorna `missing`, um retorna `matched` e mais de
um retorna `ambiguous`; filtros de classe e meaning usam igualdade exata e
nenhuma escolha é inferida silenciosamente. Consumidores
de `ambiguous` ou `missing` devem abster-se ou, quando uma regra futura tiver
evidência aprovada, permanecer `preview/info`; esses estados nunca sustentam
sozinhos um veredito normativo `stable`.

`provenance` contém `source_format`, `source_schema_version`,
`source_sha256` sobre todos os bytes exatos do arquivo fonte e
`content_sha256` sobre a representação canônica de `standard`, `issue` e
`entries`.

Para calcular `content_sha256`, as entradas são ordenadas por
`(term, part_of_speech, meaning_id, case_sensitive)` usando a ordem nativa de
strings do Python 3.12 e `False` antes de `True`. O payload usa chaves nesta
ordem: `standard`, `issue`, `entries`; cada entrada usa `term`,
`part_of_speech`, `meaning_id`, `case_sensitive`. Ele é serializado por
`json.dumps(..., ensure_ascii=False, separators=(",", ":"), allow_nan=False)`,
sem newline final, codificado em UTF-8 e então submetido a SHA-256. O loader
recalcula esse hash e revalida todo o schema em cada abertura; cache truncado ou
adulterado falha. O hash da fonte registra origem, enquanto o hash de conteúdo
protege o recurso canônico: um não substitui o outro.

O comando `ste vocabulary import-json` exige `--confirm-authorized` e grava
atomicamente o recurso canônico em um cache local explicitamente informado. O
nome do arquivo é `<source_sha256>.json`, calculado internamente, sem incorporar
nomes ou caminhos do documento de entrada. O diretório de cache pode ser
absoluto ou relativo ao diretório atual, é resolvido antes da escrita e não
aceita um nome de saída fornecido pelo documento. Isso elimina path traversal
originado pelo conteúdo importado. O cache armazena somente o recurso canônico
necessário ao lookup, nunca os bytes originais da fonte.

Não há cache global implícito, rede, PDF/DOCX, extração do documento oficial ou
descoberta automática de arquivos. O importador rejeita recursos já canônicos e
qualquer outro formato; a confirmação declara somente que o usuário afirma ter
direito de processar a entrada, não concede licença nem autoriza redistribuição.

Configuração de lint aceita `[vocabulary].path`; `--vocabulary PATH` a substitui
conforme ADR-009. Caminhos relativos no TOML são resolvidos relativamente ao
próprio arquivo de configuração; caminhos da CLI são relativos ao diretório
atual. Caminhos absolutos são permitidos porque o recurso BYO pode residir fora
do projeto. O overlay técnico vem de `[glossary].terms`, já definido no contrato
de configuração, e não altera o recurso em disco.

Sem caminho configurado, o lint continua sem vocabulário e regras que declarem
essa capacidade como requisito ficam desabilitadas ou se abstêm. Quando um
caminho foi informado, arquivo ausente, inacessível, acima do limite, JSON
inválido ou duplicado, schema desconhecido, norma/issue incompatível ou hash
inválido é falha operacional orientativa antes de executar qualquer regra. A
mensagem identifica categoria e caminho, mas não imprime entradas do recurso.

## Alternativas rejeitadas

- SQLite ou binário proprietário no primeiro schema, por dificultar auditoria e
  portabilidade;
- YAML, por ampliar tipos e exigir dependência;
- embutir definições e exemplos, por não serem necessários ao lookup e elevarem
  o risco de redistribuição;
- indexar somente por palavra, porque perde classe e significado;
- escolher automaticamente o primeiro match, porque transforma ambiguidade em
  falso veredito;
- cache global automático, porque cria estado implícito e risco de vazamento.

## Consequências

- testes públicos usam somente entradas sintéticas autorais;
- recursos oficiais e caches locais continuam fora de Git, wheel e sdist;
- o hash dá provenance do arquivo autorizado, mas não concede licença sobre seu
  conteúdo;
- uma mudança incompatível exige novo major de schema e ADR;
- a Fase 5 fornece capacidade de lookup, não uma nova regra de compliance.
- cache local ou hash não substitui autorização jurídica para uso ou
  redistribuição do conteúdo.

## Revisão independente

O `cursor-agent` com `composer-2.5-fast` revisou a proposta em modo somente
leitura. A primeira revisão fundamentada encontrou dois bloqueios: falha de
recurso configurado não explicitada e colisão por `casefold`. Também apontou
gaps de schema, integridade, limites, paths e estados do lookup. Duas rodadas
subsequentes verificaram as correções; a última não encontrou bloqueantes e
recomendou aprovação após explicitar `issue` como string JSON, ajuste incorporado
nesta versão.

## Aprovação necessária

Aceito explicitamente pelo mantenedor em 2026-08-12 após três rodadas de revisão
independente com `cursor-agent` e `composer-2.5-fast`.
