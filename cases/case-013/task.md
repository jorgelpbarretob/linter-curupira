# Tarefa case-013 — transformação de notas em procedimento

## Objetivo de produto
Transformar notas soltas em procedimento enxuto e legível, baixando tokens
de leitura. Não é só passar no lint.

## Entrada
`notas-sanitizacao.md` (notas de sanitização com horários e tags).

## Entregar
Procedimento em `procedimento-sanitizacao.md`.

## Pronto quando
1. Tags preservadas: SD-8, XV-302, P-410, CT-15.
2. Horários das notas preservados como referência.
3. Frases curtas. Uma ação principal por passo quando possível.
4. Sem ponto e vírgula em prosa.
5. Texto final mais curto em caracteres de prosa que as notas.
6. Braço com Curupira: `curupira lint` exit 0 nas regras do aceite.

## Restrições
- Não invente etapas ausentes nas notas.
- Não envie a APIs.
