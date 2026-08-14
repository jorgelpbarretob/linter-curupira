# Corpus do ste-lint

> A linha abaixo descreve o corpus inglês histórico. O corpus vigente do Hermes
> nasce em `corpus/hermes/`, sob contrato e revisão próprios. Nenhuma label ou
> métrica inglesa migra como evidência pt-BR.

Status: seed-v0, revisão humana concluída em 2026-08-12

O seed contém somente exemplos sintéticos em inglês escritos para este projeto.
As tranches F7 também incluem recortes técnicos curtos e atribuídos sob licença
aberta, conforme `f7/SOURCES.md`. O corpus não contém exemplos, regras ou
entradas de dicionário copiadas da ASD-STE100, nem documentos corporativos.

## Estados de revisão

- `pending-human-review`: candidato gerado e ainda não admitido como ground truth.
- `approved`: label revisada por humano e admitida no corpus rotulado.
- `rejected`: caso ou label descartado, com justificativa.

Os 65 casos do seed inicial foram aprovados pelo mantenedor em 2026-08-12. Novos
casos sempre começam como `pending-human-review`. Concordância de LLM não muda
esse estado.

## Formato seed-v0

Cada linha de `seed/*.jsonl` é um objeto JSON independente com:

- `case_id`: identidade provisória do caso;
- `candidate`: chave provisória da candidata;
- `category`: `violation`, `non_violation` ou `edge`;
- `text_type`: tipo declarado para o caso;
- `source_format`: `txt` ou `markdown`;
- `text`: entrada sintética;
- `expected_diagnostics`: quantidade esperada para a candidata isolada;
- `review_status`: estado humano;
- `reviewed_by` e `reviewed_on`: provenance da aprovação humana;
- `notes`: intenção do caso, sem reproduzir texto normativo.

O formato é interno e provisório. Não é contrato público nem schema de saída da
CLI.

## Tranches da Fase 7

Arquivos em `f7/` podem conter tranches de desenvolvimento e avaliação. O
estado de cada label continua explícito por linha. Em particular,
`vertical-list-blank-line-challenge.jsonl` é uma tranche autoral aprovada pelo
mantenedor em 2026-08-13 e pode ser executada como ground truth do TDD limitado
à associação por exatamente uma linha vazia.

`vertical-list-evidence-challenge.jsonl` completa a meta de desenvolvimento com
24 violações e 23 controles adicionais. `vertical-list-holdout.jsonl` contém 30
mutações mínimas e 30 controles naturais provenientes das três famílias
registradas em `f7/SOURCES.md`. As 107 labels foram aprovadas pelo mantenedor em
2026-08-13. O holdout foi congelado antes da primeira execução; seu SHA-256 está
em `vertical-list-holdout.sha256`.

Após o consumo do primeiro holdout, a Emenda 3 recuperou 16 dos 17 FN como
challenge de desenvolvimento; o caso de itens somente em inline code permanece
abstenção. `vertical-list-holdout-v2.jsonl` contém 30 novos pares independentes,
com 30 heads e 30 referências de origem não usados anteriormente. Suas 60
labels foram aprovadas pelo mantenedor em 2026-08-13 e congeladas antes da
primeira execução; seu SHA-256 está em `vertical-list-holdout-v2.sha256`.
