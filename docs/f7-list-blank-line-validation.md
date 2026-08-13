# Validação F7: associação por uma linha vazia

Data: 2026-08-13
Regra: `STE-I9-LIST-001`
Status: challenge pequeno aprovado e validado; avaliação posterior concluída

## Escopo autorizado

O mantenedor aprovou as Emendas 1–2 do plano de expansão e as 17 labels de
`corpus/f7/vertical-list-blank-line-challenge.jsonl`. A autorização cobriu
somente TDD para aceitar zero ou exatamente uma linha somente de whitespace
entre um lead-in elegível e uma lista Markdown direta. Promoção, provider,
fixer, `FixEdit`, `ste fix` e `safe_autofix` permaneceram fora do escopo.

A família de fonte proposta para o futuro holdout mudou de
`kubernetes/website` para `dotnet/docs`: a filtragem estrutural e semântica
pré-output não encontrou oito heads elegíveis e independentes em Kubernetes. O
snapshot `.NET Docs` congelado no plano oferece 77 ocorrências estruturais e 38
heads distintos antes da revisão humana. Nenhuma das fontes externas foi
executada pelo detector nesta rodada.

## Evidência Red/Green

Red:

```text
tests/rules/test_vertical_list_colon.py::test_vertical_list_rule_reports_across_one_blank_line
FAILED: expected 1 diagnostic, got 0
```

Green: a regra passou a recuar uma linha adicional somente quando a linha
imediatamente anterior ao primeiro item é whitespace-only. Com duas linhas
vazias, o segundo recuo encontra outra linha vazia e a regra se abstém pelas
precondições existentes. Nenhuma regex lexical, metadata ou sugestão mudou.

O teste unitário mínimo passou, seguido do corpus aprovado. A tranche contém:

- 8 violações com emissão esperada;
- 5 não violações com emissão zero;
- 3 casos ambíguos com abstenção;
- 1 violação deliberadamente abstida por ter duas linhas vazias.

## Resultado combinado provisório

Combinando o seed e a readiness anteriores com este challenge de
desenvolvimento:

- TP = 19, FP = 0, FN = 4, TN = 14;
- emissões em casos ambíguos = 0; abstenções ambíguas = 9;
- precisão = 1,00; Wilson bilateral de 95% = 0,832–1,000;
- recall = 19 / 23 = 0,826.

Esses números são regressão de desenvolvimento, não evidência de holdout. O
limite inferior Wilson permanece abaixo de 0,95 e a regra não é promovível.

## Gates executados

```text
.venv/bin/python -m pytest -q
211 passed, 4 skipped

.venv/bin/python -m ruff check .
All checks passed!

.venv/bin/python -m ruff format --check .
70 files already formatted

.venv/bin/python -m mypy src
Success: no issues found in 33 source files
```

Os quatro skips são os mesmos caminhos NLP opcionais esperados no ambiente
base. O corpus de linha vazia passou 17/17 e os testes direcionados da regra e
do corpus passaram 17/17.

## Estado após a validação

`STE-I9-LIST-001` continua `preview/info`, desabilitada por padrão e com
`safe_autofix = false`. O próximo trabalho permitido é preparar o challenge
completo e o holdout com labels `pending-human-review`; nenhum deles pode ser
executado antes de aprovação humana e congelamento do hash.

Esse passo posterior foi concluído e falhou o gate de promoção sem falso
positivo. Consulte
[`f7-list-frozen-evaluation.md`](f7-list-frozen-evaluation.md).
