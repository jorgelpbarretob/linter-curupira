# PT4 — harness experimental v1

Status: Frozen; model-panel approved; no candidate inference
Date: 2026-08-16
Protocol: `hermes-pt4-bakeoff/v1`

## Resultado

O harness pré-inferência de PT4 está implementado e congelado em
`tools/hermes/pt4_bakeoff_harness.py`. Ele projeta os dois corpora ouro para um
schema comum, pontua outputs candidatos já materializados e aplica os floors de
qualidade pré-registrados. Não carrega modelo, não escolhe backend e não entra no
caminho do produto.

O arquivo é stdlib-only e não importa spaCy, Stanza ou `hermes_lint`. Seus três
comandos são:

```text
pt4_bakeoff_harness.py project-conllu SOURCE OUTPUT
pt4_bakeoff_harness.py project-offset SOURCE OUTPUT
pt4_bakeoff_harness.py score GOLD CANDIDATE OUTPUT
```

Toda escrita é atômica, falha se o destino já existe e usa JSON/JSONL canônico
UTF-8. O comando `score` apenas lê outputs precomputados; não possui porta para
inferência ou download.

## Contrato executável

A projeção CoNLL-U preserva `# text` por igualdade Unicode exata, separa tokens
de superfície de palavras sintáticas, representa MWT sem inventar spans, aplica
`SpaceAfter=No` na unidade de superfície e exige exatamente uma raiz por
sentença. IDs, HEAD, FEATS e envelopes inválidos falham antes de produzir ouro.

A projeção do corpus autoral exige o schema v2 e o estado
`model-panel-approved`, valida spans, partições contíguas de tokens/palavras e
envelopes mínimos, e preserva as 36 abstenções estruturais sem remover casos.

O scorer exige bijeção e ordem canônica de `case_id`, texto idêntico e shape
estrito sem campos de SDK. Tokens casam somente por `(start, end, text)`; palavras
casam por ordem somente dentro de superfícies casadas. Toda palavra sem par entra
nos contadores e erra as métricas aplicáveis. Heads são comparados pela bijeção
determinística de palavras; head não alinhado erra UAS e LAS. FEATS micro-F1
conta somente pares reais `feature=value`; `[]` é o conjunto vazio explícito e
`null` significa que o corpus não fornece ouro linguístico.

## Projeções e self-checks

As três projeções independentes produziram hashes idênticos:

| Corpus | Casos/sentenças | Superfície | Palavras | SHA-256 das três execuções |
|---|---:|---:|---:|---|
| PetroGold r2.18 | 1.039 | 27.453 | 29.623 | `18b5a2d3d8475e2ce9546bf62ac5cde7450c45a0580bbdc93a46ec29787b5440` |
| offsets autorais v1 | 160 | 872 | 915 | `884c2a890ef680105266d38df6fe34d482804301627e2d907750c467ed38f48f` |

O self-score PetroGold tem zero erro de offset, 29.623 palavras alinhadas e
todas as métricas em `1,0`; seu artefato tem SHA-256
`665cc62f1a985d5c635ce0c8ae5f29932d03215fc3e5c3286bfe73ee8743638e`.
O self-score autoral tem zero erro de offset, token/sentence F1 `1,0` e métricas
linguísticas `null`, pois esse corpus congela offsets e estrutura, não lemma,
UPOS, FEATS ou dependências; SHA-256
`dc32a7930e9a09665fa28588e0d2ed877a5ce8b29d541aec8c13e4aef46dcaae`.

Esses números são fixtures com resposta conhecida. Não medem nenhum candidato e
não podem ser apresentados como desempenho de backend.

## Revisão Maritaca + Grok + Kimi 2.7

O desenvolvimento seguiu TDD. Revisões intermediárias encontraram e fecharam
erros reais de desalinhamento, partições de sentença, `SpaceAfter=No`, envelopes
ouro, IDs malformados, shape candidato e semântica de FEATS. Cada correção gerou
regressão antes do novo snapshot; votos de snapshots anteriores não foram
transportados para o v5.

O snapshot final fixa o harness em SHA-256
`09d79236e96b998e6f02a65b52feab505870a01db25975960ce3bed265c871cf`
e os 34 testes em
`39e59e27af7f23738b0fb41512018cb812fa5b54ae9af18a66d8f08c5cf2c415`.
Maritaca `sabia-4-thinking`, Grok solicitado como `grok-4.6` e observado como
`grok-4.6-build`, e Kimi solicitado como `kimi-k2.7-code:cloud` e observado como
`kimi-k2.7-code` retornaram votos finais `approve`, sem findings.

O Grok recebeu um schema que acrescentou somente consistência lógica entre
veredito e findings; o modelo continuou livre para aprovar ou emitir achado.
O Kimi contestou duas hipóteses fora do contrato no primeiro output v5, recebeu
prova determinística e revotou `approve`; depois o próprio modelo reemitiu os
mesmos valores com os nomes exigidos pelo schema. O executor não converteu
decisão de modelo. Cadeia completa, tokens, IDs e hashes estão em
`artifacts/hermes/pt4-harness/model-panel-review-v1.json`.

## Validações

- 34 testes dedicados do harness passaram;
- suíte completa: 357 testes passaram e 4 skips NLP esperados;
- Ruff, formatação e mypy passaram;
- smoke offline da CLI passou;
- projeção tripla, hashes, JSON estrito e `git diff --check` passaram.

## Fronteiras e próximo WIP

- nenhuma saída candidata foi vista ou produzida;
- nenhuma inferência, rede de backend ou download ocorreu;
- nenhum adapter ou dependência entrou no produto;
- nenhum backend foi selecionado;
- Stanza continua inelegível por licença;
- os 4 FP e 15 FN de `HERMES-PT-PONT-001` permanecem selados;
- PT5 continua fechado;
- não existe jornada executável nova para UAT da Himavai neste incremento.

Com o harness aprovado, o próximo WIP=1 é o adapter experimental spaCy, ainda
fora do caminho de produção. A primeira inferência controlada e o selamento de
outputs permanecem atos posteriores do protocolo; este documento não os
executa nem os autoriza por si só.

## Sources

[1] https://universaldependencies.org/format.html — CoNLL-U format, MWT and FEATS
[2] https://universaldependencies.org/misc.html — token-level `SpaceAfter=No`
