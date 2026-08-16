# PT4 harness — evidência pré-inferência

Status: Model panel approved; harness frozen
Date: 2026-08-16

`harness-manifest-v1.json` fixa código, testes, schemas, corpora, projeções ouro,
self-checks e fronteiras deste incremento. `model-panel-review-v1.json` registra
os votos finais de Maritaca, Grok e Kimi 2.7, seus modelos observados, IDs,
tokens e hashes das respostas mantidas sob custódia externa.

`pt4-harness-public-v1.sha256`, SHA-256
`6089b56b3f70f5d3de3362d9242457d96b637765b2138ad5ef087e3ccadb6986`,
cobre código, testes, manifesto, auditoria do painel e relatório público.

Os outputs ouro e as respostas brutas não entram no Git. O harness é stdlib-only,
não importa SDK de backend nem `hermes_lint`, não executa inferência e recusa
sobrescrever artefatos. Os self-scores provam somente a correção conhecida das
fixtures; não são resultado de spaCy ou de outro candidato.

O próximo WIP pode implementar o adapter experimental spaCy fora do caminho de
produto. Este diretório não seleciona backend, não autoriza PT5 e não abre os
dados selados de `HERMES-PT-PONT-001`.
