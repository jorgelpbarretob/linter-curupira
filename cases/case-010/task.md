# Tarefa case-010 — modernizar runbook denso

## Objetivo de produto
Legibilidade para o time e menos tokens de ida e volta na sessão de edição.

## Mudança técnica obrigatória
- `hermes-lint` → `curupira`
- `HERMES-PT-PONT-001` → `CURUPIRA-PT-PONT-001`
- comando correto inclui subcomando `lint`

## Entrada
`runbook.md` legado denso.

## Pronto quando
1. Zero ocorrências hermes-lint / HERMES-PT-*.
2. Usa `curupira lint ... --enable-rule CURUPIRA-PT-PONT-001`.
3. Mantém fluxo: instalar → lint → corrigir → anexar JSON → abrir PR.
4. Remove ponto e vírgula de prosa e quebra o muro de texto.
5. Com Curupira: lint exit 0 no runbook final.
