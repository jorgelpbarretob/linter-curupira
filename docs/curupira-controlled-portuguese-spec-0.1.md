# Curupira — Especificação de Português Técnico Controlado 0.1

Status: Accepted
Date: 2026-08-13
Language: `pt-BR`
License: `CC-BY-4.0`

## 1. Propósito

Esta especificação autoral define princípios e regras para tornar documentação
técnica em português brasileiro mais clara, consistente e verificável. Ela não
é tradução de outra norma, não certifica documentos e não substitui julgamento
técnico ou linguístico humano.

Os termos **DEVE**, **NÃO DEVE**, **RECOMENDA-SE** e **PODE** indicam,
respectivamente, requisito, proibição, recomendação e permissão dentro do perfil
Curupira. Somente itens com ID `CURUPIRA-PT-*` e status publicado pertencem à
especificação.

## 2. Público e escopo inicial

O perfil `0.1` atende autores e revisores de:

- procedimentos de operação e manutenção;
- manuais de instalação e configuração;
- documentação de software, APIs e infraestrutura;
- instruções de segurança sem substituir normas regulatórias aplicáveis;
- bases de conhecimento e suporte técnico.

O primeiro release aceita texto UTF-8 em Markdown e TXT. PDF, DOCX, conteúdo
multilíngue, tradução automática e certificação ficam fora do escopo inicial.

## 3. Princípios autorais

1. **Ação identificável:** uma instrução informa claramente a ação e, quando
   necessário, o objeto, a condição e o resultado esperado.
2. **Uma decisão por vez:** sentenças e passos evitam acumular condições,
   exceções e ações independentes.
3. **Termo estável:** o mesmo conceito usa o mesmo termo preferido no escopo
   configurado.
4. **Referência explícita:** pronomes, elipses e demonstrativos não devem deixar
   mais de um referente plausível.
5. **Estrutura visível:** listas, passos, avisos, código e prosa são distinguidos
   antes da análise linguística.
6. **Pontuação funcional:** a pontuação separa unidades de informação sem
   compactar instruções independentes.
7. **Abstenção transparente:** quando o linter não possui evidência suficiente,
   ele declara abstenção em vez de inventar um veredito.

## 4. Taxonomia inicial de regras

| ID | Enunciado resumido | Classe | Status 0.1 |
|---|---|---|---|
| `CURUPIRA-PT-PONT-001` | não usar ponto e vírgula em prosa lintável | deterministic | primeira candidata |
| `CURUPIRA-PT-SENT-001` | limitar complexidade/comprimento de sentença | deterministic | limite pendente de corpus |
| `CURUPIRA-PT-PROC-001` | manter uma instrução principal por passo | nlp | planned |
| `CURUPIRA-PT-TERM-001` | usar o termo preferido para o mesmo conceito | deterministic | planned |
| `CURUPIRA-PT-REF-001` | evitar referência com mais de um antecedente plausível | semantic | planned |
| `CURUPIRA-PT-LIST-001` | manter função e forma paralelas em itens da mesma lista | nlp | planned |
| `CURUPIRA-PT-UNIT-001` | aplicar formato configurado de número e unidade | deterministic | planned |
| `CURUPIRA-PT-VOICE-001` | preferir agente explícito quando relevante à execução | nlp | planned |

`planned` e `primeira candidata` não significam regra habilitada. Uma regra só
entra no catálogo executável depois de especificação, corpus, TDD e gate de
avaliação próprios.

## 5. Primeira candidata: CURUPIRA-PT-PONT-001

### Enunciado

Em prosa técnica lintável, o autor **NÃO DEVE** usar o caractere ponto e vírgula
(`;`). Use uma nova sentença, dois-pontos ou uma lista, conforme a relação entre
as informações.

### Racional autoral

O ponto e vírgula frequentemente compacta ações ou condições que podem ser
apresentadas como unidades explícitas. O detector não tenta escolher a
reescrita, porque a alternativa correta depende da relação semântica.

### Escopo detectável

Emite exatamente no span do `;` quando ele pertence a uma região de prosa
lintável. Deve ignorar:

- fenced code e inline code;
- URLs e destinos de link tratados como markup;
- metadados e regiões estruturalmente excluídas;
- conteúdo que o parser não consegue mapear com offset exato.

### Exemplos autorais

Violação:

> Feche a válvula; desligue a bomba.

Forma preferida possível:

> Feche a válvula. Em seguida, desligue a bomba.

Não violação:

> Verifique a pressão e registre o valor.

Edge cases que não devem emitir:

- `chave;valor` quando o trecho está marcado como inline code;
- destino de link `https://example.invalid/?a=1;b=2`;
- `;` dentro de bloco de código.

### Política do diagnóstico

- classe: `deterministic`;
- severidade inicial: `info`;
- status inicial: `preview` somente depois de TDD;
- autofix: não;
- abstenção: região/offset incerto;
- unidade de avaliação: cada ponto e vírgula em prosa lintável.

## 6. Itens deliberadamente não normativos em 0.1

Não há, ainda, limite numérico publicado para comprimento de sentença ou
parágrafo. Um corpus independente deve medir distribuição, erros de segmentação
e utilidade observada antes de qualquer limite.

Não há lista geral de palavras permitidas. Glossários de projeto serão recursos
externos, versionados e configuráveis.

Não há regra categórica de “voz passiva proibida”. O agente pode ser omitido
quando desconhecido, irrelevante ou deliberadamente impessoal; a futura regra
será avaliada no contexto de execução.

## 7. Base de pesquisa, não normativa

NILC-Metrix reúne 200 métricas de diferentes níveis linguísticos para avaliar
complexidade textual em português brasileiro; isso sustenta medir múltiplas
dimensões em vez de reduzir qualidade a uma fórmula única.[3] Coh-Metrix-Port é
uma adaptação para português brasileiro voltada a coesão, coerência e
legibilidade, usada aqui apenas como referência de métricas e história da área,
sem copiar código ou regras.[4]

LanguageTool será comparador de revisão em português, não fonte da
especificação.[6] Vale inspira a separação entre markup e prosa, mas seu catálogo
não será importado.[7]

## 8. Processo de mudança

Mudanças seguem `docs/hermes-governance.md`, com a identidade atualizada pelo
ADR-021. Maritaca, Grok e Kimi executam o painel independente de crítica; o
Himavai executa a jornada de usuário. Uma mudança só avança quando os gates
automatizados aplicáveis passam e a decisão fica registrada. Cada regra mantém
exemplos autorais, condições de abstenção, corpus, matriz de erro e decisão
rastreável. Não existe gate de revisão humana no fluxo Curupira.

## 9. Aprovação

Versão `0.1` aceita explicitamente pelo mantenedor em 2026-08-13. A aprovação
define a regra autoral e abre o planejamento de corpus; não promove regra nem
autoriza implementação.

## Sources

[3] https://arxiv.org/abs/2201.03445 — NILC-Metrix
[4] https://github.com/nilc-nlp/coh-metrix-port — Coh-Metrix-Port
[6] https://github.com/languagetool-org/languagetool — LanguageTool
[7] https://github.com/vale-cli/vale — Vale
