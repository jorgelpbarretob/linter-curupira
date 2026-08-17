# Tarefa case-011 — criação com insumo cru e denso

## Objetivo de produto
Produzir um procedimento novo, enxuto e legível para o operador, baixando
tokens de leitura e de saída. Não é só passar no lint.

## Entrada
`notas-turno.md` (notas cruas de passagem de turno, densas).

## Entregar
Procedimento novo em `procedimento-cip.md`.

## Pronto quando
1. Tags preservadas: CIP-3, XV-210, P-301, TI-77.
2. Ordem lógica: preparação, circulação alcalina, enxágue, verificação.
3. Frases curtas. Uma ação principal por passo quando possível.
4. Sem ponto e vírgula em prosa.
5. Texto final com menos caracteres de prosa que o equivalente reescrito
   literalmente das notas.
6. Braço com Curupira: `curupira lint` exit 0 nas regras do aceite.

## Restrições
- Não invente concentrações, temperaturas ou tempos fora das notas.
- Não envie a APIs.
