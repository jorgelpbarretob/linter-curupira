# Artefatos auditáveis do Hermes

Este diretório contém manifests, locks e provas textuais pequenas que precisam
permanecer versionadas. Wheels, modelos, ambientes virtuais, respostas externas
e outros binários ficam sob custódia separada e são referenciados somente por
hash.

`pt4-gate0/` registra a elegibilidade dos candidatos de análise linguística
local antes do bake-off. Esses arquivos não selecionam backend, não entram no
wheel base do projeto e não autorizam PT5.

`pt4-corpora/` registra provas pequenas do incremento de corpora e ambiente. Os
corpora em si ficam em `corpus/hermes/pt4/`; propostas novas só se tornam
canônicas após validação mecânica e unanimidade do painel do ADR-020.
