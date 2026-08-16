# PT4 corpora — evidência pré-inferência

Status: Model panel approved; canonical offset corpus frozen
Date: 2026-08-16

`pt4-corpora-public-v1.sha256` preserva o snapshot anterior do split PetroGold,
sua licença, os manifests do corpus e do ambiente, a proposta autoral v1 e a
prova de `pip check`. `contamination-audit-v2.json` repete a prova de zero
sobreposição para a proposta corrigida v2.

`pt4-corpora-public-v2.sha256`, SHA-256
`58b099bf2b4b52642c2915904d3aa911662b7041e3e2dacf39c647c2b24a97eb`,
cobre a proposta v2, o corpus canônico, a nova auditoria e o painel final.

A proposta v2 passou validação mecânica e unanimidade de Maritaca, Grok e Kimi
2.7. O corpus aceito está em
`corpus/hermes/pt4/pt4-offset-development-v1.jsonl`, SHA-256
`45716b0581ae7c90897a3d088953ac8efde13882e6c4ef7ecfa87c6764928f5d`.

`kimi-k2.7-supplementary-review-v1.json` preserva a revisão histórica que abriu
sete correções da proposta v2. `model-panel-review-v2.json` registra os três
votos finais, o revoto Kimi baseado em prova determinística, hashes das
respostas brutas externas e o congelamento unânime.

O corpus autoriza implementar e validar o harness PT4. Inferência, escolha de
backend e PT5 continuam sujeitos às etapas pré-registradas do bake-off.
