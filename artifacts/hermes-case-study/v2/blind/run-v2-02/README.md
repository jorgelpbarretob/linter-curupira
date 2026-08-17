# Revisão cega — run-v2-02

Cases: 015, 016, 002, 005, 006 (extensão que fecha 16/16 do banco).

## Como revisar

1. Para cada `case-XXX-A.md` e `case-XXX-B.md`, aplique `docs/hermes-case-study/rubric-v1.md`.
2. Não tente adivinhar qual é control/cli.
3. Preencha `scores-template.json` (clareza 1–5, classe de aceite, erros críticos).
4. Só depois compare com `KEY-DO-NOT-SHARE-until-scores.json`.

## Gate operacional (já medido na bateria)

Independente da rubrica humana: lint executado + residual 0 no braço CLI.
Resultado: 5/5 pares com gate operacional OK.

## Atenção — executor

run-v2-02 rodou com grok-4.6 (default do profile em 2026-08-17).
run-v2-01 rodou com grok-4.5. Não misturar medianas de tokens entre baterias.
