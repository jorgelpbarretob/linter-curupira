# Corpus do ste-lint

Status: seed-v0, revisão humana concluída em 2026-08-12

O corpus contém somente exemplos sintéticos em inglês escritos para este
projeto. Ele não contém exemplos, regras ou entradas de dicionário copiadas da
ASD-STE100, nem documentos corporativos.

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
