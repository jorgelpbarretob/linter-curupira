# Tarefa case-016 — mitigação a partir de timeline densa

## Objetivo de produto
Produzir uma instrução de mitigação curta e direta, bem mais curta que a
timeline. Baixar tokens de saída é meta explícita. Não é só passar no lint.

## Entrada
`timeline-incidente.md` (timeline sanitizada de incidente).

## Entregar
Instrução de mitigação em `mitigacao-parada.md`.

## Pronto quando
1. Tags preservadas: PS-9, XV-140, P-52, LS-03.
2. Instrução com no máximo 50% dos caracteres de prosa da timeline.
3. Frases curtas. Uma ação principal por passo quando possível.
4. Sem ponto e vírgula em prosa.
5. Sem inferência além da timeline (causas não confirmadas não entram).
6. Braço com Curupira: `curupira lint` exit 0 nas regras do aceite.

## Restrições
- Não especule causa raiz.
- Não envie a APIs.
