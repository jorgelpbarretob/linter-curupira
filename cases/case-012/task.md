# Tarefa case-012 — regressão difícil em SOP longo

## Objetivo de produto
Baixar custo de tokens da sessão e deixar o texto mais legível para o
operador. Não é só passar no lint.

## Entrada
`sop-mosturacao.md` (SOP longo, denso, com muitos ponto e vírgula).

## Entregar
O mesmo arquivo, pronto para chão de fábrica.

## Pronto quando
1. Tags preservadas: TT-41, P-12, XV-55, FQ-09, TIC-70.
2. Mesma ordem lógica: pré-aquecimento, mistura, rampas, filtração.
3. Frases curtas. Uma ação principal por passo quando possível.
4. Sem ponto e vírgula em prosa.
5. Sem parágrafo denso com múltiplas ordens escondidas.
6. Texto final preferencialmente mais curto que o input em caracteres de prosa.
7. Braço com Curupira: `curupira lint` exit 0 nas regras do aceite.

## Restrições
- Não invente interlocks, setpoints ou pessoas.
- Não envie a APIs.
