# Validação e avaliação congelada da iteração de recall v2

Data: 2026-08-13
Regra: `STE-I9-LIST-001`
Status: avaliação concluída; gates quantitativos passaram; promoção aguarda gate separado

## Escopo e contrato

O mantenedor autorizou uma nova iteração de recall com holdout independente.
A Emenda 3 de `f7-list-evidence-expansion-plan.md` transforma os 17 FN do
holdout v1 consumido em challenge e amplia somente dois comportamentos:

- itens de lista podem começar com markup quando há texto visível lintável na
  mesma linha;
- lead-ins podem ter frases prefixas completas quando todos os spans cobrem a
  linha e o padrão terminal continua `these <head>.`.

O parser global, metadata, head lexical, limite de uma linha vazia, indentação
peer e span diagnosticado não mudaram. Inline-code-only continua abstenção.

## TDD observado

Fatia 1 — markup no começo do item:

```text
RED: item iniciado por **bold** produziu 0 diagnóstico, esperado 1
GREEN: buscar texto não-whitespace lintável depois do marcador; 1 passed
```

Fatia 2 — frase prefixa completa:

```text
RED: duas frases completas com lead-in terminal produziram 0, esperado 1
GREEN: validar cobertura contígua por uma ou mais sentenças completas; 1 passed
```

Duas labels antigas já tinham `truth=violation` e expectativa de abstenção pela
política anterior. A Emenda 3 mudou somente `expected_diagnostics` para 1 e
`expected_replacement` para `:`; o texto e a ground truth não mudaram.

## Resultado de desenvolvimento

O holdout v1 agora é regressão conhecida, não evidência independente. Dos seus
17 FN, 16 passaram a emitir. O caso `f7-list-ho-github-p08`, cujos dois itens
são somente inline code, permanece abstido.

No conjunto consumido, sem incluir o holdout v2:

- TP = 74, FP = 0, FN = 9, TN = 52;
- emissões ambíguas = 0; abstenções ambíguas = 18;
- precisão = 1,00;
- Wilson bilateral de 95% = 0,951–1,000;
- recall = 74 / 83 = 0,892.

Esses números passam o piso aritmético combinado, mas não autorizam promoção:
os casos que orientaram a mudança são desenvolvimento. O gate ainda exige 30
emissões corretas em um holdout v2 congelado e zero FP natural.

## Holdout v2 preparado

`corpus/f7/vertical-list-holdout-v2.jsonl` contém 30 pares novos: uma mutação
`:` → `.` e seu controle natural por ocorrência. São 30 heads e 30 referências
de origem não usados anteriormente, distribuídos em cinco produtos:

| Fonte | Pares |
|---|---:|
| GitHub Docs | 4 |
| Kubernetes Website | 4 |
| VS Code Docs | 1 |
| .NET Docs | 11 |
| Pulumi Docs | 10 |

As 60 labels foram aprovadas pelo mantenedor em 2026-08-13. A triagem e as
invariantes não executaram a regra. Antes da primeira execução, o arquivo final
foi congelado em `vertical-list-holdout-v2.sha256` com SHA-256:

```text
b91d6c6c1bd7f5955332e86e80504c1890e3437531ce352781084ab74cd07ca2
```

## Execução congelada

A verificação estática confirmou 60 IDs únicos, 30 pares, 30 heads novos, 30
referências de origem novas, hashes de texto reconciliados e mutações que
diferem do controle em exatamente um code point (`:` → `.`). O hash congelado
foi verificado imediatamente antes da execução.

A primeira tentativa do avaliador percorreu o holdout, mas abortou antes de
produzir resultado porque um caso legado de desenvolvimento não possui o campo
opcional `expected_replacement`. A regra, as labels e o arquivo congelado não
foram alterados; o retry corrigiu somente a instrumentação externa. Uma segunda
tentativa abortou ainda no corpus de desenvolvimento, antes de abrir o holdout,
por causa do nome legado `category` em vez de `truth` no seed.

A execução concluída usou o mesmo hash e não revelou mismatch no v2. O primeiro
cálculo combinado forçou extensão `.md` em dois controles `plain_text`; a
matriz v2 não foi afetada porque todos os seus casos são Markdown. A matriz de
desenvolvimento foi então rederivada separadamente com a extensão declarada por
caso, sem reexecutar o holdout.

## Resultado do holdout v2

- TP = 30, FP = 0, FN = 0, TN = 30;
- precisão por emissão = 1,000;
- recall = 1,000;
- Wilson bilateral de 95% = 0,886–1,000;
- mismatches = 0.

| Fonte | TP | FP | FN | TN |
|---|---:|---:|---:|---:|
| GitHub Docs | 4 | 0 | 0 | 4 |
| Kubernetes Website | 4 | 0 | 0 | 4 |
| VS Code Docs | 1 | 0 | 0 | 1 |
| .NET Docs | 11 | 0 | 0 | 11 |
| Pulumi Docs | 10 | 0 | 0 | 10 |

## Resultado combinado e gates

Com seed, readiness, challenges, holdout v1 consumido e holdout v2:

- TP = 104, FP = 0, FN = 9, TN = 82;
- emissões ambíguas = 0; abstenções ambíguas = 18;
- precisão = 1,000;
- Wilson bilateral de 95% = 0,964–1,000;
- recall = 104 / 113 = 0,920.

| Gate | Exigido | Observado | Resultado |
|---|---:|---:|---|
| Precisão combinada | >= 0,95 | 1,000 | passou |
| Wilson inferior combinado | >= 0,95 | 0,964 | passou |
| Emissões corretas combinadas | >= 73 | 104 | passou |
| Emissões corretas no holdout v2 | >= 30 | 30 | passou |
| FP natural | 0 | 0 | passou |
| Emissões ambíguas | 0 | 0 | passou |

A revisão quantitativa independente reproduziu os pontos e intervalos sem
delta. Veredito: `CONFIRMED_WITH_CAVEATS`. A validade externa permanece
limitada porque os 30 positivos do v2 são mutações mínimas de lead-ins naturais
terminados por dois-pontos; os controles são naturais, mas não há violações
naturais terminadas por ponto. O estrato VS Code tem apenas um par.

## Gates executados

```text
.venv/bin/python -m pytest -q
218 passed, 4 skipped

.venv/bin/python -m pytest -q tests/corpus/test_vertical_list_colon_corpus.py
7 passed

.venv/bin/python -m ruff check .
All checks passed!

.venv/bin/python -m ruff format --check .
70 files already formatted

.venv/bin/python -m mypy src
Success: no issues found in 33 source files

cd corpus/f7 && sha256sum --check vertical-list-holdout-v2.sha256
vertical-list-holdout-v2.jsonl: OK

.venv/bin/ste lint /tmp/ste-f7-recall-v2-smoke.md \
  --enable-rule STE-I9-LIST-001 --format json
1 diagnóstico no ponto final esperado; exit 1 esperado para achado
```

Os quatro skips são os caminhos NLP opcionais esperados no ambiente base.

## Decisão atual

`STE-I9-LIST-001` permanece `preview/info`, desabilitada por padrão e com
`safe_autofix = false`. Os gates quantitativos habilitam uma revisão de
promoção, mas não mudam metadata automaticamente. O próximo gate é revisão
independente seguida de decisão humana explícita. O provider e o TDD do fixer
continuam bloqueados até promoção e autorização próprias.
