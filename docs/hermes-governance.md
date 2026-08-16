# Governança da especificação e das regras Hermes

Status: Accepted
Date: 2026-08-13
License: `CC-BY-4.0`

## Autoridades

1. **Mantenedor:** aceita versão, roadmap, mudança de contrato e a própria
   governança.
2. **Validação determinística:** decide integridade, offsets, hashes, contagens,
   licença documentada e separação de conjuntos.
3. **Painel linguístico/técnico:** `sabia-4-thinking`, `grok-4.6` e
   `kimi-k2.7-code:cloud` votam isoladamente; novos artefatos exigem unanimidade.
4. **Himavai:** conduz UAT de builds utilizáveis e registra evidência de
   experiência, sem rotular corpus.

Não há gate de revisão humana. Nenhum modelo cria ground truth sozinho e voto
de modelo não resolve licença, segredo ou autorização de egress.

## Estados de uma proposta

```text
idea -> specified -> labeled -> implemented -> evaluated
                                           |-> rework
                                           |-> rejected
                                           `-> preview -> stable
```

- `idea`: problema e público afetado descritos;
- `specified`: enunciado, racional, exemplos, escopo e abstenção publicados;
- `labeled`: corpus aplicável congelado antes da execução;
- `implemented`: TDD e contratos locais verdes;
- `evaluated`: métricas e matriz de erros publicadas;
- `preview`: útil, mas sem evidência suficiente para estabilidade;
- `stable`: gates por regra cumpridos e unanimidade válida do painel;
- `rework`/`rejected`: falha ou inadequação registrada sem apagar evidência.

## Proposta de regra

Toda proposta contém:

- ID provisório `HERMES-PT-*`;
- texto autoral com `DEVE`, `NÃO DEVE`, `RECOMENDA-SE` ou `PODE`;
- problema observado e domínios afetados;
- classe `deterministic`, `nlp` ou `semantic`; `human-review` é histórica;
- unidade detectável e locator na especificação;
- exemplos positivos, negativos e edge;
- condições de abstenção e controles de falso positivo;
- dependências, licenças e dados necessários;
- plano de corpus e métricas pré-registradas;
- risco de segurança, privacidade e mudança de significado.

## Processo de decisão

1. discussão pública da proposta;
2. validação determinística de estrutura, licença e proveniência;
3. três votos cegos e isolados sobre texto/labels antes do detector;
4. unanimidade e congelamento dos hashes;
5. TDD WIP=1;
6. avaliação separada por regra;
7. relatório de erros, rework e novo painel quando necessário;
8. decisão de estado pelos gates pré-registrados;
9. UAT Himavai quando houver jornada executável;
10. changelog da especificação e do catálogo.

### Delegação operacional ao Grok

Em 2026-08-14, o mantenedor concedeu ao Grok delegação permanente e restrita
para aprovar, em seu nome, gates operacionais rotineiros do fluxo Hermes. O
agente executor deve prosseguir sem interromper o mantenedor quando o parecer
estruturado do Grok for favorável e quando entrada, prompt, schema, resposta e
artefatos de saída estiverem identificados por hashes e metadados auditáveis.

A delegação cobre abertura sequencial de artefatos congelados, validação de
isolamento, passagem entre etapas pré-registradas e decisão de estado baseada
nos gates já aceitos. Depois do ADR-020, Grok também é um dos três votos
obrigatórios, mas não decide sozinho. Ele não pode:

- resolver licença, segredo, privacidade ou novo tipo de egress;
- ampliar orçamento externo não aprovado;
- executar ação irreversível ou publicar/commitar em nome do mantenedor;
- mudar regra normativa, threshold, unidade de contagem ou gates;
- criar ground truth sozinho ou encerrar divergência técnica substancial.

Uma promoção a `stable` só é válida se todos os gates pré-registrados passarem,
os três votos forem válidos e unânimes e o registro citar os hashes do painel.
Falha de gate mantém a regra em `preview`, `rework` ou `rejected` sem solicitar
revisão humana.

Alteração de threshold, unidade de contagem, condições de abstenção, severity ou
semântica do ID exige nova versão e reavaliação. Um ID não muda de significado
silenciosamente.

## Papel dos modelos

- `sabiazinho-4` executa somente regras `semantic` aprovadas e pode abster-se;
- `sabia-4-thinking`, `grok-4.6` e `kimi-k2.7-code:cloud` fazem votos cegos e
  isolados;
- nenhum modelo cria ground truth sozinho;
- modelo não aceita PR nem resolve disputa de licença;
- qualquer divergência entre modelos entra em rework e novo ciclo completo;
- prompts, schemas e versões são artefatos revisáveis e versionados.

## Versionamento

A especificação usa `MAJOR.MINOR.PATCH`:

- `MAJOR`: remove regra estável ou muda seu significado incompatibilmente;
- `MINOR`: adiciona regra ou capacidade compatível;
- `PATCH`: esclarece texto sem mudar decisão observável.

Enquanto a versão for `0.x`, qualquer regra pode mudar, mas mudanças observáveis
continuam exigindo changelog, novo corpus aplicável e decisão explícita.

## Conflitos e recursos

Não há desempate por maioria: ausência de unanimidade causa rework. Evidência
determinística de segurança ou mudança de significado tem precedência sobre
preferência do painel. Decisões podem ser reabertas com novo corpus, novo
domínio, UAT Himavai ou falha reproduzível.

## Aprovação

Aceita explicitamente pelo mantenedor em 2026-08-13.
