# PT4 — protocolo de bake-off da análise linguística local

Status: Accepted
Date: 2026-08-16
Protocol version: `hermes-pt4-bakeoff/v1`

Corpus status: offset corpus frozen by unanimous ADR-020 panel; harness next

## Decisão e fonte de verdade

Pergunta: qual configuração local fornece a menor porta suficiente de
tokenização, sentenças, lema, UPOS, morfologia e dependências para futuras
regras `nlp` do Hermes, preservando offsets exatos, licença auditável e runtime
offline?

A fonte de verdade linguística será o split de teste congelado de UD Portuguese
PetroGold, release e commit ainda a fixar no manifesto pré-execução. PetroGold é
pt-BR técnico do domínio de petróleo e gás, foi revisado manualmente por
linguistas e é distribuído sob CC BY-SA 4.0.[1] Ele será **evidência de
desenvolvimento de PT4**, não holdout de regra PT5.

A fonte de verdade de offsets e integração será um corpus autoral Hermes,
aprovado e congelado antes da primeira execução. Nenhuma saída de candidato
pode orientar seus textos ou labels.

## Evidência, premissas e exclusões

### Evidência externa

- annotations CoNLL-U do PetroGold para tokenização, sentença, lema, UPOS,
  FEATS e dependências;
- manifestos oficiais de biblioteca/modelo para versões, componentes e
  checksums;
- medições produzidas pelo harness PT4 sobre artefatos congelados.

### Premissas que serão testadas

- um modelo treinado em notícias pode generalizar o suficiente para prosa
  técnica brasileira;
- a configuração Stanza sem character LM pode competir dentro do orçamento
  local;
- a representação superfície/palavra cobre contrações sem perder offsets.

### Fora do escopo

- NER, constituency, coreference, embeddings, language detection e GPU;
- utilidade ou promoção de qualquer regra;
- ajuste de modelo, retokenização aprendida ou fine-tuning;
- corpus, labels e erros do holdout v1 de `HERMES-PT-PONT-001`;
- fontes que possam integrar um futuro holdout PT5.

## Gate 0 — elegibilidade antes de qualquer inferência

Para cada candidato, congelar em manifesto separado:

1. nome e versão exatos da biblioteca, Python e plataforma;
2. URL imutável ou commit do artefato, tamanho e SHA-256 recomputado;
3. lock completo dos wheels transitivos com hashes;
4. modelo, configuração, componentes habilitados e checksums;
5. licenças de código, pesos e fontes de treino, com obrigações de NOTICE e
   redistribuição;
6. instrução de instalação a partir de wheelhouse/cache local;
7. prova de carga e execução com rede negada;
8. confirmação de que nenhum tipo do SDK entra no domínio.

Falha ou dúvida em qualquer item torna o candidato `ineligible`; não se baixa o
modelo para “ver se funciona”. O candidato Stanza permanece condicional ao gate
de licença descrito no ADR-019.

## Corpora congelados

### A. `pt4-offset-development-v1`

Mínimo de 160 casos autorais CC BY 4.0, distribuídos igualmente entre:

- Unicode, diacríticos combinantes, emoji, LF e CRLF;
- contrações, clíticos e tokens multiword;
- abreviações, versões, unidades, identificadores e pontuação técnica;
- fronteiras estruturais de TXT/Markdown, incluindo markup que deve provocar
  segmentação conservadora ou abstenção.

Cada caso registra texto original, spans esperados, tokens de superfície,
sentenças, palavras sintáticas aplicáveis, razão e status de revisão. Antes do
hash canônico, 100% dos casos devem passar validação mecânica e receber votos
`approve` isolados de `sabia-4-thinking`, `grok-4.6` e
`kimi-k2.7-code:cloud`, conforme ADR-020.

### B. `UD_Portuguese-PetroGold-test`

Congelar release, commit, arquivos de teste, licença e SHA-256. Usar todo o
split oficial de teste sem remover casos depois de observar resultados. Se o
split não trouxer fronteiras de documento utilizáveis, a unidade de bootstrap
será a sentença e essa limitação constará do relatório.

Antes de qualquer inferência, o harness congela esta projeção ouro CoNLL-U:

1. cada linha de intervalo `i-j` define um único `SurfaceToken`, com `FORM` e
   span exato no comentário `# text`; as linhas inteiras cobertas pelo intervalo
   definem `SyntacticWord`s que apontam para esse token;
2. cada linha inteira fora de intervalo define simultaneamente um
   `SurfaceToken` e um `SyntacticWord` que aponta para ele;
3. os tokens de superfície são alinhados da esquerda para a direita ao
   `# text`, por igualdade Unicode exata de `FORM`; entre tokens só se admite o
   whitespace presente no texto, e `SpaceAfter=No` exige adjacência;
4. qualquer reconstrução impossível ou ambígua é erro do artefato ouro,
   registrado antes da execução dos candidatos; não se corrige nem remove o
   caso depois de observar resultados;
5. a saída candidata primeiro casa `SurfaceToken`s por span exato. Dentro de
   cada superfície casada, `SyntacticWord`s são alinhadas por ordem. Diferença
   de quantidade deixa os itens excedentes sem alinhamento e conta como erro
   nas métricas de palavra aplicáveis, nunca autoriza casamento textual ad hoc;
