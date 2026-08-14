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
fila de adjudicação humana.

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
- taxonomia inicial de regras objetivas, NLP, semânticas e humanas.

Definition of Ready:

- público e domínios documentais prioritários definidos;
- revisores nativos e responsáveis pela decisão identificados;
- referências científicas e ferramentas externas classificadas como inspiração,
  dependência, comparador ou fora de escopo.

Definition of Done:

- nenhuma regra depende de texto protegido ou de uma tradução disfarçada;
- cada candidata tem racional, locator autoral e classe de automação;
- identidade e licenças aprovadas pelo mantenedor;
- uma única candidata é escolhida para o próximo WIP.

### PT2 — corpus e protocolo de avaliação — WIP vigente

Progresso: ADR-018, guia e piloto de 40 casos aceitos. O arquivo de
desenvolvimento v1 está congelado; challenge e holdout ainda não existem e o
detector não foi executado.

Entregáveis:

- guia de anotação com eixos separados para verdade, detecção e ambiguidade;
- corpus pt-BR nativo, multissetorial e redistribuível;
- conjuntos separados de desenvolvimento, challenge e holdout cego;
- protocolo de adjudicação humana e amostragem dos acordos;
- métricas pré-registradas por tipo de regra.

Aceite:

- licença e proveniência por documento;
- nenhuma fonte do holdout usada para criar ou ajustar regra;
- labels congeladas e revisadas antes da primeira execução do detector;
- conteúdo confidencial ausente dos artefatos públicos.

### PT3 — migração do núcleo independente de idioma

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
7. decidir `preview`, `stable`, `rework` ou `reject`.

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
- matriz humano × motor × avaliador;
- precisão, recall, abstenção, concordância, span accuracy, custo e latência;
- taxonomia de erros e fila de adjudicação;
- relatório de drift por versão retornada do modelo.

Aceite:

- o passe cego não recebe saída nem rationale do Sabiazinho;
- prompts e schemas não são compartilhados entre produção e avaliação;
- todo desacordo e amostra pré-registrada dos acordos recebem decisão humana;
- promoção não usa somente avaliação do modelo;
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

## Métricas por camada

| Camada | Métricas primárias |
|---|---|
| parser/núcleo | round-trip, span exato, determinismo, crashes |
| regra local | precisão, Wilson 95%, recall, abstenção, FP/1.000 palavras |
| motor semântico | precisão/recall, abstenção, span accuracy, schema errors, custo e latência |
| avaliador rigoroso | concordância humana, erro por classe, estabilidade entre execuções e drift |
| produto | utilidade humana, ruído por documento, cobertura publicada e adoção |

## Riscos que permanecem abertos

- nome, namespace e licença da especificação ainda não foram escolhidos;
- os modelos são serviços remotos e aliases podem mudar;
- processamento remoto exige revisão de retenção, jurisdição e
  confidencialidade;
- Sabiazinho e Sabiá Thinking podem produzir erros correlacionados;
- corpus público pode sub-representar domínios industriais confidenciais;
- a arquitetura existente contém defaults e contratos ingleses que exigem
  migração gradual, não substituição em massa.

## Próxima autorização necessária

PT0 e PT1 estão concluídos. PT2 prepara labels sem executar o detector. A
próxima autorização deve aceitar o ADR-018, o guia de anotação e cada label do
lote-piloto; depois disso o arquivo será congelado. Essa aprovação ainda não
autoriza migração de código, que permanece em PT3.
