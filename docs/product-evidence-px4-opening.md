# Abertura da evidência de produto — corpus PX4

Data de abertura: 2026-08-13

Status: rework revisado pelo Cursor; regras permanecem `preview`

## Objetivo

Abrir o WIP de evidência de produto definido em `PLANS.md` sem alterar regras,
fixers ou contratos. A primeira execução mede o volume de revisão e congela as
emissões; ela não promove regras e não estima recall.

## Fonte e direito de uso

- produto: PX4 Autopilot User Guide;
- fonte oficial: <https://github.com/PX4/PX4-Autopilot/tree/bb59c637cd74e04c000a0b8e35aac184251150d6/docs>;
- commit: `bb59c637cd74e04c000a0b8e35aac184251150d6`;
- data do commit: `2026-08-13T10:44:03-06:00`;
- licença da documentação: Creative Commons Attribution 4.0 International;
- arquivo de licença: `docs/LICENSE`, SHA-256
  `58b391b218f10970eb9e239bfe3c6a7df57104bbaa3c67335b4666be3ab4686a`;
- titular/projeto atribuído: PX4 Autopilot / Dronecode Foundation;
- conteúdo do corpus: não copiado nem versionado neste repositório.

A CC BY 4.0 permite reprodução, análise e adaptação com atribuição. O relatório
mantém a atribuição e o link para a fonte, e armazena somente metadados de
execução. Marcas do projeto não são usadas para alegar endosso.

## Snapshot e política de texto

O corpus foi escolhido por estrutura antes da primeira execução das regras:

| Subconjunto | Tipo explícito | Escopo | Arquivos | Palavras lintáveis |
|---|---|---|---:|---:|
| montagem | `procedural` | `docs/en/assembly/*.md` | 22 | 14.880 |
| modos de voo multicóptero | `descriptive` | `docs/en/flight_modes_mc/*.md` | 17 | 9.355 |
| total | — | duas árvores congeladas | 39 | 24.235 |

Os totais acima pertencem ao parser pré-rework. Ao ignorar os marcadores
VuePress, o mesmo snapshot passou a conter 14.748 palavras lintáveis no
subconjunto procedural e 9.321 no descritivo, total de 24.069. Nenhuma prosa do
corpus foi removida; a diferença são labels e títulos dos próprios marcadores.

Hashes das árvores Git:

- `docs/en/assembly`: `f8b537b1040e5393b2c659fe4b6acfc7409b5eef`;
- `docs/en/flight_modes_mc`: `db84b314b59f218dffe9eb8d489111759bf77cb3`.

“Palavra lintável” significa token alfabético em região que o parser Markdown
classifica como lintável. Esse denominador exclui markup e blocos ignorados e
será usado para FP por 1.000 palavras depois da adjudicação.

O tipo é aplicado por documento segundo o subconjunto. Se uma emissão ocorrer
num trecho cuja função local conflite com o tipo do documento, o adjudicador
deve registrar essa observação antes de escolher `FP` ou `ambígua`; não se muda
o tipo depois de ver o resultado.

## Política de adjudicação

- unidade: uma emissão identificada por regra, arquivo e linha inicial;
- rótulos permitidos: `TP`, `FP` ou `ambígua`;
- `TP`: a emissão identifica corretamente a condição descrita pelo contrato
  público da regra no tipo de texto declarado;
- `FP`: a condição não existe, o trecho não é prosa aplicável, ou a emissão é
  ruído causado por uma limitação conhecida do detector;
- `ambígua`: a classificação depende de interpretação normativa ou do tipo
  local do trecho e não há base suficiente para decidir com segurança;
- revisor independente: `cursor-agent`, em modo `ask` somente leitura, com
  `composer-2.5-fast`, seguindo o protocolo já adotado nas Fases 5–7;
- decisão humana separada: o mantenedor aceita ou rejeita promoção após receber
  o parecer do Cursor; o revisor não autoriza implementação ou fixer;
- divergências e observações devem ser registradas por emissão;
- não haverá ajuste de detector antes de congelar todas as decisões.

Como não houve rotulagem exaustiva das não emissões, esta rodada mede precisão,
ruído e utilidade. Zero emissão não demonstra recall.

## Sondagem congelada

Versão do linter: commit `6c7003d` deste repositório. As cinco regras
determinísticas foram habilitadas explicitamente. Resultado:

| Regra | Emissões |
|---|---:|
| `STE-I9-LIST-001` | 0 |
| `STE-I9-PARA-001` | 0 |
| `STE-I9-PUNCT-001` | 2 |
| `STE-I9-SENT-001` | 14 |
| `STE-I9-SENT-002` | 9 |
| total | 25 |

As 25 emissões abaixo foram congeladas antes da revisão. As decisões são do
Cursor; o item 13 foi reclassificado em follow-up após reprodução do span.

