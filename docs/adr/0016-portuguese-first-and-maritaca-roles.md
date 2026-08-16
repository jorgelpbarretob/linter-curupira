# ADR-016: produto português-first e papéis separados da Maritaca

Status: Accepted, amended by ADR-020
Date: 2026-08-13

> Emenda de 2026-08-16: o ADR-020 substitui revisão/adjudicação humana
> prospectiva por unanimidade de `sabia-4-thinking`, Grok e Kimi 2.7, com UAT
> da Himavai. Os papéis separados de motor e avaliador Maritaca permanecem.

## Contexto

O repositório foi construído originalmente como um linter de Simplified
Technical English. A avaliação de produto da Rodada 2 confirmou que partes do
núcleo são reaproveitáveis, mas as regras inglesas continuam `preview`, o
holdout foi consumido e os detectores de sentença apresentaram recall baixo.

O mantenedor decidiu encerrar a evolução em inglês e construir um projeto open
source nativo para português brasileiro. A oportunidade não é traduzir a
ASD-STE100 nem manter dois perfis: é publicar uma especificação autoral de
português técnico controlado, seu catálogo de regras, corpus e metodologia de
avaliação.

O projeto também precisa separar o modelo que produz diagnósticos semânticos do
modelo mais caro usado para avaliá-los. Sem essa separação, custo, latência,
risco de autocorreção e interpretação dos resultados ficam misturados.

## Opções consideradas

1. **Manter inglês e adicionar um perfil pt-BR.** Rejeitada porque preserva
   custo de produto, testes e abstrações multilíngues sem uma necessidade
   vigente.
2. **Traduzir regras da ASD-STE100.** Rejeitada por não produzir uma base
   autoral brasileira e por criar riscos de licença, marca e alegações de
   conformidade.
3. **Produto pt-BR-only com núcleo reaproveitado e Maritaca em dois papéis.**
   Aceita por concentrar a proposta de valor e permitir uma ferramenta aberta
   especializada em português brasileiro.

## Decisão

### Escopo do produto

Português brasileiro é a única direção de produto. A implementação, os ADRs,
os corpora e os resultados ingleses ficam congelados como histórico. Não há
gate de paridade com inglês, detecção automática de idioma nem contrato público
multilíngue.

Somente estes componentes são candidatos a migração, depois de testes de
caracterização:

- parser lossless de TXT/Markdown e classificação de markup;
- offsets Unicode e localizações de origem;
- domínio, registry e engine de regras;
- diagnósticos, ordenação, baseline e relatórios;
- composição da CLI e precedência de configuração.

Catálogo, namespace, especificação, vocabulário, corpus, tokenização linguística,
regras e alegações de cobertura serão pt-BR nativos. Nenhum ID `STE-I9-*` será
reutilizado.

### Motor semântico

`sabiazinho-4` será o provider inicial das regras `semantic`. Ele roda
somente com opt-in explícito e aviso de egress. A indisponibilidade do provider
afeta apenas a capacidade semântica solicitada; não altera diagnósticos locais.

A resposta deve obedecer a JSON Schema e conter, no mínimo:

- versão do contrato e ID da regra;
- veredito `emit`, `clear` ou `abstain`;
- spans de evidência mapeáveis ao texto de entrada;
- explicação curta e sugestão opcional;
- indicador de abstenção e razão rastreável.

O provider não implementa regras determinísticas, não promove regras, não
emite `error` e não produz autofix. SDKs da Maritaca ou da OpenAI não atravessam
a porta interna do projeto.

### Avaliação rigorosa

`sabia-4-thinking` será usado somente em desenvolvimento, benchmark e
auditoria. A avaliação tem duas etapas:

1. **julgamento cego:** recebe texto, regra e política de abstenção, sem acesso
   ao diagnóstico ou à justificativa do Sabiazinho;
2. **crítica do candidato:** recebe depois o diagnóstico semântico e aponta
   concordância, erro de regra, erro de span, evidência insuficiente ou caso
   ambíguo.

Os dois modelos pertencem à mesma família e, portanto, não são avaliadores
estatisticamente independentes. Conforme a emenda do ADR-020, o Sabiá Thinking
vota junto de Grok e Kimi 2.7; divergência causa rework e novo ciclo, sem
adjudicação humana.

### Proveniência e reprodutibilidade

Cada chamada registra:

- papel (`semantic-engine` ou `rigorous-evaluator`);
- alias solicitado e identificador de modelo retornado;
- versão e SHA-256 do prompt e do JSON Schema;
- SHA-256 da entrada canônica, sem persistir conteúdo confidencial;
- response ID, data/hora, latência e uso de tokens;
- resultado da validação do schema, retry e erro operacional;
- versão do linter, regra, corpus e protocolo de avaliação.

Alias de modelo pode mudar no provedor. O resultado registra o identificador
retornado e qualquer drift bloqueia comparação longitudinal até revisão. A
adoção futura de um snapshot datado exige avaliação e decisão explícitas.

### Segurança e operação

- Somente o nome `MARITACA_API_KEY` aparece em documentação e configuração; o
  valor fica fora do repositório.
- Documento remoto exige opt-in por execução e pertencer a uma classe de egress
  aprovada. Conteúdo confidencial é recusado por padrão.
- O envio usa o menor span necessário e aplica redação quando compatível com a
  regra.
- Testes públicos usam doubles determinísticos; CI não exige rede nem chave.
- Prompts e schemas dos dois papéis não são compartilhados por conveniência.
- Budget de custo, tokens, timeout, retries e concorrência é obrigatório antes
  do primeiro lote real.

## Consequências

- O produto perde compatibilidade evolutiva com inglês, mas reduz arquitetura,
  catálogo e manutenção desnecessários.
- O lint local continua aberto e reproduzível; recursos semânticos exigem conta,
  credencial e conectividade com a Maritaca.
- O Sabiazinho permite uso semântico de maior volume; o Thinking fica reservado
  ao conjunto cego e a auditorias de maior rigor e custo.
- O uso da API exige revisão de privacidade, retenção, jurisdição contratual e
  classificação documental antes de processar conteúdo real.
- A correlação entre os modelos continua sendo risco residual explícito e será
  acompanhada por divergências do painel e UAT da Himavai.
- ADR-001 e ADR-014 continuam descrevendo a linha inglesa histórica. Suas
  decisões de norma e modelo não se aplicam ao produto pt-BR.

## Gates antes de implementação

- identidade do produto, pacote, comando e namespace aprovados;
- licença do código, especificação, corpus e rótulos aprovada;
- primeira versão da especificação autoral e processo de mudança definidos;
- classes de egress e responsáveis pelo painel e pelo UAT definidos;
- schemas dos dois papéis revisados separadamente;
- custo máximo por documento e por lote pré-registrado;
- credencial nova configurada fora do Git;
- autorização explícita para iniciar TDD.

## Fontes verificadas

- Modelos e aliases: https://docs.maritaca.ai/pt/modelos
- Responses API: https://docs.maritaca.ai/pt/responses-api
- Saídas estruturadas: https://docs.maritaca.ai/pt/structured-outputs
- Preços: https://docs.maritaca.ai/pt/precos
- Compatibilidade de SDK: https://docs.maritaca.ai/pt/api/openai-compatibilidade

Verificado em 2026-08-13.

## Aprovação

Aceito explicitamente pelo mantenedor em 2026-08-13. O mantenedor decidiu:

- abandonar a direção inglesa e construir para português brasileiro;
- usar `sabiazinho-4` como motor semântico do linter;
- usar `sabia-4-thinking` para avaliações mais rigorosas.