6. heads candidatos são comparados somente pela correspondência determinística
   de palavras anterior. Palavra ou head sem correspondência erra UAS e LAS.

Essas regras, inclusive MWT, `SpaceAfter=No`, desalinhamento e dependências,
devem ter fixtures conhecidas e hashes congelados no manifesto do harness.

Casos duplicados ou derivados das fontes de treino declaradas pelo candidato
devem ser detectados antes da inferência. Contaminação material torna o
candidato inelegível para aquela métrica, não autoriza trocar o corpus.

## Métricas

Todos os resultados usam precisão interna completa e arredondamento apenas na
apresentação a seis casas decimais.

| Métrica | Unidade e correspondência |
|---|---|
| token precision/recall/F1 | span Unicode exato e texto de `SurfaceToken` |
| sentence precision/recall/F1 | envelope Unicode exato da sentença |
| lemma accuracy | palavra gold alinhada, comparação exata definida no harness |
| UPOS accuracy | palavra gold alinhada |
| FEATS micro-F1 | pares `feature=value`, conjunto vazio explícito |
| UAS | head correto entre palavras gold alinhadas |
| LAS | head e relação universal corretos |
| offset errors | qualquer span fora do texto, sobreposto ou com slice divergente |
| abstention/unsupported | casos não analisados por contrato, por motivo |
| determinism | hash canônico da saída em três execuções |
| cold load | segundos até backend pronto, sem inferência |
| latency | p50/p95 por 1.000 palavras gold, após uma warm-up descartada |
| throughput | palavras gold por segundo |
| peak RSS | MiB máximos do processo |
| footprint | MiB de wheels, modelos e recursos instalados |

O harness valida ainda bijeção de casos, contagens, head dentro da sentença,
palavra ligada a token de superfície e ausência de tipos serializados do SDK.

## Gates quantitativos

### Bloqueadores comuns

- `offset_errors == 0` nos dois corpora;
- `token_F1 >= 0.990000`;
- `sentence_F1 >= 0.950000`;
- `UPOS_accuracy >= 0.920000`;
- `lemma_accuracy >= 0.900000`;
- `FEATS_micro_F1 >= 0.850000`;
- `UAS >= 0.800000` e `LAS >= 0.750000`;
- três hashes de saída idênticos;
- zero crash, download ou tentativa de rede;
- cold load `<= 60 s`, p95 `<= 5 s/1.000 palavras`, peak RSS
  `<= 2.500 MiB` e footprint `<= 2.000 MiB` no ambiente de referência.

Esses gates aceitam uma capacidade para desenvolvimento; não são evidência de
precisão de uma regra e não promovem nada a `stable`.

### Escolha entre candidatos aprovados

Calcular o score de utilidade linguística:

```text
S = 0,15 token_F1
  + 0,10 sentence_F1
  + 0,10 lemma_accuracy
  + 0,15 UPOS_accuracy
  + 0,15 FEATS_micro_F1
  + 0,10 UAS
  + 0,25 LAS
```

Reamostrar a unidade de documento 10.000 vezes com seed `20260816`; se não
houver documento, reamostrar sentenças e declarar a limitação. Reportar IC
percentil 95% de cada métrica e do delta pareado de `S`.

- vence o maior `S` quando o IC 95% do delta exclui zero;
- se o IC inclui zero ou `|delta S| < 0,005`, desempatar por menor p95, depois
  peak RSS e depois footprint;
- se somente um candidato for elegível, ele pode ser selecionado apenas se
  passar todos os gates; o parecer registra `single-qualified-candidate`;
- nenhum aprovado resulta em `insufficient-evidence`, sem relaxar threshold ou
  trocar corpus depois do resultado.

Como análise de sensibilidade, recalcular sete scores removendo uma métrica por
vez e renormalizando os pesos restantes. Se o vencedor mudar em três ou mais
cenários, a decisão recebe `weight-sensitive` e exige revisão do mantenedor;
essa divergência não pode ser encerrada pelo Grok.

## Auditoria quantitativa do pré-registro

`VERDICT: CONFIRMED_WITH_CAVEATS`

- **Scope and source-of-truth:** fórmulas, limites, unidade de reamostragem e
  regra de seleção deste protocolo; não há resultado de modelo submetido.
- **Independent result:** os sete pesos são não negativos, estão entre zero e
  um e somam exatamente `1,0`; todos os gates de qualidade também estão no
  intervalo `[0, 1]` e são monotônicos na direção esperada.
- **Submitted result and delta:** soma declarada `1,0`; soma recomputada `1,0`;
  delta absoluto `0,0` e relativo `0,0%`.
- **Material findings:** nenhuma falha aritmética. Os floors são critérios de
  produto pré-registrados, não estimativas de desempenho. O bootstrap por
  sentença, se não houver IDs de documento, subestima dependência entre
  sentenças próximas e deve aparecer como limitação.
