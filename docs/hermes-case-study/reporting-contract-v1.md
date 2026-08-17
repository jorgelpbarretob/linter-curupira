# Contrato de relatório A/B — 5 dimensões

Status: ativo  
Âncora: estudo Hermes × Curupira  
Modelos Athena de referência:
- executor `qwen3.8-max` (Bailian)
- OSS cloud `qwen/qwen3.8-27b` (OpenRouter)
- fallbacks Athena `kimi-k2.7-code:cloud` e `deepseek-v4-flash:0731-cloud`

## Dimensões obrigatórias

### 1. Sessão do executor

Por braço (control / tratamento):

- `input_tokens`
- `output_tokens`
- `total_tokens`
- `reasoning_tokens` (se existir)
- `cache_read_tokens` (se existir)
- `delta` tratamento − control em input/output/total

Fonte preferida: `hermes -z ... --usage-file` (piloto Athena).  
SessionDB só quando usage-file falhar. Marcar a fonte.

### 2. Painel revisor

- tokens por caso × revisor (in/out/total)
- tokens por revisor (soma do painel)
- total do painel (todos os revisores)

Revisores padrão Athena/cloud:

- `qwen/qwen3.8-27b` (OSS pequeno, sempre cloud)
- `qwen3.8-max` (mesmo provedor Athena)
- opcional: Kimi / Maritaca se o painel expandir

Painel fixado nas baterias v2 (run-v2-01 em diante):

- Kimi `kimi-k2.7` (temp=1, exigência da API coding)
- Maritaca `sabia-4-thinking` (temp=0)

### 3. Gate operacional

Binário por braço de tratamento:

1. invocação efetiva de `curupira lint` (evidência em tool/log)
2. residual zero nas regras do aceite

Não misturar com qualidade.

### 4. Qualidade (cega)

SoT: `docs/hermes-case-study/rubric-v1.md` (aceite) e
`docs/hermes-case-study/semantic-rubric-v2.md` (residual semântico contável).

Camada 1 — aceite (por artefato A/B, sem rótulo de condição):

- clareza 1–5
- classe de aceite (aceito / aceito_retrabalho_menor / rejeitado_retrabalho_maior / bloqueado)
- `critical_errors`
- preferência A vs B + justificativa

Camada 2 — rubrica semântica contável:

- 4 categorias fixas: `ambiguous-reference`, `implicit-agent`, `multiple-actions`, `terminology`
- contagem por categoria e total, severity `major`/`minor`
- achado exige `excerpt` literal verificável; sem trecho, rejeitado
- preferência semântica: braço com menos achados (empate declarado)
- concordância entre revisores (Spearman dos totais)

Unblind só depois dos scores.
Gate PONT-001 e tokens ficam fora desta soma.

### 5. Integridade

Sem exclusão silenciosa.

Marcar explicitamente quando:

- tokens de sessão nulos/zero/assimétricos anômalos
- usage-file ausente
- `total_tokens` muito maior que input+output (cache ou reasoning embutido)
- revisor sem JSON parseável (`reviewer_error` / `semantic_reviewer_error`)
- achado semântico rejeitado por falta de trecho literal verificável (`semantic_invalid_findings_rejected`)
- artefato vazio
- telemetria de fontes mistas no mesmo quadro

Campo: `integrity.flags[]` com código + evidência.  
Anômalo permanece no agregado.

## Política de modelos

- Executor do estudo Athena: **sempre cloud** nos IDs Athena.
- OSS pequeno preferido: `qwen/qwen3.8-27b` via OpenRouter (não local-first).
- Não restaurar skill preload como default.
- CLI-min permanece.

## Artefato canônico

Cada bateria grava:

`artifacts/hermes-case-study/<run>/report-5d.json`

Schema: `hermes-case-study-report-5d/v1`
