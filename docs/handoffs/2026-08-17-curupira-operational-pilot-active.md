# Handoff — Piloto operacional do Curupira ativo

**Próxima sessão:** registrar a primeira tarefa documental real do piloto
**Data:** 2026-08-17
**Status:** aguardando a primeira tarefa real autorizada

## Goal

Medir em uso real se o preflight determinístico do Curupira é executado pelo
Hermes, encontra problemas úteis e bloqueia somente quando necessário. O piloto
deve produzir evidência operacional auditável sem instalar NLP, inferir tokens
ou ajustar regras pelo holdout selado.

## Current state

O release corretivo está no commit
`48b39ec8b9a226bafdc2e8f1c79ea4e5c7c3eb50`, publicado em `origin/main`. O
plugin `curupira-preflight==1.2.0` usa o wrapper `1.1.0` e o pacote
`curupira-lint==0.3.0`. A telemetria agora é persistida pelo próprio plugin em
`~/.hermes/cron/state/curupira-usage/preflight-events.jsonl`, sem depender do
shim de usuário, e falha fechada com `telemetry_write_error` se não puder ser
gravada.

O gateway `hermes-gateway-time.service` está `active/running`, PID `2169273`,
com `NRestarts=0`. Fonte, venv e overlay imutáveis apontam para o commit
`48b39ec8...` e seus três manifests verificam com exit 0. O UAT corretivo cobriu
`passed`, `needs_review`, `blocked` e `not_applicable`, preservou hashes e
removeu corpos dos documentos da telemetria persistente.

O piloto `curupira-pilot-ops-2w-20260817T220937` está ativo de 2026-08-17 a
2026-08-31. Ainda não existe tarefa real registrada. A baseline permanece em
quatro linhas, SHA-256
`e8b78aa0f96f8d2bc6a342a0bc2d9f095c7618d5dd62818ce2d5784a4ac88bab`, e
o offset de medição é a linha 4.

O cron one-shot `53ebfe20ecb1`, nome
`curupira-piloto-ops-2w-encerrar`, está agendado para
`2026-08-31T09:00:00-03:00` com entrega na DM Slack de origem. Ele consolida
as métricas após o offset, preserva o snapshot final e devolve o veredito sem
instalar NLP, testar `analyze` ou alterar configuração e serviço. Não disparar
o job antes da data, pois isso encerraria o piloto antecipadamente.

## Reference artifacts

- Repositório: `https://github.com/jorgelpbarretob/linter-curupira` — fonte pública canônica.
- Commit corretivo: `https://github.com/jorgelpbarretob/linter-curupira/commit/48b39ec8b9a226bafdc2e8f1c79ea4e5c7c3eb50` — telemetria persistente e fail-closed.
- `integrations/hermes-agent/curupira-lint/README.md` — contrato do plugin, gate e JSONL.
- `/home/jorge/Hermes-workspace/artifacts/curupira-uat-telemetry-fix-20260817T220014/report/REPORT.md` — UAT de promoção com veredito PASS.
- `/home/jorge/Hermes-workspace/artifacts/curupira-pilot-ops-2w-current/START.md` — baseline e estado operacional do piloto.
- `/home/jorge/Hermes-workspace/artifacts/curupira-pilot-ops-2w-current/protocol/PROTOCOL.md` — regras, métricas e encerramento.
- `/home/jorge/Hermes-workspace/artifacts/curupira-pilot-ops-2w-current/protocol/CRON-ENCERRAR.json` — custódia do cron one-shot de encerramento.

## Decisions made this session

- Persistir telemetria dentro do plugin → o PATH real do gateway usa o binário congelado e não passa pelo shim `~/.local/bin/curupira`. ADR: não formalizado.
- Bloquear a conclusão quando a evidência não puder ser gravada → um resultado sem trilha auditável não satisfaz o gate. ADR: não formalizado.
- Sanitizar a projeção persistida → mensagens, evidências e excertos podem conter conteúdo do documento. Somente posições, hashes, versões, estados e códigos operacionais entram no JSONL. ADR: não formalizado.
- Manter `analyze` fora do UAT e do piloto → o gate aprovado usa apenas lint determinístico e não deve adquirir a dependência NLP opcional. ADR: não formalizado.
- Rodar o piloto somente com tarefas reais autorizadas → os quatro eventos existentes são seed do UAT e ficam fora das métricas pelo offset de baseline. ADR: não formalizado.
- Agendar o encerramento sem executar agora → o cron one-shot consolida o piloto em 31/08 e evita fechamento manual esquecido ou antecipado. ADR: não formalizado.
- Promover por overlay user-level imutável → o thin sudo não autoriza o instalador root e o overlay já é verificado no `ExecStartPre`. ADR: não formalizado.

## Assumptions to verify

- O protocolo do piloto não prova automação do registro de casos → ao ocorrer uma tarefa real, confirmar que o case JSON, o registry e o agregado diário foram efetivamente atualizados.
- A janela termina em 2026-08-31 com zero ou mais casos → não fabricar tarefas para aumentar a amostra e registrar amostra zero se nenhuma tarefa autorizada ocorrer.
- O PID do gateway pode mudar por operação normal → validar estado, commit, overlay e `NRestarts` em vez de exigir o PID `2169273` em sessões futuras.
- A entrega `origin` do cron continuará apontando para a DM Slack correta → verificar o estado do job `53ebfe20ecb1` se não houver relatório em 31/08, sem executá-lo antecipadamente.

## Failed attempts — do not repeat

- Executar `/home/jorge/bin/install-curupira-hermes-authority.sh` com sudo → o thin sudo de `jorge` não autoriza esse comando como root. Usar o overlay user-level já promovido.
- Medir uso do gateway por `invocations.jsonl` do shim → o gateway chama diretamente o venv congelado. A fonte correta agora é `preflight-events.jsonl` gravado pelo plugin.
- Tratar `analyze` sem NLP como falha do gate → esse comando é opcional e não pertence ao wrapper nem ao hook aprovado.
- Usar `/home/jorge/.local/bin/uv` na construção → o binário existente é
  `/usr/local/bin/uv`. Para o build imutável foi usado `uv --no-config` com
  Python 3.12 fixado.
- Atualizar os manifests congelados para fazer a suíte global passar → as duas divergências com `pyproject.toml` já existiam no `HEAD` e não devem ser misturadas ao piloto nem ao holdout.

## Out of scope

- Instalar NLP ou testar `analyze` durante o piloto.
- Chamar `semantic-review` sem nova autorização e proveniência explícita.
- Alterar configuração, serviço, detector ou regra durante a coleta.
- Inferir tokens ou combinar input, output, cache e revisão numa métrica única.
- Ajustar pelo holdout selado ou criar casos sintéticos para preencher a amostra.

## Next step — WIP=1

**Ação única:** executar o preflight na primeira tarefa real autorizada que
altere `.md`, `.markdown` ou `.txt` e registrar o caso no diretório do piloto.

**Pré-condições:** tarefa real autorizada, caminhos modificados conhecidos,
telemetria live ainda append-only e stack promovida sem drift.

**Definition of done:** evento ou sequência de eventos após a linha 4 associado
à tarefa, case JSON criado em `cases/`, `REGISTRY.json` e agregado diário
atualizados, com estado do gate, diagnósticos, correções, falsos positivos,
duração e retries preservados sem conteúdo documental.
