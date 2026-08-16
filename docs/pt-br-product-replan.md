# Replan do produto para português técnico brasileiro

Status: Accepted
Date: 2026-08-13
WIP limit: 1

## Resultado pretendido

Publicar um linter open source nativo para português brasileiro, sustentado por
uma especificação autoral de linguagem técnica controlada, corpus legalmente
redistribuível, regras locais reproduzíveis e análise semântica especializada.

O produto não é tradução da ASD-STE100, não mantém uma edição inglesa e não
promete certificação. A ausência de diagnósticos significa somente que as regras
habilitadas não encontraram ocorrências.

## Fronteiras do sistema

### Núcleo local

Opera offline e contém parser, offsets, catálogo, registry, engine, regras
determinísticas/NLP locais, baseline e relatórios. Seus resultados devem ser
estáveis para a mesma entrada e configuração.

### Motor semântico

Usa exclusivamente `sabiazinho-4` no primeiro incremento. É remoto,
opt-in e limitado às regras `semantic`. Retorna achados estruturados e
rastreáveis; não substitui diagnósticos determinísticos nem gera autofix.

### Avaliador rigoroso

Usa exclusivamente `sabia-4-thinking`. Não roda no lint normal. Aplica
julgamento cego, depois crítica do resultado do motor semântico, e alimenta a
votação isolada com Grok e Kimi 2.7. Unanimidade do painel e validação mecânica
substituem adjudicação humana conforme ADR-020.

## Roadmap vigente

### PT0 — pivot e congelamento inglês — concluído

Entregáveis:

- ADR do pivot e dos papéis Maritaca;
- snapshot final da evidência inglesa;
- plano e instruções do repositório atualizados.

Aceite:

- histórico inglês preservado sem promoção de regras;
- pt-BR declarado como única direção de produto;
- migração de código ainda bloqueada.

### PT1 — identidade, licença e especificação autoral — concluído

Identidade e licenças foram aceitas no `ADR-017`. Especificação `0.1`,
governança, taxonomia e `HERMES-PT-PONT-001` foram aceitas pelo mantenedor em
2026-08-13.

Entregáveis:

- nome do projeto, pacote, comando e namespace de regras;
- licença do código e política de contribuição;
- licença separada para especificação, corpus e rótulos;
- versão `0.1` da especificação autoral de português técnico controlado;
- processo público de proposta, discussão e mudança de regra;
- taxonomia inicial de regras objetivas, NLP e semânticas; a classe histórica
  `human-review` está depreciada para novas regras.

Definition of Ready:

- público e domínios documentais prioritários definidos;
- modelos do painel, responsáveis operacionais e equipe de UAT identificados;
- referências científicas e ferramentas externas classificadas como inspiração,
  dependência, comparador ou fora de escopo.

Definition of Done:

- nenhuma regra depende de texto protegido ou de uma tradução disfarçada;
- cada candidata tem racional, locator autoral e classe de automação;
- identidade e licenças aprovadas pelo mantenedor;
- uma única candidata é escolhida para o próximo WIP.

### PT2 — corpus e protocolo de avaliação — concluído para PONT-001

Progresso: ADR-018, guia e piloto de 40 casos aceitos. O arquivo de
desenvolvimento v1, o manifesto do holdout Kubernetes e os 409 labels sob
custódia separada foram congelados. O detector foi executado uma única vez no
holdout, depois da autorização do mantenedor. O Grok aprovou os gates
operacionais delegados e decidiu `preview` após a avaliação: 148 TP, 4 FP,
15 FN e 242 TN. O holdout está consumido e não será usado para ajuste.

Entregáveis:

- guia de anotação com eixos separados para verdade, detecção e ambiguidade;
- corpus pt-BR nativo, multissetorial e redistribuível;
- conjuntos separados de desenvolvimento, challenge e holdout cego;
- protocolo de painel Maritaca + Grok + Kimi 2.7 e reconciliação determinística;
- métricas pré-registradas por tipo de regra.

Aceite:

