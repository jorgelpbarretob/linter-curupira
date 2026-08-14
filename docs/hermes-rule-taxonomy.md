# Taxonomia inicial de regras Hermes

Status: Accepted
Date: 2026-08-13
License: `CC-BY-4.0`

## Dimensões independentes

Cada regra registra separadamente:

- **família linguística:** estrutura, pontuação, sentença, procedimento,
  terminologia, referência, lista, número/unidade ou voz/agente;
- **classe de automação:** `deterministic`, `nlp`, `semantic` ou
  `human-review`;
- **estado:** `planned`, `preview` ou `stable` no catálogo executável;
- **decisão de avaliação:** `promote`, `hold`, `rework` ou `reject`;
- **severity:** `info`, `warning` ou `error`, sujeita à política de estabilidade;
- **capacidade requerida:** parser, glossary, NLP local ou provider semântico.

Família não determina tecnologia. Uma regra de terminologia pode ser
determinística com glossário exato ou semântica quando depende de significado.

## Famílias e primeiras candidatas

| Família | Prefixo | Candidata | Classe inicial | Gate específico |
|---|---|---|---|---|
| pontuação | `PONT` | ponto e vírgula em prosa | deterministic | span exato e regiões excluídas |
| sentença | `SENT` | complexidade/comprimento | deterministic | segmentação e threshold por corpus |
| procedimento | `PROC` | uma instrução principal por passo | nlp | ações coordenadas e exceções |
| terminologia | `TERM` | termo preferido consistente | deterministic | glossário e escopo explícitos |
| referência | `REF` | antecedente inequívoco | semantic | abstenção e evidência textual |
| lista | `LIST` | paralelismo entre itens | nlp | função sintática e fragmentos válidos |
| número/unidade | `UNIT` | formato configurado | deterministic | locale, unidade e tolerâncias |
| voz/agente | `VOICE` | agente explícito quando relevante | nlp | passivas legítimas e impessoais |

## Política por classe

### deterministic

Mesma entrada/configuração produz a mesma saída sem rede. A regra publica
algoritmo, unidade de contagem e abstenção. Pode chegar a `warning` ou `error`
somente depois do gate de estabilidade.

### nlp

Usa análise linguística local pinada. O modelo fornece evidência; a regra ainda
define um padrão verificável e rejeita offsets ou parses inconsistentes.

### semantic

Usa `sabiazinho-4` com schema por regra, spans de evidência e veredito
`emit|clear|abstain`. No primeiro release fica `info`, sem autofix e com opt-in
de egress.

### human-review

Registra cobertura deliberadamente não automatizada. Não emite diagnóstico
categórico; aparece no relatório de capacidade e no checklist humano.

## Ferramentas e literatura de referência

NILC-Metrix demonstra que complexidade textual em português brasileiro pode ser
descrita por métricas em múltiplos níveis linguísticos; o Hermes usará essa visão
para desenhar medições, não para importar um score único.[3]

Coh-Metrix-Port será referência histórica de métricas e não dependência: o
repositório declara GPLv3, o que exige uma decisão de licença separada antes de
qualquer reutilização de código.[4]

spaCy é candidato de PT4 para a porta NLP local, sujeito a bake-off, modelo
português pinado e validação de offsets.[5] LanguageTool, que declara suporte a
português e licença LGPL 2.1 ou posterior, será comparador externo, não fonte
normativa nem dependência inicial.[6]

Vale informa o desenho markup-aware e extensível, sem importação de suas regras
ou implementação.[7]

A Maritaca documenta `sabiazinho-4` e `sabia-4-thinking` como aliases aceitos.[8]
A Responses API é a interface recomendada para novos projetos e suporta saída
estruturada por `text.format`.[9] O schema do Hermes respeitará o subconjunto de
JSON Schema documentado pelo provedor.[10]

## Primeira candidata escolhida

`HERMES-PT-PONT-001` é a primeira candidata porque exercita parser, regiões,
offsets, catálogo, engine, reporting e corpus sem exigir NLP, rede ou threshold
estatístico inventado. A escolha autoriza especificação e corpus; não autoriza
implementação antes dos gates PT2–PT3.

## Aprovação

Taxonomia e primeira candidata aceitas explicitamente pelo mantenedor em
2026-08-13.

## Sources

[3] https://arxiv.org/abs/2201.03445 — NILC-Metrix
[4] https://github.com/nilc-nlp/coh-metrix-port — Coh-Metrix-Port
[5] https://github.com/explosion/spaCy — spaCy
[6] https://github.com/languagetool-org/languagetool — LanguageTool
[7] https://github.com/vale-cli/vale — Vale
[8] https://docs.maritaca.ai/pt/modelos — Modelos Maritaca
[9] https://docs.maritaca.ai/pt/responses-api — Responses API Maritaca
[10] https://docs.maritaca.ai/pt/structured-outputs — Saídas estruturadas Maritaca
