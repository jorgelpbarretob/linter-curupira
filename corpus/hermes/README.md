# Corpus Hermes

Status: PT2 holdout manifest frozen
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

`pont-001-kubernetes-holdout-manifest-v1.jsonl` é o manifesto sem labels e sem
texto externo aceito em 2026-08-14. Ele referencia 336 ocorrências literais em
90 arquivos e 73 documentos de controle do snapshot Kubernetes aprovado. O
SHA-256 canônico está em `pont-001-kubernetes-holdout-manifest-v1.sha256`. O
manifesto não é ground truth e não autoriza executar detector ou modelo.

O gerador auditável é
`tools/hermes/generate_pont_001_holdout_manifest.py`. Ele recebe um checkout
externo do snapshot, verifica commit, licença e contagens e grava somente
caminhos, hashes, coordenadas e metadados determinísticos de seleção.

O pacote com contexto para revisão é gerado por
`tools/hermes/prepare_pont_001_human_review.py` e deve permanecer sob custódia
separada, fora deste repositório. O CSV inicial contém somente decisões
`pending-human-review`; seu conteúdo ou futuras labels não devem ser copiados
para fixtures, prompts ou testes.

A revisão delegada ao Grok segue
`docs/hermes-pt2-grok-review-protocol.md`. Prompt, resposta, propostas e
ground-truth candidato permanecem fora do Git. Somente hashes e estado dos
gates são registrados aqui; o candidato não é congelado sem aprovação humana
final do hash.

O mantenedor aprovou o SHA-256
`6cab9e0a4090df19fc5c3cc5a8e93122413160f523e032367ec25849567abab6` em
2026-08-14. Os 409 registros foram congelados sob custódia externa com os mesmos
bytes. O arquivo de labels não entra neste diretório e não pode ser consultado
durante a implementação do detector.

Contrato e processo:

- `docs/adr/0018-corpus-label-and-evaluation-protocol.md`;
- `docs/hermes-annotation-guide-v0.1.md`;
- `docs/hermes-pt2-corpus-protocol.md`;
- `schema-v1.json`.
