# PT2 — protocolo de revisão delegada ao Grok para PONT-001

Status: Accepted
Date: 2026-08-14

## Autorização e emenda operacional

O mantenedor autorizou explicitamente o uso do Grok como revisor externo do
primeiro holdout de `HERMES-PT-PONT-001` e solicitou receber somente aprovações
críticas. Esta decisão emenda, para esta tranche, a exigência operacional de
confirmação humana linha a linha do ADR-018 sem transformar o modelo em fonte
normativa ou executor do produto.

Depois de aprovar os bytes do ground truth e autorizar a primeira execução, o
mantenedor ampliou a delegação: o Grok passou a aprovar em seu nome os gates
operacionais rotineiros, sem novas interrupções. Os limites dessa delegação
estão em `docs/hermes-governance.md`.

O Grok propõe `truth`, região, domínio, expectativa e racional para todas as
409 unidades. O mantenedor continua autoridade para:

- casos `ambiguous`;
- confiança `medium` ou `low`;
- contexto insuficiente, markup malformado, região mista ou lacuna de protocolo;
- falha de schema, bijeção, proveniência, licença ou integridade;
- aprovação final dos bytes e do SHA-256 antes do congelamento.

Labels `high` sem sinal crítico podem ser aceitas por delegação registrada. A
decisão não autoriza executar detector, implementar regra, ajustar threshold ou
usar casos do holdout como fixture, prompt de produto ou exemplo de TDD.

## Egress e isolamento

O opt-in desta execução cobre somente o conteúdo público CC BY 4.0 do snapshot
Kubernetes já aceito. O runner:

- usa o modelo solicitado `grok-4.6`;
- envia somente contexto necessário e metadados do manifesto;
- executa uma conversa nova por lote, sem memória, ferramentas, web ou agentes;
- não concede acesso ao repositório nem ao detector;
- mantém prompts, wrappers de resposta e propostas sob
  `/home/jorge/.hermes/holdout-custody/`, fora do Git;
- registra modelo solicitado/retornado, hashes, request/session IDs, uso e custo
  quando fornecidos pelo Grok CLI;
- não grava texto-fonte no manifesto público ou em arquivos de label no Git.

## Contrato de saída

Cada `case_id` recebe exatamente uma proposta conforme
`tools/hermes/pont_001_grok_review_schema.json`:

- `truth`: `violation`, `non_violation`, `out_of_scope` ou `ambiguous`;
- `structural_region`: região fechada definida pelo schema;
- `expected_diagnostics`: `1`, `0` ou `null`, coerente com `truth`;
- `domain`: domínio técnico fechado com fallback `other`;
- `rationale`: justificativa curta em pt-BR baseada somente no contexto;
- `confidence`: `high`, `medium` ou `low`;
- `requires_human`: verdadeiro para toda decisão crítica;
- `critical_reason`: motivo fechado e coerente com `requires_human`.

Controles sem ponto e vírgula devem receber `non_violation`, região
`document_control`, expectativa `0` e confiança alta, salvo problema explícito
de integridade ou proveniência.

## Prompt cego

O prompt repete o guia aceito e proíbe:

- consultar, inferir ou executar qualquer detector;
- pesquisar a implementação ou comparar com labels anteriores;
- julgar qualidade geral do texto;
- converter incerteza em negativo;
- omitir ou duplicar `case_id`;
- usar informação externa ao lote.

O alvo de cada ocorrência é identificado por caminho, hash, linha, coluna,
offset Unicode, offset UTF-8 e janela de contexto. Se a janela não sustentar a
classificação estrutural, a resposta deve ser `ambiguous`, confiança baixa e
`requires_human=true`.

## Gates

1. autenticação e disponibilidade do Grok;
2. congelamento de prompt, schema, modelo e manifesto de entrada;
3. revisão em lotes e validação estrita de todas as respostas;
4. adjudicação humana somente da fila crítica;
5. consolidação, bytes canônicos e SHA-256;
6. aprovação humana final do congelamento;
7. detector implementado e congelado em TDD;
8. autorização separada para primeira execução.

## Resultado

Os gates 1–6 foram concluídos em 2026-08-14. O Grok retornou 409/409 unidades
com schema válido e nenhuma fila crítica. O ground truth candidato foi
reproduzido byte a byte, aprovado explicitamente pelo mantenedor e congelado sob
custódia externa com SHA-256
`6cab9e0a4090df19fc5c3cc5a8e93122413160f523e032367ec25849567abab6`.

Os gates 7–8 também foram concluídos em 2026-08-14. Depois da execução cega, o
Grok aprovou a abertura dos labels e tomou a decisão pós-holdout delegada. O
estado resultante foi `preview`; métricas e hashes estão em
`docs/hermes-pont-001-holdout-evaluation-v1.md`.

## Referências operacionais

- <https://docs.x.ai/developers/model-capabilities/text/structured-outputs>
- <https://docs.x.ai/developers/models/grok-4.5>
- listagem local do Grok CLI em 2026-08-14, que registrou `grok-4.6` como modelo
  padrão disponível.
