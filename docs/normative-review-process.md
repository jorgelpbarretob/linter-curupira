# Processo de revisão normativa

Status: proposta para aprovação humana

## Objetivo

Permitir que uma regra `STE-I9-*` seja rastreável à Issue 9 sem copiar conteúdo
protegido nem transformar memória, site secundário ou saída de modelo em fonte.

## Papéis

- **Autor da regra:** prepara paráfrase curta, classificação, abstenções e
  exemplos sintéticos.
- **Revisor normativo:** pessoa identificada com acesso legítimo à Issue 9 que
  confirma locator, interpretação e limites.
- **Adjudicador do corpus:** humano que decide o ground truth; pode ser a mesma
  pessoa somente quando isso ficar registrado.
- **Revisor de código:** não é o executor da implementação.

## Fluxo de uma candidata

1. Criar uma entrada `planned` sem texto normativo copiado.
2. Registrar `standard`, `issue` e `locator` exatamente como confirmados pelo
   revisor normativo.
3. Escrever uma paráfrase autoral curta e classificar a regra em uma das quatro
   classes públicas.
4. Registrar capacidade de automação, dependências, condições de abstenção,
   controles de falso positivo e oráculo.
5. Preparar exemplos autorais: inicialmente 5 violações, 5 não violações e
   3 edge cases.
6. O revisor registra nome/identificador, data e decisão, sem anexar a norma.
7. Somente uma entrada revisada pode orientar teste e implementação.
8. A regra nasce `preview`; só vira `stable` após o gate de precisão do
   `PLANS.md` e revisão humana do corpus.

## Registro mínimo de revisão

```yaml
normative_review:
  status: pending  # pending | approved | rejected
  reviewer: TBD
  reviewed_on: null
  source_issue: "9"
  source_locator: TBD
  source_fingerprint: null
  notes: null
```

`source_fingerprint` é opcional e identifica a cópia usada sem armazená-la.
Notas não podem reproduzir texto protegido.

## Rejeição e mudança

- Locator não confirmado: a candidata permanece `planned` e não é implementada.
- Interpretação ambígua: classificar como `human-review`, reduzir o detector ou
  registrar abstenção.
- Mudança de issue: não atualizar silenciosamente; abrir decisão e revalidar
  catálogo, corpus e métricas.
- Falso positivo, falso negativo ou crash: adicionar fixture minimizada no mesmo
  change set antes da correção.
