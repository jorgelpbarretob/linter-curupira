# Tarefa case-015 — atualização difícil de runbook

## Objetivo de produto
Aplicar a mudança de tag e enxugar o texto, baixando tokens de leitura.
Não é só passar no lint.

## Mudança definida
A válvula XV-201 foi substituída pela XV-205 no projeto. Todo o runbook deve
referenciar XV-205. O passo de confirmação de posição no painel foi removido
do projeto e deve sair do runbook.

## Entrada
`runbook-envase.md`.

## Entregar
O mesmo arquivo atualizado.

## Pronto quando
1. Nenhuma referência restante a XV-201.
2. Tags preservadas: XV-205, P-77, FS-12.
3. Passo de confirmação de posição no painel removido.
4. Sem ponto e vírgula em prosa.
5. Texto final mais curto que o input em caracteres de prosa.
6. Braço com Curupira: `curupira lint` exit 0 nas regras do aceite.

## Restrições
- Não altere nenhum outro fato técnico.
- Não envie a APIs.
