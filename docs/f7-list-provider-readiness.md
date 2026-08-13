# Readiness do primeiro provider: `STE-I9-LIST-001`

Status: preview-hardening-validated-locally
Data: 2026-08-13
Escopo: endurecimento e avaliação da regra `preview`; nenhum código de fixer
Approved by: project maintainer, 2026-08-13

## Decisão que esta tranche prepara

Decidir se uma subclasse estreita de `STE-I9-LIST-001` pode ser promovida a
`stable` e, depois, sustentar um provider que substitui exatamente o ponto final
diagnosticado por dois-pontos.

Unidade de observação: um documento sintético com uma lista candidata. A verdade
rotulada responde se a linha anterior é realmente o primeiro trecho da lista. A
decisão observável responde se o detector deve emitir 1 ou 0 diagnósticos. Como
o contrato `Rule` não diferencia `clear` de `abstain`, ambos aparecem como zero;
o campo `truth` preserva falsos negativos conservadores.

## Base normativa verificada

Fonte: ASD-STE100 Simplified Technical English, Issue 9, 2025-01-15,
Part 1, Section 4, Rule 4.3, página impressa 1-4-4. Consulta em 2026-08-13:
<https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf>.

Paráfrase autoral curta: quando um trecho introduz uma lista vertical, a
pontuação que separa esse trecho dos itens é dois-pontos. O projeto não reproduz
os exemplos nem o texto extenso da fonte.

Conclusão normativa: `.` → `:` é uma substituição exata somente depois de provar
que o span pertence ao lead-in real da lista. A norma não transforma proximidade
gráfica em associação semântica.

## Falha observada no detector atual

O detector atual procura `these` em qualquer posição da linha imediatamente
anterior. Probes autorais executados pela API pública produziram diagnóstico em
casos nos quais `these` é pronome e a lista contém ações independentes. Exemplo
minimizado: uma frase identifica ferramentas, a frase seguinte manda armazená-las
e a lista subsequente manda fechar um painel e registrar o resultado.

Portanto, o estado atual é **não promovível** e `safe_autofix` deve continuar
`false`. Expandir somente os cinco templates felizes do seed até 73 emissões
criaria pseudo-replicação e não resolveria o falso positivo estrutural.

Na tranche proposta, a regra atual emitiu 10 vezes. Somente 6 dessas emissões
pertencem à política estreita proposta; 4 deveriam abster-se. A precisão de
política provisória é 0,60, com Wilson bilateral de 95% de 0,313 a 0,832. Como
as labels ainda não estavam aprovadas no momento dessa medição pré-TDD, esses
números são diagnóstico histórico de readiness, não métrica oficial da regra.

## Subclasse proposta para o próximo Red/Green

Além dos controles atuais, emitir somente quando:

1. o parser retorna exatamente uma `Sentence` completa, contígua e cujo span
   cobre todo o conteúdo da linha depois de remover whitespace horizontal nas
   bordas;
2. o fim da sentença é `these <head>.`, sem tokens posteriores;
3. `<head>` é um único token alfabético ou hifenizado, plural terminado em `s`;
4. todo o lead-in e o ponto final são lintáveis;
5. a lista Markdown direta contém pelo menos dois itens.

O comportamento validado nesta rodada foi deliberadamente estreito. Multiword
heads, pronome nu, postmodifiers, markup no head, uma linha com duas sentenças e
lista de um item abstêm-se. Naquele baseline, uma linha em branco entre o
lead-in e a lista e marcadores com mais de três espaços ou indentação por tab
também ficavam fora da associação direta. A Emenda 1 do plano de expansão,
aprovada depois deste baseline, autoriza testar exatamente uma linha vazia por
TDD sem alterar as demais barreiras.

## Tranche de labels proposta

[`corpus/f7/vertical-list-provider-readiness.jsonl`](../corpus/f7/vertical-list-provider-readiness.jsonl)
contém 16 casos autorais:

- 6 violações dentro da subclasse, com emissão e replacement `:` esperados;
- 6 controles de abstenção, incluindo 3 violações e 2 ambiguidades
  deliberadamente não emitidas;
- 4 não violações ou casos fora de formato.

O mantenedor aprovou as labels em 2026-08-13. Uma revisão externa somente leitura
com `cursor-agent` e `composer-2.5-fast` não encontrou erro material, confirmou
compatibilidade com as 13 labels seed e deu **YES** para Red/Green incremental
da regra `preview`. A revisão não aprovou fixer, promoção ou `safe_autofix`.

## Contrato quantitativo

Métrica primária: precisão por emissão, `TP / (TP + FP)`, com intervalo Wilson
bilateral de 95%. Gate: precisão pontual >= 0,95, limite inferior >= 0,95 e zero
falso positivo conhecido. Recall e abstenções são reportados, mas não podem ser
otimizados reduzindo a precisão.

Com zero falsos positivos, o limite inferior Wilson alcança 0,95 pela primeira
vez com 73 emissões corretas. O seed aprovado contém 5. A tranche proposta não
serve para promoção: ela valida o contrato do detector antes de expandir a
amostra. Casos derivados de um mesmo template são correlacionados; o Wilson por
linha será reportado por convenção do projeto, mas não prova validade externa.

O cálculo foi rederivado pela fórmula Wilson em Python 3.13.5: o limite inferior
é 0,949348827404 para 72/72 e 0,950007992044 para 73/73. Os comandos previstos
pela skill quantitativa, `prime-quant` e `prime-quant-sync`, não existem neste
host; nenhum pacote ou ambiente do projeto foi alterado para substituí-los.

## Resultado após o Red/Green

O detector `preview` agora exige o terminal lexical estreito e uma sentença
parser-backed que cubra a linha. A tranche F7 passou 16/16 e o seed anterior
passou 13/13.

No conjunto aprovado combinado de 29 casos:

- TP = 11, FP = 0, FN = 3, TN = 9;
- emissões em casos ambíguos = 0; abstenções ambíguas = 6;
- precisão = 1,00, Wilson bilateral de 95% = 0,741–1,000;
- recall = 0,786.

Com zero FP futuro, ainda são necessárias 62 emissões corretas adicionais para
chegar a 73. Um único FP elevaria o mínimo para 110 emissões totais. A regra
permanece `preview/info`, desabilitada por default e com `safe_autofix = false`.
Detalhes reproduzíveis estão em
[`f7-list-detector-validation.md`](f7-list-detector-validation.md).

## Próximo gate

Os quatro primeiros gates foram concluídos em 2026-08-13. A revisão independente
pós-implementação aprovou o endurecimento para commit sem bloqueio material e
reiterou que não aprova promoção, `safe_autofix` ou fixer. O trabalho seguinte é:

1. aprovar e executar o
   [`plano de expansão de evidência`](f7-list-evidence-expansion-plan.md);
2. novo gate humano antes de promoção ou código de fixer.

Nenhum item acima autoriza `FixEdit`, registry de providers, `ste fix` ou
alteração de `safe_autofix`.
