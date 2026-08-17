# Critérios de sucesso — split gate × qualidade

Status: ativo  
Release âncora: `v1-cli-default-2026-08-16` (fechada)

## Gate operacional (binário, por artefato/rodada)

Passa só se **ambos**:

1. `curupira lint` foi executado no braço de tratamento (evidência em tool log)
2. residual das regras do aceite = 0 no artefato final

Falha de gate ≠ “produto inútil”. É só não-conformidade operacional.

## Resultados de qualidade (independentes do gate)

Medir e reportar **separados**, sem fundir num score único:

| Resultado | Fonte |
|---|---|
| Legibilidade | score automático + rubrica humana 1–5 |
| Aceite | classes da rubrica (cego quando possível) |
| Retrabalho | ciclos até aceite |
| Tokens de sessão | SessionDB in/out/total |
| Tools / wall time | SessionDB + arm-meta |

## Default de runtime

- preflight default = instrução curta + CLI `curupira lint`
- skill preload **não** é default
- skill completa só sob pedido explícito ou coleta improve

## Regra anti-ajuste pós-resultado

Release fechada não muda protocolo nem casos usados nela.
Evolução = nova versão (`v2`, …) com diff explícito.