- **Assumptions and missing inputs:** contagens finais do split PetroGold,
  hardware, footprint, tempos, outputs e elegibilidade de licença ainda não
  existem; nenhum veredito de backend é possível nesta etapa.
- **Sensitivity / uncertainty:** IC percentil pareado, regra de empate e análise
  leave-one-metric-out acima são obrigatórios; mudança frequente de vencedor
  impede decisão operacional automática.
- **Reproduction:** recomputação executada no virtualenv do projeto com
  `.venv/bin/python -c 'weights=(0.15,0.10,0.10,0.15,0.15,0.10,0.25); print(sum(weights))'`.

## Sequência congelada

1. resolver licenças e congelar manifestos dos candidatos;
2. criar, revisar e congelar os dois corpora e o ambiente de referência;
3. implementar harness e adapters experimentais fora do caminho de produção;
4. testar o harness contra fixtures pequenas com respostas conhecidas;
5. executar todos os candidatos na mesma ordem determinada por hash do ID;
6. selar saídas antes de calcular scores;
7. auditar métricas com implementação independente;
8. publicar somente resultados redistribuíveis, hashes e limitações;
9. submeter a decisão estruturada ao Grok pela delegação operacional;
10. somente depois abrir TDD da porta com o candidato aceito.

Não há parada antecipada. Falha operacional de um candidato é resultado; uma
única repetição é permitida somente para falha de infraestrutura demonstrada e
é registrada junto com a primeira tentativa.

## Artefatos exigidos

- manifesto de cada candidato e wheelhouse/cache hash manifest;
- manifesto dos corpora e relatório de contaminação;
- configuração e ambiente de referência;
- saídas canônicas por candidato;
- métricas, intervalos, deltas e medições operacionais;
- auditoria quantitativa independente no formato da skill
  `quantitative-review`;
- parecer Grok estruturado com hashes de entrada/prompt/schema/resposta,
  modelo solicitado/retornado, request/session IDs, tokens, custo e latência;
- decisão `accepted`, `single-qualified-candidate`, `insufficient-evidence` ou
  `rework`.

## Estado pré-inferência

Este documento abriu PT4 e pré-registrou o bake-off antes de qualquer saída
candidata. Gate 0, corpora/ambiente e harness já concluíram seus incrementos;
nenhuma dependência entrou no produto e nenhuma regra PT5 foi implementada.

O gate documental foi aceito com condições pelo revisor Grok em 2026-08-16.
Antes da primeira inferência, o manifesto do harness fixou o envelope ouro de
sentença como o menor intervalo Unicode da primeira à última
`SurfaceToken`, com fixture hash-congelada, e limitar métricas linguísticas aos
casos com análise ouro alinhável. Abstenção contratual é reportada somente em
`abstention/unsupported`; não pode remover caso difícil nem inflar as demais
métricas. Evidência e hashes estão em
`docs/hermes-pt4-grok-opening-review.md`.

O Gate 0 posterior foi aceito com condições e está registrado em
`docs/hermes-pt4-gate0-eligibility-v1.md` e
`docs/hermes-pt4-gate0-grok-review-v1.md`. Essa execução adquiriu somente o
candidato spaCy fora do ambiente do projeto, instalou o wheelhouse congelado e
carregou o modelo sem processar texto. Stanza não foi adquirido por dúvida de
licença. Nenhum desses atos seleciona backend ou abre as etapas seguintes.

O incremento seguinte congelou PetroGold `r2.18`, o ambiente de referência e
uma proposta autoral de 160 casos, conforme
`docs/hermes-pt4-corpora-environment-v1.md`. A proposta v1 recebeu revisão Kimi;
sete achados linguísticos confirmados originaram a v2. Validação mecânica e
unanimidade do painel ADR-020 congelaram o corpus canônico.

O incremento posterior implementou o harness stdlib-only em TDD. Ele projeta os
dois ouros, valida envelopes/partições, MWT, `SpaceAfter=No`, heads, shape e
abstenção, e pontua somente outputs precomputados. Três projeções de cada corpus
produziram hashes idênticos. Maritaca, Grok e Kimi 2.7 aprovaram o snapshot
final sem findings; manifesto e cadeia de custódia estão em
`docs/hermes-pt4-harness-v1.md` e `artifacts/hermes/pt4-harness/`.

O incremento seguinte implementou o adapter experimental spaCy fora do caminho
de produto, em TDD. Ele reduz o ouro a entradas model-blind, preserva o schema
estrito, bloqueia rede e falha fechado; Maritaca, Grok e Kimi 2.7 aprovaram o
snapshot final sem findings. Evidência em
`docs/hermes-pt4-spacy-adapter-v1.md` e
`artifacts/hermes/pt4-spacy-adapter/`.

Nenhuma saída candidata ou inferência foi produzida. O próximo WIP é a primeira
execução controlada e o selamento dos outputs. Seleção de backend, porta de
produto e PT5 continuam fechadas.

## Sources

[1] https://universaldependencies.org/treebanks/pt_petrogold/index.html — UD Portuguese PetroGold
[2] https://universaldependencies.org/format.html — CoNLL-U format
[3] https://universaldependencies.org/misc.html — token-level `SpaceAfter=No`
