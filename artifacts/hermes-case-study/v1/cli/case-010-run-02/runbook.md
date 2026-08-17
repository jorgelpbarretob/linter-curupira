# Runbook — preflight docs

## Objetivo

Garantir ambiente e lint limpo antes de abrir PR de documentação.

## Fluxo

### 1. Instalar

Garanta a toolchain do time.
Se faltar o binário, instale `curupira`.

### 2. Lint

Em cada PR de documentação, rode:

```bash
curupira lint docs/**/*.md --enable-rule CURUPIRA-PT-PONT-001
```

Se o exit for diferente de 0, o checklist falha.

### 3. Corrigir

Quando houver finding, ajuste só a prosa.
Não altere código.
Repita o lint até limpar.

### 4. Anexar JSON

Salve a saída JSON no ticket.

### 5. Segundo revisor (se aplicável)

Se o documento for procedimento operacional, peça leitura em voz alta a um segundo revisor.

### 6. Abrir PR

Abra o PR só depois do lint limpo e do checklist marcado.

## Restrições

- Não commite segredos.
- Não rode semantic-review sem autorização explícita.
