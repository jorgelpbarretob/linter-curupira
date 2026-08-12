# ADR-007: namespace e estabilidade dos IDs de regra

Status: Accepted
Data: 2026-08-12

## Contexto

IDs aparecem em configuração, diagnósticos, JSON e futuras baselines. Alterar o
significado de um ID publicado faria supressões e integrações apontarem para a
regra errada. A Issue normativa já fica separada em `SourceReference`.

## Decisão proposta

Usar dois namespaces públicos:

- `STE-I9-<FAMILY>-NNN` para uma obrigação da Issue 9 com locator e revisão
  normativa aprovados;
- `PROJECT-<FAMILY>-NNN` para política local explicitamente não normativa.

Os componentes usam ASCII maiúsculo, dígitos e hífen; `NNN` tem três dígitos.
Depois que um ID entrar em release ou saída pública, seu significado não muda e
o ID não é reutilizado. Mudança material de detector ou fonte recebe novo ID; o
antigo pode ser descontinuado, mas continua reservado.

O startup valida namespace, unicidade e coerência da fonte: `STE-I9-*` exige
`standard="ASD-STE100"`, `issue="9"` e locator aprovado; `PROJECT-*` exige
`standard="PROJECT"`. Entradas `planned` podem continuar sem implementação,
mas não entram no registry executável.

## Alternativas rejeitadas

- embutir locator ou número completo da norma no ID, porque a fonte já tem campo
  próprio e pode mudar entre issues;
- usar IDs livres, porque erros de digitação virariam configuração silenciosa;
- renumerar IDs após remoções, porque quebraria consumidores.

## Consequências

- as cinco candidatas só recebem ID definitivo durante o incremento de cada
  regra, depois da revisão normativa já registrada;
- catálogo divergente ou ID desconhecido falha de forma operacional;
- futura Issue 10 usa outro namespace, sem redefinir IDs da Issue 9.

## Aprovação necessária

Aceito explicitamente pelo mantenedor em 2026-08-12, antes de congelar IDs no
catálogo ou expô-los em configuração e JSON.