- licença e proveniência por documento;
- nenhuma fonte do holdout usada para criar ou ajustar regra;
- labels congeladas e revisadas antes da primeira execução do detector;
- conteúdo confidencial ausente dos artefatos públicos.

### PT3 — migração do núcleo independente de idioma — concluído

Entregáveis:

- testes de caracterização dos contratos reutilizados;
- identidade autoral no `SourceReference` e catálogo;
- configuração e CLI com nomes pt-BR decididos em PT1;
- remoção incremental de imports, defaults e modelos ingleses;
- baseline novo, sem fingerprints `STE-I9-*`.

Aceite:

- parser preserva offsets em Unicode, CRLF/LF e markup suportado;
- CI base e smoke permanecem offline;
- nenhuma regra inglesa aparece no catálogo pt-BR;
- cada remoção possui substituto testado ou decisão explícita de descarte.

### PT4 — análise linguística local pt-BR

Progresso: WIP aberto em 2026-08-16. O ADR-019 define a porta,
as unidades superfície/palavra, a projeção exata de offsets e o isolamento de
falhas. `docs/hermes-pt4-bakeoff-protocol.md` pré-registra candidatos, corpora,
métricas, gates, incerteza e desempate. Gate 0, corpus/ambiente e harness
pré-inferência estão congelados; nenhuma regra PT5 foi aberta.

O ADR-020 removeu o gate humano. A proposta de offsets v2 passou validação
mecânica e recebeu três votos `approve` em 160/160 casos de
`sabia-4-thinking`, `grok-4.6` e `kimi-k2.7-code:cloud`. O corpus canônico tem
SHA-256 `45716b0581ae7c90897a3d088953ac8efde13882e6c4ef7ecfa87c6764928f5d`.
O harness stdlib-only recebeu três votos `approve`, projeta os dois ouros com
hash triplo idêntico e pontua somente outputs precomputados. Nenhuma inferência
foi executada; o adapter experimental spaCy é o próximo WIP.

Entregáveis:

- contrato local para tokenização, sentenças, morfologia e dependências;
- bake-off documentado do pipeline pt-BR;
- modelo e dependências pinados, com licença e checksum;
- corpus específico para spans e fenômenos do português brasileiro.

Aceite:

- runtime não baixa modelos;
- SDK ou tipos do backend não atravessam a porta interna;
- offsets do analisador mapeiam exatamente ao `Document`;
- falha ou ausência da capacidade é explícita e isolada.

### PT5 — primeiro pacote de regras locais

Processo WIP=1 por regra:

1. publicar regra e condições de abstenção;
2. preparar exemplos autorais positivos, negativos e edge;
3. congelar labels aplicáveis;
4. escrever teste falhando;
5. implementar a menor lógica;
6. executar suíte, corpus e análise de erros;
7. aplicar o painel de três modelos e decidir `preview`, `stable`, `rework` ou
   `reject` pelos gates pré-registrados.

Gates mínimos de promoção:

- precisão pontual >= 0,95;
- limite inferior Wilson de 95% >= 0,95;
- zero falso positivo conhecido não adjudicado;
- recall e abstenção publicados, sem gate agregado esconder falha por regra;
- nenhuma sugestão quando a correção não for inequívoca.

### PT6 — motor semântico com `sabiazinho-4`

Entregáveis:

- porta `semantic` sem tipos de SDK no domínio;
- Responses API e JSON Schema validados;
- prompts versionados por regra;
- mapeamento de spans, abstenção e erros operacionais;
- controles de egress, redaction, timeout, retry, concorrência e custo;
- doubles offline e fixtures sintéticas.

Aceite:

- habilitação explícita por execução e documento;
- diagnóstico identifica provider, modelo, prompt e regra;
- schema inválido, timeout e rate limit não viram achado;
- falha remota não altera o resultado local;
- semantic fica no máximo `info` no primeiro release;
- nenhum conteúdo ou segredo aparece em logs, baseline ou cassette público.

### PT7 — avaliação rigorosa com `sabia-4-thinking`

