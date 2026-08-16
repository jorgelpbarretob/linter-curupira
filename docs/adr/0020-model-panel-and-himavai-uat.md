# ADR-020: painel de modelos e UAT da Himavai

Status: Accepted
Date: 2026-08-16

## Contexto

O fluxo Hermes ainda dependia de revisão, adjudicação e promoção humanas. O
mantenedor decidiu que nenhum humano fará revisão de corpus ou adjudicação de
regra neste projeto. Em seu lugar, as decisões de desenvolvimento usam
Maritaca, Grok e Kimi 2.7, com rastreabilidade por prompt, schema, entrada,
resposta e modelo retornado. A Himavai fará testes de usuário, sem assumir o
papel de oráculo linguístico ou curadora de corpus.

Esta decisão substitui os gates humanos prospectivos do ADR-016, ADR-018, da
governança e do roadmap. Registros históricos de decisões já tomadas não são
reescritos.

## Decisão

### Painel obrigatório

Todo novo corpus, regra ou promoção que antes exigiria revisão humana usa três
votos isolados:

1. **Maritaca:** `sabia-4-thinking`, especialista principal em pt-BR;
2. **Grok:** `grok-4.6`, auditor adversarial e operacional;
3. **Kimi:** `kimi-k2.7-code:cloud`, revisão independente de consistência.

Os três recebem a mesma versão canônica da entrada, sem saída do detector ou do
backend avaliado. Um modelo não recebe a resposta dos outros antes de emitir o
primeiro voto. Ferramentas, memória, web e subagentes ficam desabilitados quando
o cliente permitir.

### Gate de aceite

- todos os três outputs devem validar contra o schema e cobrir 100% dos casos,
  uma vez, na ordem canônica;
- cada caso precisa de três votos `approve` depois de eventuais ciclos de
  correção; maioria simples não congela ground truth;
- `change_required`, `reject`, schema inválido, modelo ausente ou credencial
  ausente mantém o artefato em `rework`;
- alegação puramente mecânica sobre slice, offset, ordem, sobreposição, hash ou
  contagem é verificada por código determinístico. Quando contradita, o modelo
  recebe a prova e deve emitir novo voto; o executor não converte o voto por
  conta própria;
- mudança proposta por modelo só entra numa nova versão do artefato, com novos
  hashes e novo ciclo de três votos;
- licença, segredo e autorização de egress continuam gates determinísticos e
  não podem ser resolvidos por opinião de modelo.

Nenhum modelo cria ground truth sozinho. Ground truth nasce apenas do artefato
canônico que passou validação mecânica e obteve unanimidade do painel.

### Papéis Maritaca

O `sabiazinho-4` continua reservado ao motor semântico opt-in do produto. O
`sabia-4-thinking` representa a Maritaca no painel e não compartilha prompt ou
schema com o motor semântico. A chamada usa a Responses API, registra o alias
solicitado e o modelo retornado e exige `MARITACA_API_KEY` fora do Git.

Credencial ausente não autoriza fallback silencioso nem voto sintético. O gate
fica `rework-missing-provider` até uma chamada real ser validada.

### Testes de usuário

A Himavai executa UAT sobre builds utilizáveis, cenários e documentação do
produto. O pacote de UAT registra tarefas, versão, ambiente, sucesso da tarefa,
tempo, severidade do problema, comentário e consentimento de coleta. O UAT
mede utilidade, clareza, ruído, confiança e ergonomia; não rotula corpus, não
define semântica normativa e não substitui testes automatizados.

PT4 prepara o contrato e os artefatos de UAT, mas a primeira execução da
Himavai ocorre somente quando existir uma jornada de usuário executável após
PT5. Resultados de UAT podem abrir issues e `rework`, nunca editar silenciosamente
ground truth ou holdout consumido.

## Evidência e reprodutibilidade

Cada voto registra:

- papel, provider, alias solicitado e identificador retornado;
- SHA-256 de proposta, prompt e schema;
- response/session ID, data, latência e tokens quando disponíveis;
- status do schema, bijeção dos casos e fronteiras de segurança;
- SHA-256 da resposta bruta mantida sob custódia externa.

CI permanece offline. Testes públicos exercitam validação e agregação com
fixtures sintéticas; chamadas reais nunca são requisito de CI.

## Consequências

- nenhum novo gate fica esperando revisão humana;
- o custo e a disponibilidade de três providers passam a fazer parte do gate;
- unanimidade reduz o risco de um único modelo, mas não demonstra independência
  estatística nem elimina erro correlacionado;
- indisponibilidade da Maritaca bloqueia o congelamento, porém não impede
  preparação, validação mecânica ou votos isolados de Grok e Kimi;
- a classe histórica `human-review` fica depreciada para novas regras e será
  removida em incremento próprio, sem quebrar contratos retrospectivamente;
- Himavai passa a ser a fonte explícita de evidência de uso, separada da
  adjudicação linguística.

## Fontes verificadas

- Modelos Maritaca: https://docs.maritaca.ai/pt/modelos
- Responses API: https://docs.maritaca.ai/pt/responses-api
- Compatibilidade OpenAI: https://docs.maritaca.ai/pt/api/openai-compatibilidade

Verificado em 2026-08-16.

## Aprovação

Aceito explicitamente pelo mantenedor em 2026-08-16: usar Maritaca, Grok e Kimi
2.7 para validação, remover revisão humana do plano e reservar testes de usuário
à Himavai.
