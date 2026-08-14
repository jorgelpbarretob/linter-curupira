# Corpus Hermes

Status: PT2 pilot proposed
License: veja cada arquivo e `docs/hermes-identity-and-licensing.md`

Este diretório é exclusivo do produto pt-BR. Não reutiliza labels, thresholds
ou evidência da linha inglesa.

`pont-001-development-proposal.jsonl` contém somente exemplos sintéticos
autorais sob CC BY 4.0. Todos começam `pending-human-review`; o arquivo não é
ground truth, fixture de detector nem holdout.

`pont-001-development-v1.jsonl` é a cópia canônica aprovada pelo mantenedor em
2026-08-13. Contém 40 casos e está congelada pelo SHA-256 registrado em
`pont-001-development-v1.sha256`. É evidência de desenvolvimento, nunca
holdout, e ainda não foi executada contra qualquer detector.

Contrato e processo:

- `docs/adr/0018-corpus-label-and-evaluation-protocol.md`;
- `docs/hermes-annotation-guide-v0.1.md`;
- `docs/hermes-pt2-corpus-protocol.md`;
- `schema-v1.json`.