| # | Regra | Fonte e linha | Evidência | Decisão |
|---:|---|---|---|---|
| 1 | `STE-I9-SENT-001` | `assembly/_assembly.md:66` | 22 palavras; limite 20 | TP |
| 2 | `STE-I9-SENT-001` | `assembly/_assembly.md:83` | 22 palavras; limite 20 | TP |
| 3 | `STE-I9-SENT-001` | `assembly/_assembly.md:129` | 32 palavras; limite 20 | TP |
| 4 | `STE-I9-SENT-001` | `assembly/_assembly.md:235` | 32 palavras; limite 20 | TP |
| 5 | `STE-I9-SENT-001` | `assembly/_assembly.md:301` | 28 palavras; limite 20 | TP |
| 6 | `STE-I9-SENT-001` | `assembly/_assembly.md:340` | 21 palavras; limite 20 | TP |
| 7 | `STE-I9-SENT-001` | `assembly/_assembly.md:370` | 30 palavras; limite 20 | TP |
| 8 | `STE-I9-SENT-001` | `assembly/cable_wiring.md:119` | 22 palavras; limite 20 | TP |
| 9 | `STE-I9-SENT-001` | `assembly/cable_wiring.md:182` | 23 palavras; limite 20 | TP |
| 10 | `STE-I9-SENT-001` | `assembly/mount_and_orient_controller.md:35` | 25 palavras; limite 20 | ambígua |
| 11 | `STE-I9-SENT-001` | `assembly/mount_gps_compass.md:25` | 28 palavras; limite 20 | TP |
| 12 | `STE-I9-PUNCT-001` | `assembly/quick_start_cuav_x25_evo.md:52` | ponto e vírgula | TP |
| 13 | `STE-I9-SENT-001` | `assembly/quick_start_pixhawk.md:66` | span começa em `:::`; 22 palavras | FP |
| 14 | `STE-I9-SENT-001` | `assembly/quick_start_pixhawk4.md:51` | 23 palavras; limite 20 | TP |
| 15 | `STE-I9-SENT-001` | `assembly/vibration_isolation.md:3` | 21 palavras; limite 20 | TP |
| 16 | `STE-I9-SENT-002` | `flight_modes_mc/acro.md:55` | 29 palavras; limite 25 | TP |
| 17 | `STE-I9-PUNCT-001` | `flight_modes_mc/descend.md:42` | ponto e vírgula | TP |
| 18 | `STE-I9-SENT-002` | `flight_modes_mc/follow_me.md:99` | 28 palavras; limite 25 | TP |
| 19 | `STE-I9-SENT-002` | `flight_modes_mc/index.md:3` | 36 palavras; limite 25 | TP |
| 20 | `STE-I9-SENT-002` | `flight_modes_mc/mission.md:107` | 35 palavras; limite 25 | TP |
| 21 | `STE-I9-SENT-002` | `flight_modes_mc/mission.md:218` | 34 palavras; limite 25 | TP |
| 22 | `STE-I9-SENT-002` | `flight_modes_mc/return.md:64` | 32 palavras; limite 25 | TP |
| 23 | `STE-I9-SENT-002` | `flight_modes_mc/throw_launch.md:30` | 27 palavras; limite 25 | TP |
| 24 | `STE-I9-SENT-002` | `flight_modes_mc/throw_launch.md:52` | 28 palavras; limite 25 | TP |
| 25 | `STE-I9-SENT-002` | `flight_modes_mc/throw_launch.md:60` | 28 palavras; limite 25 | TP |

## Revisão independente do Cursor

O `cursor-agent --mode ask --model composer-2.5-fast` revisou as 25 localizações
em modo somente leitura. A primeira rodada marcou 23 TP e 2 ambiguidades. A
reprodução local do item 13 confirmou que o span começa no fechamento VuePress
`:::` da linha 66 e termina na prosa da linha 68. No follow-up, o mesmo revisor
classificou o caso como FP por segmentação não inequívoca e span iniciado em
markup.

Resultado congelado:

| Regra | TP | FP | Ambígua | Decisão técnica |
|---|---:|---:|---:|---|
| `STE-I9-SENT-001` | 12 | 1 | 1 | `rework` |
| `STE-I9-SENT-002` | 9 | 0 | 0 | `preview` |
| `STE-I9-PUNCT-001` | 2 | 0 | 0 | `preview` |
| `STE-I9-LIST-001` | 0 | 0 | 0 | `preview`; evidência insuficiente |
| `STE-I9-PARA-001` | 0 | 0 | 0 | `preview`; evidência insuficiente |
| total | 23 | 1 | 1 | nenhuma promoção |

Métricas pré-rework:

- `STE-I9-SENT-001`, estrita e excluindo ambiguidade: 12/13 = 0,923; Wilson
  95% `[0,667; 0,986]`; 0,067 FP por 1.000 palavras procedurais;
- `STE-I9-SENT-001`, conservadora e contando ambiguidade contra a regra: 12/14
  = 0,857; Wilson 95% `[0,601; 0,960]`;
