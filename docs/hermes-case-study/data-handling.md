# Data handling — estudo Hermes × Curupira v1

## Permitido no pacote público

- tarefas semissintéticas
- logs sanitizados
- hashes e métricas agregadas
- artefatos sem segredo

## Exige autorização explícita (`explicit_ok`)

- tarefa real anonimizada
- trecho derivado de operação

## Proibido no estudo / no semantic-review

- documento industrial confidencial sem base
- holdout selado do Curupira como material de treino/ajuste
- chaves, tokens, PII

## Proveniência por caso

Campo `manifest.json → provenance`:

- `synthetic`
- `public`
- `explicit_ok`
- `internal_redacted` (só métricas lint locais, sem publicar texto)

## Retenção

- Artefatos de rodada em `artifacts/hermes-case-study/v1/`
- Casos improve do funil mesa em `~/.hermes/cron/state/curupira-usage/improve/` (operacional, não substitui o estudo)
