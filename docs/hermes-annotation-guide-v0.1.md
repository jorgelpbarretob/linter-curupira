# Guia de anotação Hermes 0.1

Status: Accepted
Date: 2026-08-13
Language: `pt-BR`
License: `CC-BY-4.0`

## Escopo

Este guia governa o lote-piloto de `HERMES-PT-PONT-001`. O anotador julga o
texto e a especificação aceita, sem consultar código, saída do linter ou labels
de outro avaliador.

## Unidade de anotação

Quando há `;`, a unidade é o próprio caractere e seu contexto estrutural. Um
documento pode conter mais de uma unidade. Controles sem `;` verificam emissões
espúrias e têm `expected_diagnostics = 0`.

## Labels

### violation

Use quando um `;` literal pertence a prosa técnica lintável. A relação entre as
orações não muda a label: contraste, sequência, explicação ou coordenação
continuam dentro da proibição autoral.

### non_violation

Use para controle sem `;` em prosa lintável. A qualidade geral do texto não
importa para esta regra; avalie somente seu escopo.

### out_of_scope

Use quando o `;` aparece somente em região que a especificação exclui:

- fenced code ou inline code;
- destino de link ou URL;
- metadado estrutural;
- atributo/markup não apresentado como prosa.

Não use `out_of_scope` como sinônimo de “não gostei da regra”.

### ambiguous

Use quando o texto/markup não permite decidir se o `;` pertence à prosa
lintável sem primeiro fixar um contrato ainda inexistente. Registre a fonte da
ambiguidade. `expected_diagnostics` deve ser `null`.

## Decisão passo a passo

1. Há um `;` literal?
2. Se não, marque `non_violation` como controle.
3. Se sim, ele está inequivocamente em código, URL, destino, metadado ou markup?
4. Se sim, marque `out_of_scope`.
5. A classificação estrutural depende de sintaxe incompleta ou suporte ainda
   não decidido?
6. Se sim, marque `ambiguous`.
7. Caso contrário, marque `violation` para cada ocorrência em prosa.

## Revisão e adjudicação

O revisor confirma `case_id`, texto, formato, domínio, licença, label, contagem
esperada e racional. Discordância não é resolvida por maioria automática: os
revisores registram interpretações e o mantenedor decide se a especificação deve
ser esclarecida, se o caso é ambíguo ou se uma label está errada.

Casos rejeitados permanecem no log de decisão, mas não entram no arquivo
congelado. Nenhuma label muda depois do hash sem nova versão.

## Proibições

- executar ou inspecionar o detector antes do congelamento;
- usar Sabiá/Sabiazinho como anotador único;
- copiar exemplos protegidos;
- aprovar texto sem licença/proveniência;
- transformar caso ambíguo em negativo por conveniência;
- usar racional para esconder informação não presente no texto.

## Aprovação

Guia aceito explicitamente pelo mantenedor em 2026-08-13 para o piloto de
`HERMES-PT-PONT-001`.
