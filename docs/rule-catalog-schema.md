# Schema preliminar do catálogo de regras

Status: proposta, schema `0.1-draft`

O catálogo é inventário e metadado; não é uma DSL de implementação e não copia
a norma. Uma entrada `STE-I9-*` só pode orientar código após revisão normativa.

## Entrada proposta

```yaml
rule_id: STE-I9-TBD-001
title: Project-authored short title
source:
  standard: ASD-STE100
  issue: "9"
  locator: TBD
kind: deterministic  # deterministic | nlp | semantic | human-review
detector_basis: pure # pure | pos-dependent | parser-dependent | model-dependent | none
default_severity: warning
automation: partial  # full | partial | none
status: planned      # planned | preview | stable
summary: Project-authored short paraphrase
requires: []
abstain_when: []
false_positive_controls: []
oracle: human-labeled-corpus
quality_gate:
  minimum_precision: 0.95
  maximum_false_positives_per_1000_words: 1.0
tests:
  violation_minimum: 5
  non_violation_minimum: 5
  edge_minimum: 3
  metamorphic: []
autofix: none        # none | safe | suggested
normative_review:
  status: pending
  reviewer: TBD
  reviewed_on: null
```

## Invariantes

- `rule_id` é único.
- `STE-I9-*` exige `source.issue: "9"`, locator não-TBD e revisão aprovada.
- `PROJECT-*` é não normativo e não pode alegar fonte ASD.
- `kind` contém exatamente uma das quatro classes públicas.
- `detector_basis` descreve capacidade interna e não cria uma quinta classe.
- `human-review` usa `automation: none` e não executa detector.
- `semantic` não usa severidade `error`.
- `stable` exige revisão normativa aprovada e evidência do quality gate.
- Exemplos não armazenam texto copiado da norma.

## Questões antes de congelar o schema

- Formato definitivo e validação: YAML mais JSON Schema, ou outro mecanismo.
- Identidade do schema e política de compatibilidade.
- Forma de registrar intervalos de confiança e tamanho da amostra.
- Vocabulário de `requires` e relações metamórficas.
- Separação física entre catálogo normativo e regras `PROJECT-*`.
