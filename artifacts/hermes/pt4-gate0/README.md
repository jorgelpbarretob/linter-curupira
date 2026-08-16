# PT4 Gate 0 — elegibilidade dos candidatos

Status: Proposed pending delegated operational review
Date: 2026-08-16

Este diretório congela somente evidência anterior ao bake-off:

- `spacy-candidate-v1.json`: decisão proposta do candidato spaCy;
- `stanza-candidate-v1.json`: bloqueio de licença do candidato Stanza;
- `spacy-wheelhouse-v1.json`: 45 wheels, URLs, tamanhos, hashes, metadados e
  dependências declaradas;
- `spacy-wheelhouse-v1.sha256`: hashes no formato `sha256sum`;
- `spacy-requirements-v1.lock`: instalação offline com `--require-hashes`;
- `spacy-license-audit-v1.json`: declarações e arquivos de licença por wheel;
- `spacy-load-proof-v1.json`: carga sem texto e com rede bloqueada.

Os wheels, ambientes virtuais e scripts de auditoria permanecem fora do Git em
`/home/jorge/.hermes/pt4-gate0/20260816-spacy-v1`. Nenhum desses artefatos entra
no runtime base do Hermes. O relatório canônico está em
`docs/hermes-pt4-gate0-eligibility-v1.md`.
