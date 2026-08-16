# PT4 — corpora e ambiente de referência v1

Status: Blocked pending independent human review
Date: 2026-08-16
Protocol: `hermes-pt4-bakeoff/v1`

## Resultado deste incremento

O split oficial de teste UD Portuguese PetroGold `r2.18` foi congelado no
commit `83ca567418405fdae830a3e5be55c29b6ed80a24`. A fonte oficial identifica o
treebank como português brasileiro técnico do domínio de petróleo e gás,
revisado manualmente por linguistas e licenciado sob CC BY-SA 4.0.[1] O
repositório upstream registra `r2.18` e `r2.17` no mesmo commit; o manifesto
local seleciona explicitamente `r2.18`.[2]

O arquivo de teste foi preservado sem alteração, junto da licença upstream.[3]
Seu SHA-256 é
`069a43e29462ac24f876c43affcd12b519e2aa650b934f8591d67dae8a993f5d`.
O split contém 2 documentos, 1.039 sentenças, 27.453 tokens de superfície,
29.623 palavras sintáticas, 2.170 multiword tokens e nenhum empty node. Todo o
split permanece obrigatório; nenhuma linha pode ser removida após observar
resultado de candidato.

## Corpus autoral proposto

`pt4-offset-development-proposal-v1.jsonl` contém 160 casos autorais CC BY 4.0,
distribuídos igualmente entre:

- Unicode, diacríticos, emoji, LF e CRLF;
- contrações, clíticos e tokens multiword;
- abreviações, versões, unidades, identificadores e pontuação técnica;
- fronteiras de TXT/Markdown e abstenção estrutural.

Cada linha registra texto exato, segmentos analisáveis, spans de abstenção,
tokens de superfície com offsets, envelopes de sentença, palavras sintáticas,
razão e estado de revisão. O gerador é independente do produto e não importa
spaCy, Stanza ou `hermes_lint`. Nenhuma saída candidata, label ou erro de
`HERMES-PT-PONT-001` foi consultado.

A proposta tem SHA-256
`b0c21e03b8fa2f0e13e51927362819bbc77abc831a9aef3fcff580e30d15a438`.
Esse hash protege o pacote submetido à revisão; não é hash canônico de corpus
aceito.

## Contaminação

A auditoria cega comparou as 1.039 sentenças PetroGold e os 160 textos autorais
contra as 9.364 sentenças dos três splits oficiais Bosque r2.8, commit
`625982f781b64ac793b3a818968ea9fc6ee5a8af`.[4] Houve zero interseção por igualdade
exata e zero após NFC, `casefold` e colapso de whitespace. Também houve zero
interseção entre a proposta autoral e PetroGold.

O snapshot português WikiNER também foi resolvido. O Figshare oficial publica o
dataset DOI `10.6084/m9.figshare.5462500.v1` sob CC BY 4.0 e identifica
`aij-wikiner-pt-wp3.bz2` como o arquivo português, file ID `9446356`, com
6.059.022 bytes e MD5
`d74198c00ab91078747ee4a49aff5332`.[5] A API pública é o mecanismo oficial para
obter metadados e URLs de download por article ID.[6]

O arquivo foi congelado fora do Git com SHA-256
`d34a73ca46ebae6c83db1f4d8057406e6ceed5a7ea579407c3b35120274c48d4`.
Suas 142.112 sentenças não têm interseção com PetroGold ou com a proposta
autoral por igualdade exata, NFC + `casefold` + colapso de whitespace ou NFC +
`casefold` + remoção de whitespace. A auditoria de contaminação agora está
`pass`, sem pendências; seu SHA-256 é
`7ac450d6afca14b41e8595379ed9b5958feecb92080964603ea50fe59ee1c7c7`.

## Revisão humana obrigatória

O pacote externo está em
`/home/jorge/.hermes/pt4-corpora/20260816-offset-review-v1`. Ele contém o JSONL,
uma planilha CSV de decisão, instruções e manifesto, sem saída de modelo. Uma
segunda pessoa deve revisar e aprovar 100% dos 160 casos. O validador falha
fechado diante de campo pendente, alteração dos identificadores/hashes,
rejeição sem justificativa ou qualquer caso rejeitado.

O manifesto do pacote tem SHA-256
`e15f4595ad3498adcffda272e837ef9d9a8844c556f01ea92012ff2afd16ded2`;
o CSV inicial tem SHA-256
`8f719a4400fd6641157e9ec03dd5f49f8b428f47a49b523a93265b59705269e4`.

Enquanto essa revisão humana não existir, o corpus autoral não pode ser
renomeado como canônico e nenhuma inferência do bake-off pode começar.

## Ambiente congelado

`reference-environment-v1.json` fixa Debian 13.6 x86_64, CPython 3.12.13,
glibc 2.41 e CPU Intel i7-9700. A futura execução será CPU-only, presa ao CPU
lógico 0, com um processo e uma thread por biblioteca, locale `C.UTF-8`, fuso
UTC, seed de hash zero, GPU oculta, rede/download negados e NER excluído.

O ambiente aponta somente para o wheelhouse Gate 0 já aceito. spaCy e o modelo
continuam fora de `pyproject.toml` e do runtime base. A condição menor do parecer
Grok sobre `pip check` foi materializada em
`artifacts/hermes/pt4-corpora/spacy-offline-install-check-v1.json`, que registra
exit code zero e `No broken requirements found.`

## Fronteiras preservadas

- nenhuma inferência de candidato foi executada;
- nenhum harness ou adapter foi implementado;
- nenhum backend foi selecionado;
- nenhuma dependência entrou no produto;
- Stanza não foi adquirido;
- PONT-001 e seus erros continuam selados;
- PT5 permanece fechado.

## Sources

[1] https://universaldependencies.org/treebanks/pt_petrogold/index.html — UD Portuguese PetroGold
[2] https://github.com/UniversalDependencies/UD_Portuguese-PetroGold/tree/83ca567418405fdae830a3e5be55c29b6ed80a24 — frozen upstream commit
[3] https://raw.githubusercontent.com/UniversalDependencies/UD_Portuguese-PetroGold/83ca567418405fdae830a3e5be55c29b6ed80a24/LICENSE.txt — upstream license
[4] https://github.com/UniversalDependencies/UD_Portuguese-Bosque/tree/625982f781b64ac793b3a818968ea9fc6ee5a8af — Bosque r2.8 frozen commit
[5] https://api.figshare.com/v2/articles/5462500 — WikiNER v1 public metadata
[6] https://docs.figshare.com — Figshare API v2 documentation
