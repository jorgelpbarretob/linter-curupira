# Avaliação congelada F7: `STE-I9-LIST-001`

Data: 2026-08-13
Status: holdout executado; promoção bloqueada
Regra: `STE-I9-LIST-001`

## Integridade e ordem da avaliação

O mantenedor aprovou as 107 labels em 2026-08-13. Antes de qualquer execução,
`vertical-list-holdout.jsonl` foi congelado com SHA-256:

```text
30d30b0ab2377983f33329a032286ed6f31cfab7b92cd168fc335a66d34b1cc7
```

O challenge foi executado primeiro. Ele revelou uma emissão incorreta quando um
item aninhado era contado como segundo item de nível superior. O Red/Green passou
a exigir indentação uniforme no run; o challenge então passou 47/47. O hash do
holdout foi verificado novamente antes da primeira abertura.

Nenhum código ou label foi alterado depois do output do holdout.

## Resultado do holdout

O primeiro run congelado produziu:

- TP = 13;
- FP = 0;
- FN = 17;
- TN = 30;
- precisão por emissão = 1,00;
- recall = 13 / 30 = 0,433.

Por família:

| Fonte | TP | FP | FN | TN |
|---|---:|---:|---:|---:|
| GitHub Docs | 5 | 0 | 5 | 10 |
| .NET Docs | 7 | 0 | 3 | 10 |
| VS Code Docs | 1 | 0 | 9 | 10 |

Os 30 controles naturais não produziram falso positivo. Entre as 30 mutações
mínimas, 13 emitiram e 17 abstiveram. O holdout não contém violações naturais
terminadas por ponto; portanto, a validade externa dos positivos continua
limitada mesmo nas emissões corretas.

## Resultado combinado

Combinando seed, readiness, challenge pequeno, challenge completo e holdout:

- TP = 56, FP = 0, FN = 27, TN = 52;
- emissões em casos ambíguos = 0; abstenções ambíguas = 18;
- precisão = 1,00;
- Wilson bilateral de 95% = 0,936–1,000;
- recall = 56 / 83 = 0,675.

O gate exigia simultaneamente 73 emissões corretas, limite inferior Wilson de
0,95, pelo menos 30 emissões corretas no holdout e zero FP. Somente o último
critério passou. A avaliação falhou por 17 emissões corretas combinadas, pelo
Wilson e pelo mínimo do holdout.

## Interpretação e decisão

Os erros observados são falsos negativos conservadores, não autorização para
alargar o detector automaticamente. O holdout agora está consumido para esta
versão: qualquer mudança orientada por seus casos exige challenge novo e outro
holdout independente antes de uma nova proposta de promoção.

`STE-I9-LIST-001` permanece `preview/info`, desabilitada por padrão e com
`safe_autofix = false`. Não existe provider elegível; implementação de fixer,
`FixEdit` e `ste fix` continua bloqueada.

## Gates de qualidade

```text
.venv/bin/python -m pytest -q
214 passed, 4 skipped, 1 xfailed

.venv/bin/python -m ruff check .
All checks passed!

.venv/bin/python -m ruff format --check .
70 files already formatted

.venv/bin/python -m mypy src
Success: no issues found in 33 source files

sha256sum -c vertical-list-holdout.sha256
vertical-list-holdout.jsonl: OK
```

Os quatro skips são os mesmos caminhos NLP opcionais do ambiente base. O
`xfail` estrito preserva de forma executável a falha conhecida do holdout; um
futuro passe integral vira `XPASS` e exige uma nova decisão explícita, enquanto
um teste separado mantém os 30 controles naturais protegidos contra FP.
