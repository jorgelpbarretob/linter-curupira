# Encerramento e congelamento da linha inglesa

Status: Frozen
Decision date: 2026-08-13

## Decisão

A linha de produto em inglês foi encerrada por decisão do mantenedor. Código,
ADRs, testes e evidências existentes permanecem no histórico para auditoria e
migração segura de componentes independentes de idioma. Não serão criadas novas
regras inglesas, não haverá promoção para `stable`, e fixer, NLP inglês e
integrações específicas da ASD-STE100 não avançam.

Congelamento não significa apagar imediatamente. Remoção ou renomeação será
feita em incrementos reversíveis depois que o substituto pt-BR possuir testes de
caracterização.

## Snapshot final da Rodada 2

A execução controlada usou 55 invocações isoladas, distribuídas pelos documentos
selecionados para cada regra, e 55 replays de baseline. Produziu 20 diagnósticos.

Hashes dos artefatos externos:

- inventário: `bebbabe41b28f59e87250e188fe946b237152f9293c8765a06d1322cb3d94c38`;
- diagnósticos: `07fc6f34927c8922ca7fd621d2a7dc1925d4861b468faf15ca78707535990cfb`;
- métricas: `ab3ba4ae73be402d4bc1c7a19f26244d4bb7f0d1bdcfb628d20bbb924c497627`.

| Regra | TP | FP | FN | TN | Precisão | Recall | Estado de encerramento |
|---|---:|---:|---:|---:|---:|---:|---|
| `STE-I9-PUNCT-001` | 2 | 0 | 0 | 67 | 1,000 | 1,000 | amostra positiva insuficiente |
| `STE-I9-LIST-001` | 0 | 0 | 0 | 0 | n/a | n/a | 73 casos fora do escopo; sem denominador normativo |
| `STE-I9-PARA-001` | 0 | 0 | 0 | 86 | n/a | n/a | sem suporte positivo |
| `STE-I9-SENT-001` | 12 | 1 | 28 | 200 | 0,923 | 0,300 | reprovada por precisão/recall |
| `STE-I9-SENT-002` | 4 | 1 | 11 | 166 | 0,800 | 0,267 | reprovada por precisão/recall |

Os intervalos inferiores de Wilson para precisão foram 0,342 em
`PUNCT-001`, 0,667 em `SENT-001` e 0,376 em `SENT-002`. Os resultados não
autorizam promoção ou fixer. O holdout está consumido e não pode ser apresentado
como evidência independente de mudanças futuras.

## Disposição dos ativos

Podem ser caracterizados para migração pt-BR:

- parser e tratamento lossless de markup;
- offsets e localizações Unicode;
- contratos de domínio, registry e engine;
- ordenação, reporting e baseline;
- precedência de configuração e composição da CLI.

Permanecem históricos e não migram como regra de produto:

- catálogo e namespace `STE-I9-*`;
- locators e alegações relacionadas à ASD-STE100;
- modelo `en_core_web_sm` e heurísticas linguísticas inglesas;
- corpora, labels e thresholds derivados da linha inglesa;
- resultados da Rodada 2 como evidência para pt-BR.

## Rastreabilidade

O executor reproduzível está em
`tools/product_evidence/round2_evaluate.py`. Inventário, labels, corpora e
resultados vivem fora do repositório conforme os contratos de licença e
congelamento registrados nos documentos da Rodada 2.

O encerramento não altera retroativamente resultados nem estados publicados.
Todas as regras inglesas terminam como `preview`.
