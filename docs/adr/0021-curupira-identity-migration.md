# ADR-021: migração de identidade Hermes para Curupira

Status: Accepted
Date: 2026-08-16

## Contexto

O mantenedor decidiu renomear o produto Hermes para Curupira antes de abrir a
distribuição ao público. A mudança alcança marca, pacote Python, comando,
namespace de código, IDs de regra e schemas novos. Evidência histórica contém
paths e hashes com o nome Hermes e não pode ser reescrita.

## Decisão

A identidade ativa passa a ser:

- produto: **Curupira**;
- repositório: `jorgelpbarretob/linter-curupira`;
- distribuição: `curupira-lint`;
- pacote Python: `curupira_lint`;
- CLI: `curupira`;
- regras: `CURUPIRA-PT-*`;
- schemas novos: prefixo `curupira-`.

`CURUPIRA-PT-PONT-001` preserva exatamente a semântica e o detector de
`HERMES-PT-PONT-001`. A avaliação Hermes é registrada como linhagem histórica,
não como novo holdout Curupira: o status continua `preview`, os 4 FP e 15 FN
permanecem selados e não orientam ajuste.

## Compatibilidade

A distribuição 0.3.x inclui temporariamente o pacote Python `hermes_lint` com o
comportamento 0.2.0, mas não publica uma CLI `hermes`. Esse nome pertence ao
Hermes Agent da Nous Research, integração inicial do Curupira; criar o alias
sombrearia o executável do agente. Configurações Curupira que mencionem um ID
Hermes falham com a substituição exata, sem migração silenciosa. A remoção do
pacote Python legado exige outra decisão incompatível e não ocorre antes de
0.4.0.

Baselines incluem `rule_id` no fingerprint. Uma baseline Hermes não suprime
diagnósticos Curupira. O usuário deve gerar uma nova baseline ao migrar para
`curupira`; a prerelease histórica Hermes continua disponível no repositório
anterior para reprodução.

Releases, tags, corpus, artefatos, ADRs, ferramentas e relatórios Hermes ficam
imutáveis. Em particular, não se renomeiam `corpus/hermes`, `artifacts/hermes`,
`tools/hermes` nem documentos que participem de hashes publicados.

## Consequências

- integrações novas usam somente Curupira;
- links históricos continuam citando Hermes quando essa é a identidade real da
  evidência;
- o wheel contém dois namespaces durante a janela de transição;
- o rebrand não promove regra, não muda threshold e não corrige o holdout;
- a prerelease Hermes 0.2.0 permanece histórica e uma prerelease Curupira 0.3.0
  inaugura a distribuição no novo repositório.

## Aprovação

Aceito explicitamente pelo mantenedor em 2026-08-16: “vamos mudar de Hermes
para Curupira”, seguido da definição do repositório
`https://github.com/jorgelpbarretob/linter-curupira`.
