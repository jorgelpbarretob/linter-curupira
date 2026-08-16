# PT4 — adapter experimental spaCy v1

Status: Frozen; model-panel approved; no candidate inference
Date: 2026-08-16
Protocol: `hermes-pt4-bakeoff/v1`

## Resultado

O adapter experimental está implementado em
`tools/hermes/pt4_spacy_adapter.py`, fora de `src/hermes_lint` e sem alterar
`pyproject.toml`. Ele converte um `Doc` spaCy já analisado para o schema estrito
`hermes-pt4-linguistic-analysis/v1` congelado pelo harness. Tipos do SDK entram
somente na borda de `adapt_doc` e nenhum deles aparece no JSONL.

Este incremento não executou `pt_core_news_sm`, não produziu output candidato,
não calculou métricas, não selecionou backend e não abriu porta de produto ou
PT5.

## Interface executável

```text
pt4_spacy_adapter.py prepare-input GOLD OUTPUT
pt4_spacy_adapter.py analyze INPUT OUTPUT
```

`prepare-input` reduz uma projeção ouro aos cinco campos model-blind
`schema_version`, `case_id`, `document_id`, `text` e `abstention_reason`. O
comando recusa schema divergente e grava JSONL canônico de forma atômica, sem
sobrescrever destino existente. Ele não importa spaCy.

`analyze` importa spaCy somente em runtime, exige `spacy==3.8.15`,
`pt_core_news_sm==3.8.0`, NER excluído e exatamente os componentes congelados no
Gate 0. Carga e análise ocorrem com DNS e conexões de socket bloqueados. Ausência
do candidato, drift de versão/componentes, normalização do texto, offset
inválido, partição inconsistente, root inválido, head externo ou tentativa de
rede são erros operacionais explícitos.

## Projeção linguística

- tokens `is_space` viram lacunas, nunca superfícies artificiais;
- cada superfície satisfaz `text[start:end] == token.text` em offsets Unicode;
- nesta candidata, cada token spaCy produz uma palavra sintática ligada à mesma
  superfície; expansões MWT não são inventadas;
- `lemma_`, `pos_`, `tag_` e `morph.to_dict()` são copiados para tipos JSON;
- `ROOT` vira relação `root` com `head_word_index = null`;
- sentenças particionam todas as superfícies e palavras em intervalos contíguos,
  com envelope mínimo e heads internos;
- casos com abstenção estrutural preservam texto/identidade, emitem coleções
  vazias e não chamam spaCy.

A proveniência operacional — backend/modelo, versões, hashes de wheel/config,
ambiente e tempos — pertence ao manifesto da execução posterior. Ela não pode
ser acrescentada a cada registro candidato porque o schema v1 do harness exige
exatamente oito campos e falha diante de campos extras.

## TDD e prévia model-blind

Quinze regressões cobrem schema e offsets Unicode, normalização, slice inválido,
head entre sentenças, partição, roots, análise vazia, abstenção, remoção de ouro,
shape estrito de input, CLI canônica, UTF-8 inválido, bloqueio de rede,
configuração pinada e caminho `analyze` com double de fronteira. Nenhum teste
importa ou executa o modelo real.

As projeções ouro congeladas foram reduzidas três vezes em diretório temporário:

| Corpus | Casos | Abstenções | SHA-256 das três entradas model-blind |
|---|---:|---:|---|
| PetroGold r2.18 | 1.039 | 0 | `c241cf19a521f7d89fffed2489436218a256dace341f80123a1b5f4e55662e4b` |
| offsets autorais v1 | 160 | 36 | `7f751e78a67d70dfc0849d18ce7139850e70d045e47c062e16c54a562062ca65` |

Os 1.199 registros tinham exatamente os cinco campos permitidos. Esses hashes
provam somente a separação model-blind e o determinismo de `prepare-input`; não
são output nem desempenho do candidato.

Uma checagem sintética no ambiente Gate 0, sem carregar modelo, confirmou que
`MorphAnalysis.to_dict()` representa FEATS multivaloradas como
`{"Gender": "Fem,Masc"}`. Isso coincide com a projeção congelada do harness,
que separa pares por `|` e preserva o valor CoNLL-U completo depois de `=`.

## Revisão Maritaca + Grok + Kimi 2.7

O snapshot final fixa o adapter em SHA-256
`9cd78ee6d5f0d7b51fb35efb41d01be00c3fe81f05b14c728b326c541f16c175`
e os 15 testes em
`8f2edf9faaa0d6c42054891647aec441c27b663df7b7dabf97d78d1dfb04b9ad`.
Maritaca `sabia-4-thinking`, Grok solicitado como `grok-4.6` e observado como
`grok-4.6-build`, e Kimi solicitado como `kimi-k2.7-code:cloud` e observado
como `kimi-k2.7-code` retornaram `approve`, sem findings.

Kimi encontrou UTF-8 inválido sem tratamento em um snapshot anterior. A
regressão falhou, a CLI passou a retornar erro operacional 2 sem traceback e os
três modelos revisaram os novos hashes. Dois outros achados Kimi foram
rejeitados por prova mecânica do schema estrito e da representação de FEATS;
nenhuma decisão do modelo foi alterada pelo executor. Metadados e hashes estão
em `artifacts/hermes/pt4-spacy-adapter/model-panel-review-v1.json`.

## Fronteiras e próximo WIP

- spaCy/modelo continuam ausentes das dependências do produto;
- Stanza continua inelegível por licença e não foi adquirido;
- os 4 FP e 15 FN de `HERMES-PT-PONT-001` permanecem selados;
- a Himavai não recebe UAT porque não existe jornada de produto nova;
- a revisão de implementação usa Maritaca, Grok e Kimi 2.7, sem gate humano;
- a primeira inferência controlada e o selamento dos outputs são o próximo ato
  somente depois da unanimidade e das validações deste snapshot.
