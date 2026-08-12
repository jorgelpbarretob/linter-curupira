# ADR-001: identidade normativa e referências

Status: Accepted
Data: 2026-08-12

## Contexto

IDs internos precisam permanecer estáveis, enquanto issue e locator normativos
podem mudar entre edições. O catálogo não pode copiar a norma.

## Decisão proposta

Separar `rule_id` de `SourceReference(standard, issue, locator)`. Reservar
`STE-I9-*` para entradas cuja referência tenha revisão humana aprovada e
`PROJECT-*` para políticas não normativas.

## Consequências

- Atualização de issue exige revisão explícita, não renomeação silenciosa.
- Diagnósticos permanecem rastreáveis sem reproduzir conteúdo protegido.
- Registry e catálogo devem rejeitar IDs duplicados ou fonte divergente.

## Aprovação necessária

Aceito pelo mantenedor do produto e revisor da seleção inicial em 2026-08-12.