Entregáveis:

- schema de julgamento separado do motor semântico;
- passe cego e passe de crítica;
- matriz motor × Maritaca × Grok × Kimi;
- precisão, recall, abstenção, concordância, span accuracy, custo e latência;
- taxonomia de erros e fila de rework;
- relatório de drift por versão retornada do modelo.

Aceite:

- o passe cego não recebe saída nem rationale do Sabiazinho;
- prompts e schemas não são compartilhados entre produção e avaliação;
- todo desacordo causa rework e novo ciclo isolado dos três modelos;
- promoção exige unanimidade do painel e validadores determinísticos;
- orçamento máximo por lote é aprovado antes da chamada real;
- holdout não é reutilizado após ajuste.

### PT8 — primeira release open source

Entregáveis:

- pacote, CLI, documentação e exemplos pt-BR;
- especificação e catálogo navegáveis;
- benchmark público reproduzível;
- guia de contribuição de regras, corpus e adjudicação;
- SBOM/NOTICE, segurança, privacidade e política de divulgação de limitações.

Aceite:

- instalação base e lint determinístico funcionam sem rede;
- recursos Maritaca são extras claramente documentados;
- nenhuma chave, corpus sem licença ou conteúdo confidencial entra na release;
- alegações de cobertura correspondem exatamente às regras avaliadas;
- release candidata é validada em mais de um domínio técnico brasileiro.
- cenários de uso, documentação e ergonomia são validados pela Himavai em UAT
  separado do ground truth.

## Métricas por camada

| Camada | Métricas primárias |
|---|---|
| parser/núcleo | round-trip, span exato, determinismo, crashes |
| regra local | precisão, Wilson 95%, recall, abstenção, FP/1.000 palavras |
| motor semântico | precisão/recall, abstenção, span accuracy, schema errors, custo e latência |
| painel rigoroso | unanimidade, erro por classe, estabilidade entre execuções e drift |
| produto | UAT Himavai, ruído por documento, cobertura publicada e adoção |

## Riscos que permanecem abertos

- nome, namespace e licença da especificação ainda não foram escolhidos;
- os modelos são serviços remotos e aliases podem mudar;
- processamento remoto exige revisão de retenção, jurisdição e
  confidencialidade;
- Sabiazinho e Sabiá Thinking podem produzir erros correlacionados;
- corpus público pode sub-representar domínios industriais confidenciais;
- a arquitetura existente contém defaults e contratos ingleses que exigem
  migração gradual, não substituição em massa.

## Próximo estado operacional

PT0, PT1 e PT3 estão concluídos; PT2 foi fechado para `HERMES-PT-PONT-001` com
decisão `preview`; PT4 está aberto com WIP=1 para o bake-off local.
O gate documental foi aceito pelo Grok com condições pré-inferência registradas
em `docs/hermes-pt4-grok-opening-review.md`. Nenhuma aprovação rotineira do
mantenedor está pendente. Por delegação
registrada em `docs/hermes-governance.md`, o Grok pode aprovar os gates
operacionais seguintes quando os artefatos forem isolados e auditáveis.

Gate 0, corpora/ambiente e harness v1 estão congelados. spaCy +
`pt_core_news_sm` está `eligible` somente para o bake-off; Stanza está
`ineligible-license` sem download. O harness passou validação mecânica e painel
Maritaca + Grok + Kimi, conforme `docs/hermes-pt4-harness-v1.md`. O próximo WIP
é o adapter experimental spaCy; isso ainda não escolhe backend, não abre porta
de produto nem PT5.

Os 4 FP e 15 FN deste holdout permanecem selados. Uma futura decisão explícita
de `rework` pode movê-los para challenge, mas qualquer nova tentativa de
promoção exigirá outro holdout independente. O próximo incremento implementa o
adapter experimental elegível e continua o bake-off pré-registrado, sem tratar
PONT-001 como `stable`. Licença não resolvida bloqueia somente o candidato
afetado e continua fora da autoridade do Grok.
