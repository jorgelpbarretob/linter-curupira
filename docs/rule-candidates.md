# Candidatas normativas do MVP

Status: approved-for-fixtures
Approved by: project maintainer, 2026-08-12
Fonte consultada: ASD-STE100 Simplified Technical English, Issue 9, 2025-01-15
Origem: https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf
Consulta: 2026-08-12

Este documento contém locators e paráfrases autorais curtas. Não reproduz
exemplos, tabelas, vocabulário ou texto extenso da norma. Os IDs foram
congelados na Fase 4 após a aprovação do ADR-007.

## Resumo da seleção

| ID | Candidata | Locator Issue 9 | Automação | Estado |
|---|---|---|---|---|
| `STE-I9-PUNCT-001` | Semicolon in lintable prose | Part 1, Section 8, Rule 8.1 | full | preview |
| `STE-I9-SENT-001` | Procedural sentence length | Part 1, Section 5, Rule 5.1; contagem em 8.4–8.7 | full conservador | preview |
| `STE-I9-SENT-002` | Descriptive sentence length | Part 1, Section 6, Rule 6.3; contagem em 8.4–8.7 | full conservador | preview |
| `STE-I9-PARA-001` | Descriptive paragraph length | Part 1, Section 6, Rule 6.6 | full conservador | preview |
| `STE-I9-LIST-001` | Vertical-list lead-in colon | Part 1, Section 4, Rule 4.3 | partial | preview |

Revisão normativa: `approved`, revisor `project-maintainer`, data 2026-08-12.
As labels dos 65 casos sintéticos também foram aprovadas pelo mantenedor. Esse
registro autoriza implementação rastreável; não equivale a aprovação ASD.

## 1. Semicolon in lintable prose

**Paráfrase:** sinalizar ponto e vírgula encontrado em prosa lintável.
**Base do detector:** pure.
**Span:** somente o caractere sinalizado.

Condições de abstenção e controles:

- ignorar code fences, inline code, front matter e destinos de links;
- não interpretar markup ou entidade HTML como prosa;
- manter o texto original para que o span prove o achado;
- sugestão automática fica desabilitada, pois a divisão correta depende do
  significado das duas partes.

Motivo da prioridade: detector lexical simples, com pouco espaço para
interpretação e sem dependência de vocabulário ou NLP.

## 2. Procedural sentence length

**Paráfrase:** em texto declarado como procedural, sinalizar sentença que
permanece acima do limite aplicável depois da contagem STE.
**Base do detector:** parser-dependent.
**Dependências:** segmentação de sentenças, tipo de texto declarado e contador
compatível com Part 1, Section 8, Rules 8.4–8.7.

Condições de abstenção e controles:

- não inferir silenciosamente o tipo do texto;
- notas não usam este detector procedural;
- tratar listas verticais, parênteses, números/unidades, abreviações,
  identificadores, texto citado, nomes próprios e palavras hifenizadas conforme
  as regras de contagem referenciadas;
- se uma construção ambígua puder reduzir a contagem até o limite, abster-se;
- ignorar markup e regiões não lintáveis.

Estado recomendado: `preview` até o parser e o contador passarem pelo corpus
rotulado sem falso positivo.

## 3. Descriptive sentence length

**Paráfrase:** em texto declarado como descritivo, sinalizar sentença que
permanece acima do limite aplicável depois da contagem STE.
**Base do detector:** parser-dependent.
**Dependências:** as mesmas regras de contagem da candidata procedural.

Condições de abstenção e controles:

- exigir tipo de texto declarado ou região de nota reconhecida explicitamente;
- aplicar o mesmo tratamento conservador para construções especiais de
  contagem;
- se o parser não puder delimitar a sentença com segurança, não emitir;
- não contar título, heading, código ou markup como prosa da sentença.

Estado recomendado: `preview` até o gate de precisão.

## 4. Descriptive paragraph length

**Paráfrase:** sinalizar parágrafo descritivo com mais de seis sentenças.
**Base do detector:** parser-dependent.
**Dependências:** parágrafo lossless, segmentação de sentenças e tipo descritivo
declarado.

Condições de abstenção e controles:

- não aplicar a passos de procedimento, headings, tabelas, listas ou código;
- itens de lista não criam parágrafos implícitos;
- se abreviações ou markup impedirem segmentação segura, abster-se;
- o diagnóstico aponta para o parágrafo, sem sugerir uma divisão automática.

Estado recomendado: `preview` até validar Markdown real e o corpus sintético.

## 5. Vertical-list lead-in colon

**Paráfrase:** quando um bloco de lista for claramente continuação de uma frase
introdutória, verificar se essa introdução termina com dois-pontos.
**Base do detector:** parser-dependent.
**Automação:** partial, pois cobre somente uma condição mecânica de Rule 4.3.

Condições de abstenção e controles:

- exigir que o parser reconheça uma lista vertical e uma introdução de prosa
  diretamente associada;
- abster-se para lista independente após heading ou separador estrutural;
- não decidir automaticamente se uma lista é necessária para texto complexo;
- não combinar neste detector requisitos que dependem de saber se cada item é
  uma sentença completa.

Estado recomendado: `preview`; pode sair do primeiro corte se o parser Markdown
não fornecer associação confiável entre introdução e lista.

## Regras deliberadamente adiadas

- **Part 1, Section 5, Rule 5.2:** identificar instruções e simultaneidade exige
  análise linguística ou revisão humana.
- **Part 1, Section 5, Rule 5.3:** reconhecer imperativo com precisão exige NLP.
- **Part 1, Section 6, Rule 6.5:** decidir se um parágrafo tem um único tópico é
  semantic ou human-review.
- **Part 1, Section 8, Rule 8.2:** uso correto de hífen depende da relação
  gramatical e terminológica entre palavras.
- **Vocabulário aprovado:** parte do discurso e significado impedem um detector
  bloqueante simples no primeiro MVP.

## Candidatas propostas para a Fase 6

Duas candidatas NLP foram verificadas na Issue 9 e propostas em
[`docs/f6-candidate-labels.md`](f6-candidate-labels.md):

- `STE-I9-VOICE-001`, Part 1, Section 3, Rule 3.6, detecção conservadora de voz
  passiva com abstenção para a exceção descritiva;
- `STE-I9-NOTE-001`, Part 1, Section 5, Rule 5.5, imperativo em texto declarado
  como nota procedural.

As duas candidatas, seus IDs e as labels sintéticas revisadas foram aprovados
explicitamente pelo mantenedor em 2026-08-12 para implementação `preview/info`.

## Aprovação registrada

O mantenedor confirmou em 2026-08-12 que:

1. estas cinco candidatas são um ponto inicial adequado;
2. regras incertas permanecem `preview` ou se abstêm;
3. nenhum ID definitivo será congelado nesta etapa;
4. exemplos futuros serão sintéticos e escritos para o projeto.

As cinco candidatas foram implementadas como `preview/info` na Fase 4. Nenhuma
foi promovida a `stable`, pois o corpus pequeno não produz intervalo de precisão
suficientemente estreito.