- `STE-I9-SENT-002`: 9/9 = 1,000; Wilson inferior 0,701;
- `STE-I9-PUNCT-001`: 2/2 = 1,000; Wilson inferior 0,342;
- agregado estrito: 23/24 = 0,958; Wilson inferior 0,798.

O agregado não pode promover uma regra individual. `LIST-001` e `PARA-001` não
têm denominador positivo nesta rodada, e recall continua não mensurável.

## Rework TDD e segunda revisão do Cursor

O FP gerou dois ciclos verticais Red/Green pelo caminho público
`parse_document → Rule.check`:

1. fechamento `:::` seguido de sentença longa: o Red mostrou o diagnóstico no
   offset do marcador; o Green passou após classificar o fechamento como markup;
2. abertura `:::warning` antes de sentença longa: o segundo Red mostrou o mesmo
   defeito; o Green ampliou a classificação para marcadores VuePress de abertura
   e fechamento, mantendo o corpo lintável.

A reexecução do snapshot fez a antiga emissão 13 começar corretamente na linha
68, somente em prosa. Ela revelou também uma emissão legítima antes suprimida em
`assembly/_assembly.md:270`, com 27 palavras. As outras 24 emissões não mudaram.

O Cursor revisou o diff e as duas emissões em modo somente leitura. Considerou a
correção localizada na camada certa, classificou as duas como TP e avaliou como
baixo o risco de overmatch: a expressão exige uma linha composta somente pelo
marcador, tipo opcional e título opcional. Variantes de container ainda não
cobertas são dívida de recall, não autorização para ampliar o escopo agora.

Resultado pós-rework:

| Regra | TP | FP | Ambígua | Decisão técnica |
|---|---:|---:|---:|---|
| `STE-I9-SENT-001` | 14 | 0 | 1 | `preview` |
| `STE-I9-SENT-002` | 9 | 0 | 0 | `preview` |
| `STE-I9-PUNCT-001` | 2 | 0 | 0 | `preview` |
| `STE-I9-LIST-001` | 0 | 0 | 0 | `preview`; evidência insuficiente |
| `STE-I9-PARA-001` | 0 | 0 | 0 | `preview`; evidência insuficiente |
| total | 25 | 0 | 1 | nenhuma promoção |

Métricas pós-rework:

- `STE-I9-SENT-001`, estrita: 14/14 = 1,000; Wilson 95%
  `[0,785; 1,000]`; zero FP por 1.000 palavras procedurais;
- `STE-I9-SENT-001`, conservadora: 14/15 = 0,933; Wilson 95%
  `[0,702; 0,988]`;
- `STE-I9-SENT-002`: 9/9 = 1,000; Wilson inferior 0,701;
- `STE-I9-PUNCT-001`: 2/2 = 1,000; Wilson inferior 0,342;
- agregado estrito: 25/25 = 1,000; Wilson inferior 0,867;
- agregado conservador: 25/26 = 0,962; Wilson inferior 0,811.

O Cursor encerrou o `rework` técnico imediato de `STE-I9-SENT-001`, mas não
promoveu regras nem autorizou fixer. O agregado continua sem poder substituir os
gates individuais.

## Baseline e reprodutibilidade

Uma baseline temporária foi criada para cada um dos 39 documentos e reaplicada
com o mesmo tipo e conjunto de regras. Resultado: zero diagnóstico remanescente.
Os arquivos continham somente `schema_version` e fingerprints SHA-256; nenhum
conteúdo do corpus foi armazenado. As baselines ficaram fora do repositório.

O procedimento foi repetido depois do rework: 39 baselines novas e zero
diagnóstico remanescente.

O clone e os resultados temporários também ficaram fora do repositório. Para
reproduzir, faça checkout do commit e das duas árvores acima, execute cada
arquivo com o tipo declarado e habilite somente as regras determinísticas
aplicáveis ao tipo. Saída JSON é a fonte dos metadados desta tabela.

## Candidata PDF rejeitada

Antes deste snapshot, o capítulo 10 do handbook FAA-H-8083-32B foi considerado
por proximidade com manutenção aeronáutica. Ele foi rejeitado para esta rodada
porque a conversão de PDF em texto alterou limites de parágrafo e ordem de
colunas. Executar as regras nesse texto avaliaria o extrator, não o linter. O PDF
não foi incorporado ao repositório.

## Próximo gate de evidência

O rework está concluído, mas o WIP de evidência de produto continua aberto. O
próximo incremento deve ampliar amostras independentes por regra e rotular
também não-emissões suficientes para medir recall. O item ambíguo em bloco
`details` permanece registrado como dívida de política, sem ser convertido em
TP por conveniência. O mantenedor recebe o parecer pós-rework e decide a
continuidade; nenhuma regra está autorizada para `stable` ou fixer nesta rodada.
