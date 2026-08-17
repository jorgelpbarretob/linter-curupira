# Runbook — preflight de docs

## Objetivo
Garantir que PRs de documentação passem no lint PT antes do merge.

## Fluxo

### 1. Instalar
Confirme a toolchain do time. Se faltar o CLI:

```bash
# instale curupira conforme o padrão do repositório/time
```

### 2. Lint
Em cada PR de documentação:

```bash
curupira lint docs/**/*.md --enable-rule CURUPIRA-PT-PONT-001
```

Checklist falha se `exit != 0`.

### 3. Corrigir
Se houver finding:
- Ajuste só a prosa (não altere código).
- Rode o lint de novo até limpar.

### 4. Anexar JSON
Salve a saída JSON no ticket.

### 5. Abrir PR
Abra o PR só com lint limpo e checklist marcado.

## Extras
- Procedimento operacional: peça leitura em voz alta a um segundo revisor.
- Não commite segredos.
- Não rode semantic-review sem autorização explícita.
