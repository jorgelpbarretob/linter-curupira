# Governança da especificação e das regras Hermes

Status: Accepted
Date: 2026-08-13
License: `CC-BY-4.0`

## Autoridades

1. **Mantenedor:** aceita versão, licença, roadmap e mudança de contrato.
2. **Revisor linguístico pt-BR:** avalia formulação, variedade brasileira,
   ambiguidade e exemplos.
3. **Revisor de domínio:** verifica se a regra preserva segurança e intenção
   técnica nos domínios afetados.
4. **Curador de corpus:** valida proveniência, licença, separação de conjuntos e
   congelamento.
5. **Revisor de privacidade/segurança:** aprova egress, redaction e classes de
   documento permitidas.

No bootstrap, uma pessoa pode acumular papéis, mas cada decisão registra qual
papel foi exercido. Promoção de regra exige pelo menos uma revisão humana além
do autor do detector.

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
- `stable`: gates por regra cumpridos e decisão humana explícita;
- `rework`/`rejected`: falha ou inadequação registrada sem apagar evidência.

## Proposta de regra

Toda proposta contém:

- ID provisório `HERMES-PT-*`;
- texto autoral com `DEVE`, `NÃO DEVE`, `RECOMENDA-SE` ou `PODE`;
- problema observado e domínios afetados;
- classe `deterministic`, `nlp`, `semantic` ou `human-review`;
- unidade detectável e locator na especificação;
- exemplos positivos, negativos e edge;
- condições de abstenção e controles de falso positivo;
- dependências, licenças e dados necessários;
- plano de corpus e métricas pré-registradas;
- risco de segurança, privacidade e mudança de significado.

## Processo de decisão

1. discussão pública da proposta;
2. revisão linguística, técnica e de licença;
3. aprovação do texto antes do detector;
4. labels humanas congeladas antes da primeira execução;
5. TDD WIP=1;
6. avaliação separada por regra;
7. relatório de erros e adjudicação;
8. decisão humana de estado;
9. changelog da especificação e do catálogo.

Alteração de threshold, unidade de contagem, condições de abstenção, severity ou
semântica do ID exige nova versão e reavaliação. Um ID não muda de significado
silenciosamente.

## Papel dos modelos

- `sabiazinho-4` executa somente regras `semantic` aprovadas e pode abster-se;
- `sabia-4-thinking` faz julgamento cego e crítica em avaliação;
- nenhum modelo cria ground truth sozinho;
- modelo não aceita PR, promove regra, resolve disputa de licença nem substitui
  revisão técnica;
- divergência modelo-humano entra na fila de adjudicação;
- prompts, schemas e versões são artefatos revisáveis e versionados.

## Versionamento

A especificação usa `MAJOR.MINOR.PATCH`:

- `MAJOR`: remove regra estável ou muda seu significado incompatibilmente;
- `MINOR`: adiciona regra ou capacidade compatível;
- `PATCH`: esclarece texto sem mudar decisão observável.

Enquanto a versão for `0.x`, qualquer regra pode mudar, mas mudanças observáveis
continuam exigindo changelog, novo corpus aplicável e decisão explícita.

## Conflitos e recursos

O mantenedor decide empates depois de registrar as posições linguística,
técnica, empírica e de risco. Evidência de segurança ou mudança de significado
tem precedência sobre preferência estilística. Decisões podem ser reabertas com
novo corpus, novo domínio ou falha reproduzível.

## Aprovação

Aceita explicitamente pelo mantenedor em 2026-08-13.
