# Runbook — preflight docs

## Objetivo
Garantir ambiente e lint de documentação antes de abrir PR.

## Fluxo

### 1. Instalar
Garantir a toolchain do time.
Se faltar o binário, instalar `curupira`.

### 2. Lint
Em cada PR de documentação, rodar:

```bash
curupira lint docs/**/*.md --enable-rule CURUPIRA-PT-PONT-001
```

Falhar o checklist se exit for diferente de 0.

### 3. Corrigir
Se houver finding, ajustar só a prosa.
Não alterar código.
Repetir o lint até limpar.

### 4. Anexar JSON
Salvar a saída JSON no ticket.

### 5. Abrir PR
Abrir PR só depois do lint limpo e do checklist marcado.

## Regras extras
- Se o documento for procedimento operacional, pedir leitura em voz alta por um segundo revisor.
- Não commitar segredos.
- Não rodar semantic-review sem autorização explícita.
