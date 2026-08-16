# PT4 — adapter experimental spaCy v2

Status: Frozen after sealed operational rework; model-panel approved; no candidate output
Date: 2026-08-16
Protocol: `hermes-pt4-bakeoff/v1`

## Resultado

A primeira inferência controlada do snapshot v1 falhou no warm-up descartado
do corpus de offsets. O spaCy expôs uma sentença composta somente por token
`is_space`; o adapter v1 abortou antes de criar qualquer arquivo candidato e
antes de scoring. A falha foi classificada como correção do adapter, não
infraestrutura, e o mesmo hash não foi repetido.

O rework final preserva o schema e as fronteiras do v1 e acrescenta validações
fail-closed para sentenças SDK sem superfícies, JSONL Unicode, ouro malformado,
DNS/socket e árvores de dependência. O código permanece fora de
`src/hermes_lint`, sem dependência nova no produto e sem seleção de backend.

## Regressões RED→GREEN

- sentença SDK somente-whitespace é ignorada, com índices públicos densos;
- U+0085, U+2028 e U+2029 sobrevivem ao parsing e são escapados no JSONL;
- ouro sem campos obrigatórios encerra o CLI com código 2, sem traceback;
- resolvedores DNS diretos e criação de socket falham com `AdapterError`;
- cada `ROOT` é auto-head e nenhum token não-ROOT pode ser auto-head;
- FEATS `Gender=Fem,Masc` permanece um único par nome/valor.

O snapshot final fixa `tools/hermes/pt4_spacy_adapter.py` em
`4ac1704385f00de586b4cf155fcc2df82889267183173f05d2db0dfcdef50057`
e 25 testes em
`d4afb7467947575c134e6ff663d4e8107ecb6e6f5711dd1fbb496dc618cc2a39`.

## Validação e painel

- 25 testes do adapter passaram;
- 58 testes do adapter+harness passaram;
- suíte completa: 381 passaram e 4 skips NLP esperados;
- Ruff, formatação, mypy do produto e `git diff --check` passaram;
- Maritaca `sabia-4-thinking`, Grok `grok-4.6` e Kimi
  `kimi-k2.7-code:cloud` aprovaram o delta final, sem findings.

Findings intermediários aceitos viraram regressões antes do voto final.
Findings contraditórios foram rejeitados por prova mecânica de JSON, índices de
partição, projeção model-blind e threat model. Prompts, respostas e tentativas
de transporte inválidas permanecem em custódia externa; o resumo público está
em `artifacts/hermes/pt4-spacy-adapter/model-panel-review-v2.json`.

## Fronteiras e próximo WIP

- nenhum output candidato foi criado ou visto;
- nenhuma métrica foi calculada e nenhum backend foi selecionado;
- Stanza permanece inelegível e nenhuma porta de produto/PT5 foi aberta;
- PONT-001 permanece selado; Himavai continua reservada para UAT de jornada;
- a próxima inferência deve usar nova custódia e manifesto pré-execução, nunca
  reutilizar `/home/jorge/.hermes/pt4-spacy-run/20260816-v1`.
