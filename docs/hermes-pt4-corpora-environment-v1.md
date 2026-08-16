# PT4 — corpora e ambiente de referência v1

Status: Corpora and environment frozen; harness not started
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

## Corpus autoral congelado

`pt4-offset-development-proposal-v2.jsonl` contém 160 casos autorais CC BY 4.0,
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

A proposta v2 corrige as sete inconsistências confirmadas na revisão Kimi v1:
expansões completas nos casos 063, 076 e 078 e proteção consistente de
decimais/unidade nos casos 098, 099, 105 e 113. Seu SHA-256 é
`5f696644ba83bf588b4f831774d9c8e588b519df36183318740d1c107b7e7d55`.

Depois da validação mecânica e do painel descrito abaixo, os bytes aceitos foram
congelados em `pt4-offset-development-v1.jsonl`, SHA-256
`45716b0581ae7c90897a3d088953ac8efde13882e6c4ef7ecfa87c6764928f5d`.

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
`casefold` + remoção de whitespace. A auditoria da proposta v2 está `pass`, sem
sobreposição material; seu SHA-256 é
`5b213eec46525d866a8fff7cfb14625197957cd6643a659fdf70733b1323a213`.

## Painel Maritaca + Grok + Kimi 2.7

O pacote externo está em
`/home/jorge/.hermes/pt4-corpora/20260816-offset-panel-v2`. Ele contém a proposta
v2, prompt, schema, requests, respostas brutas e votos estruturados, sem saída
de candidato nem dados PONT-001. O manifesto do pacote tem SHA-256
`4e0a36b68d1b7bf92a50dede80187afcad70580c8b2e725ef65de437f5234e9c`.

Maritaca `sabia-4-thinking` e Grok solicitado como `grok-4.6`, retornado como
`grok-4.6-build`, aprovaram 160/160 na primeira revisão. Kimi solicitado como
`kimi-k2.7-code:cloud`, retornado como `kimi-k2.7-code`, aprovou 153 e contestou
sete alegações mecânicas. O validador demonstrou slices, comprimentos e code
points diretamente nos bytes; o Kimi recebeu essa prova e revotou os sete como
`approve`. O executor não converteu decisão de modelo.

Os votos finais cobrem 160 `case_id` únicos, na ordem canônica, validam no
schema e são unânimes. Seus SHA-256 são
`06f728759d02b422e2bcfabca225899fed974d654d7b9dd38d3efc1e38511a81`
(Maritaca),
`ffb9844829edc28da62315a4ff1a8c61a86106e8bc411e219aea5b64a94cd6ee`
(Grok) e
`073f6f27db6494c0b920085077bb2fc1bbda9defe7c9c8765908c1c4689a6a17`
(Kimi). O resumo auditável está em
`artifacts/hermes/pt4-corpora/model-panel-review-v2.json`.

O comando `freeze-panel` materializou corpus, hash, votos e manifesto sob
custódia externa com staging atômico. O manifesto tem SHA-256
`a0eaa255e0677d840f8d7384f12c5c317ec58946f9861f6f3c9b1db3bf9b8b3b`.

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
- o corpus side de PT4 está aberto para implementação do harness;
- PT5 permanece fechado.

## Sources

[1] https://universaldependencies.org/treebanks/pt_petrogold/index.html — UD Portuguese PetroGold
[2] https://github.com/UniversalDependencies/UD_Portuguese-PetroGold/tree/83ca567418405fdae830a3e5be55c29b6ed80a24 — frozen upstream commit
[3] https://raw.githubusercontent.com/UniversalDependencies/UD_Portuguese-PetroGold/83ca567418405fdae830a3e5be55c29b6ed80a24/LICENSE.txt — upstream license
[4] https://github.com/UniversalDependencies/UD_Portuguese-Bosque/tree/625982f781b64ac793b3a818968ea9fc6ee5a8af — Bosque r2.8 frozen commit
[5] https://api.figshare.com/v2/articles/5462500 — WikiNER v1 public metadata
[6] https://docs.figshare.com — Figshare API v2 documentation
