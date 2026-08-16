# PT4 spaCy adapter — evidência pré-inferência e rework

Status: rework v5 model-panel approved; no candidate output or scoring
Date: 2026-08-16

Os artefatos `*-v1` preservam o snapshot aprovado antes da primeira inferência.
A tentativa v1 falhou durante o warm-up descartado, antes de criar output ou
iniciar scoring. `controlled-inference-failure-v1.json` fixa essa ocorrência.

`adapter-manifest-v2.json` congela o rework final, os testes e as fronteiras da
nova execução. `model-panel-review-v2.json` registra a sequência de findings,
adjudicações e a aprovação final unânime de Maritaca, Grok e Kimi 2.7. Nenhum
output de `pt_core_news_sm` entra neste diretório.

Respostas brutas, prompts e metadados do painel ficam sob custódia externa em
`/home/jorge/.hermes/pt4-spacy-adapter/` e a falha operacional bruta em
`/home/jorge/.hermes/pt4-spacy-run/20260816-v1/`. Os resumos redistribuíveis
contêm apenas metadados, decisões e hashes.
