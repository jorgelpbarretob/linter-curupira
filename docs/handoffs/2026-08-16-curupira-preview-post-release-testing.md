# Handoff — Curupira preview após a primeira publicação

**Próxima sessão:** consolidar os testes adicionais em evidência UAT v2
**Data:** 2026-08-16
**Status:** aguardando novas jornadas de teste

## Goal

Evoluir o Curupira como preflight mensurável para documentação técnica pt-BR no
Hermes Agent, usando Sabiázinho como motor semântico opt-in. A próxima decisão
de produto deve partir de comparações A/B reais ou autorizadas, não de ajuste ao
holdout selado nem de alegação sem telemetria.

## Current state

O preview público `v0.3.0-preview.1` está publicado no repositório Curupira no
commit `6e74b3f6bf67f8f1cd4f39fc2c6e0afaac57da76`. A branch `main` está limpa e
sincronizada. O pacote publica somente o executável `curupira`; mantém
`hermes_lint` apenas como compatibilidade Python 0.3.x e não conflita com o
executável do Hermes Agent.

O piloto sintético inicial observou findings residuais `1 → 0`, com chamadas de
ferramenta `9 → 10` e mensagens `11 → 12`. A diferença de duração `41 s → 40 s`
é ruído. Tokens não foram expostos pela superfície interativa e não foram
estimados. O painel final Maritaca/Grok/Kimi aprovou por unanimidade com zero
findings.

Validação da release: 447 testes passaram; quatro skips pertencem à linha NLP
histórica. Ruff, formatação, mypy, dependências, freeze, skill, wheel e sdist
ficaram verdes. Um smoke Sabiázinho posterior ao endurecimento do prompt usou
texto sintético, retornou o modelo fixado, 263 tokens e duas observações
ancoradas. A análise spaCy direta retornou 2 sentenças e 15 palavras.

## Reference artifacts (NÃO duplicar — apontar)

- Repositório: `https://github.com/jorgelpbarretob/linter-curupira` — origem pública atual.
- Release: `https://github.com/jorgelpbarretob/linter-curupira/releases/tag/v0.3.0-preview.1` — wheel e sdist publicados.
- `docs/curupira-hermes-agent-pilot-v1.md` — desenho, métricas e limitações do piloto.
- `artifacts/curupira/hermes-agent-pilot-v1/summary.json` — resultado agregado canônico.
- `docs/curupira-preview-panel-review-v1.md` — auditoria do painel de três modelos.
- `integrations/hermes-agent/curupira-preflight/SKILL.md` — fluxo válido no Hermes Agent.
- `tools/curupira/hermes_agent_ab.py` — comparador para rodadas com telemetria real.
- `docs/adr/0021-curupira-identity-migration.md` — contrato de identidade e compatibilidade.

## Decisions made this session

- Curupira substitui Hermes como identidade ativa → evita conflito com o Hermes Agent e cria posicionamento brasileiro. ADR: `docs/adr/0021-curupira-identity-migration.md`.
- Hermes Agent é a primeira integração → já existe uma jornada executável por slash command e um A/B reproduzível.
- Sabiázinho é semântico e opt-in → o documento só sai da máquina por comando explícito; observações ancoradas não viram regra normativa.
- O preview foi publicado antes de perfeição → evolução ocorrerá por issues, PRs e jornadas autorizadas, com claims limitados aos dados observados.
- Não há gate de revisão humana → validação operacional usa testes, painel Maritaca/Grok/Kimi e UAT automatizado.

## Assumptions (verificar antes de seguir)

- Novos exemplos serão sintéticos, públicos ou explicitamente autorizados → verificar proveniência antes de persistir qualquer entrada ou saída.
- A superfície interativa do Hermes Agent 0.20.1 pode continuar sem telemetria de tokens → verificar a versão e a existência de `--usage-file` ou métrica equivalente antes de registrar comparação.
- Não há runner Himavai configurado neste host → verificar CLI, endpoint ou contrato fornecido antes de atribuir a Himavai qualquer UAT.
- A chave Maritaca continua disponível apenas em `/home/jorge/.config/hermes/maritaca.env` → carregar por `source` sem copiar valor para logs, artefatos ou repositório.

## Failed attempts (NÃO repetir)

- `hermes --oneshot --skills curupira-preflight` → o build 0.20.1 não aplicou a skill.
- `hermes chat -s curupira-preflight` → carregou contexto, mas não impôs o gate de lint; usar a invocação interativa `/curupira-preflight`.
- Inferir tokens por bytes ou mensagens → não é uma métrica defensável; deixar `not-measured` quando o provedor não expuser uso.
- Executar o projeto com `uv` 0.12.0 → o `pyproject.toml` exige exatamente 0.11.14; usar a versão fixada ou instalar essa versão.
- Consumir JSON cru do Kimi sem tolerar cerca Markdown exata → a primeira rodada retornou JSON válido dentro de ```json; o runner externo final remove somente esse invólucro exato e continua rejeitando texto adicional.

## Out of scope (usuário rejeitou)

- Revisão humana como condição de lançamento.
- Ajustar detector usando os 4 FP ou 15 FN do holdout histórico selado.
- Alegar redução de tokens, velocidade ou qualidade geral a partir de uma única tarefa sintética.
- Criar PR para a publicação inicial; o fluxo autorizado foi commit direto em `main`.

## Next step (WIP=1)

**Ação única:** registrar o primeiro lote de jornadas adicionais como UAT v2 A/B do Hermes Agent.
**Pré-condições:** entradas com proveniência autorizada; mesma tarefa, modelo e configuração nos dois braços; skill ativada apenas no tratamento; versão do agente registrada.
**Definition of done:** pares baseline/tratamento preservados por hash, findings residuais e custo operacional medidos, tokens registrados somente quando informados pelo provedor, relatório agregado criado sem ajustar o detector durante a coleta.

## Suggested skills

- `quantitative-review` — auditar deltas e impedir que uma amostra pequena sustente claims maiores que os dados.
- `tdd` — transformar findings reproduzíveis das jornadas em testes antes de alterar regras ou adapters.
