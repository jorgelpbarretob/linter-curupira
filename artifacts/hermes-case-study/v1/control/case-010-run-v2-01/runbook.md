# Runbook — preflight docs

## Objetivo
Garantir que PRs de documentação passem no lint de prosa do time antes de abrir o PR.

## Fluxo

### 1. Instalar
Garantir o ambiente com a toolchain do time.
Se faltar o linter, instalar `curupira`.

### 2. Lint
Em cada PR de documentação, rodar:

```bash
curupira lint docs/**/*.md --enable-rule CURUPIRA-PT-PONT-001
```

Falhar o checklist se exit != 0.

### 3. Corrigir
Quando houver finding:
- ajustar só a prosa (não alterar código)
- repetir o lint até limpar

### 4. Anexar JSON
Salvar a saída JSON no ticket.

### 5. Abrir PR
Abrir PR só depois do lint limpo e do checklist marcado.

## Extras (procedimento operacional)
Se o documento for procedimento operacional, pedir leitura em voz alta por um segundo revisor.

## Restrições
- não commitar segredos
- não rodar semantic-review sem autorização explícita
