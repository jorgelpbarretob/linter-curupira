# ADR-002: offsets, Unicode e newlines

Status: Accepted
Data: 2026-08-12

## Contexto

Offsets são parte do contrato público e afetam parser, JSON, baseline e fixer.
Uma escolha inconsistente produz diagnósticos que apontam para texto incorreto.

## Decisão proposta

Usar intervalos Unicode semiabertos `[start, end)` no texto do `Document` como
identidade canônica. Linha e coluna são projeções 1-based em code points. O
parser preserva mapeamento para bytes e newlines do arquivo original.

## Consequências

- CRLF, LF, Unicode e arquivo vazio exigem testes dedicados.
- Serializadores não podem recalcular offsets sobre texto transformado.
- Fixer futuro precisa mapear edições ao arquivo original.

## Aprovação necessária

Aceito pelo mantenedor em 2026-08-12, antes da publicação de `Diagnostic` ou
schema JSON.
