# Hermes — plano de desenvolvimento do linter pt-BR

Status: PT4 aberto documentalmente; HERMES-PT-PONT-001 permanece `preview`
Base pretendida: especificação autoral e aberta de português técnico controlado
Última revisão: 2026-08-16

> A identidade alvo foi decidida como Hermes, repositório `hermes-STL-IA-PT`,
> pacote `hermes_lint` e comando `hermes`. A distribuição e a CLI já usam essa
> identidade; `src/ste_lint` permanece somente como histórico fora do wheel.

## 0. Direção vigente após o pivot para pt-BR

O mantenedor decidiu em 2026-08-13 encerrar a evolução do produto em inglês e
construir um projeto open source nativo para português brasileiro. O pivot não
é uma tradução da ASD-STE100, não mantém paridade com o inglês e não cria uma
plataforma multilíngue. A linha inglesa fica congelada como evidência histórica;
somente componentes comprovadamente independentes de idioma podem migrar.

As decisões e o roadmap operacionais estão em:

- [`ADR-016`](docs/adr/0016-portuguese-first-and-maritaca-roles.md), que registra
  o produto pt-BR e a separação dos papéis da Maritaca;
- [`ADR-020`](docs/adr/0020-model-panel-and-himavai-uat.md), que substitui gates
  humanos prospectivos pelo painel Maritaca + Grok + Kimi 2.7 e define o UAT da
  Himavai;
- [`docs/pt-br-product-replan.md`](docs/pt-br-product-replan.md), que contém os
  incrementos, gates e critérios de avaliação vigentes;
- [`docs/english-line-closure.md`](docs/english-line-closure.md), que congela o
  estado final da linha inglesa e da Rodada 2.

### Arquitetura de produto decidida

```text
especificação autoral pt-BR + catálogo de regras
                         |
                         v
        núcleo local, determinístico e reproduzível
                         |
             +-----------+-----------+
             |                       |
             v                       v
 análise linguística local   motor semântico remoto
                             sabiazinho-4
                                      |
                                      v
                         painel isolado de validação
                  sabia-4-thinking + grok-4.6 + kimi-k2.7
                                      |
                                      v
                       unanimidade + validação mecânica
                                      |
                                      v
                         UAT de produto pela Himavai
```

O Sabiazinho é o motor das regras `semantic` do linter, nunca a implementação
de regras determinísticas. O Sabiá Thinking é o voto Maritaca de desenvolvimento
e benchmark, não participa do caminho normal de lint. Ground truth novo exige
unanimidade entre Maritaca, Grok e Kimi 2.7, além dos validadores
determinísticos. A Himavai valida a experiência de uso, não rotula corpus.

### WIP vigente

WIP permanece igual a 1. PT1 foi aceito pelo mantenedor em 2026-08-13 e o lado
de corpus de PT2 foi concluído em 2026-08-14. O mantenedor autorizou PT3 em
2026-08-14 com o recorte de contratos independentes de idioma e TDD de
`HERMES-PT-PONT-001`. A implementação, a revisão Grok do código, a regressão
local e o congelamento do detector foram concluídos. Nenhuma execução no
holdout ocorreu antes da autorização explícita separada. A primeira execução e
a avaliação foram concluídas em 2026-08-14; o holdout agora está consumido.

Os artefatos aceitos de PT1 são:

- [`docs/hermes-controlled-portuguese-spec-0.1.md`](docs/hermes-controlled-portuguese-spec-0.1.md);
- [`docs/hermes-governance.md`](docs/hermes-governance.md);
- [`docs/hermes-rule-taxonomy.md`](docs/hermes-rule-taxonomy.md).

Os artefatos propostos de PT2 são:

- [`ADR-018`](docs/adr/0018-corpus-label-and-evaluation-protocol.md);
- [`docs/hermes-annotation-guide-v0.1.md`](docs/hermes-annotation-guide-v0.1.md);
- [`docs/hermes-pt2-corpus-protocol.md`](docs/hermes-pt2-corpus-protocol.md);
- [`corpus/hermes/pont-001-development-proposal.jsonl`](corpus/hermes/pont-001-development-proposal.jsonl).

ADR-018, guia e 40/40 labels foram aceitos em 2026-08-13. O piloto canônico foi
congelado sem executar o detector:
`corpus/hermes/pont-001-development-v1.jsonl`, SHA-256
`51f52007848deaae5169171354d900488df9faedbf073a17a48b14d714703bfc`.
O snapshot pt-BR do Kubernetes, as exclusões e o método de seleção foram
aceitos pelo mantenedor em 2026-08-14. O manifesto auditável foi gerado sem
labels e sem texto externo: 336 ocorrências literais candidatas em 90 arquivos
e 73 documentos de controle, SHA-256
`3eaf4069017593c4f9e0d0c573736899ccbf137e3792ba97161e94d0663f86e7`.
Fonte, contrato, exclusões, seleção e comando de reprodução estão em
[`docs/hermes-pt2-holdout-source-assessment.md`](docs/hermes-pt2-holdout-source-assessment.md).
O pacote histórico de revisão foi preparado fora do repositório com 409 decisões
inicialmente `pending-human-review`, SHA-256 do CSV
`b3fcb6214c5fc2eff295b4b7906d558f00770f1159a079648a64ac081e30fad4`.
Esse estado intermediário foi resolvido pelo protocolo Grok daquele ciclo e não
é gate vigente. Artefatos novos seguem o painel definido no ADR-020.

O mantenedor em seguida autorizou o Grok como revisor delegado. A emenda aceita
para os labels está em
[`docs/hermes-pt2-grok-review-protocol.md`](docs/hermes-pt2-grok-review-protocol.md).
O modelo solicitado `grok-4.6` respondeu como `grok-4.6-build` para 409/409
unidades, sem fila crítica, com prompt/schema e respostas sob custódia separada.
O ground-truth candidato sem texto-fonte foi materializado fora do Git, SHA-256
`6cab9e0a4090df19fc5c3cc5a8e93122413160f523e032367ec25849567abab6`.
O mantenedor aprovou explicitamente esse hash em 2026-08-14. Os mesmos bytes
foram congelados sob custódia externa com 409 registros; labels e texto-fonte
não entraram no Git. Em seguida, PT3 foi autorizado e implementado em TDD. O
pacote `hermes_lint` não importa a linha inglesa, o catálogo expõe somente
`HERMES-PT-PONT-001` e os 36 casos adjudicados do conjunto de desenvolvimento
passam; os quatro casos `ambiguous` continuam fora da asserção. O mantenedor
autorizou o envio isolado dos paths PT3 ao Grok. O parecer estruturado final foi
`approve`, sem achados bloqueantes; um risco residual reproduzível na interação
entre inline code e matemática foi corrigido em TDD antes do congelamento. O
manifesto canônico tem SHA-256
`29bfebaeab126a33d7d0f4aaae44f83d53dd22f03496e30758693d0d9212bae8` e o
detector, SHA-256
`972a1c67e14d4316afc388df523838f4338a60d5866ab13710d19bda1fc016b9`.
Detalhes estão em
[`docs/hermes-pt3-grok-code-review.md`](docs/hermes-pt3-grok-code-review.md).
O mantenedor autorizou a primeira execução isolada e determinou que o Grok
fizesse as aprovações operacionais seguintes sem novas interrupções. A execução
cega foi selada antes da abertura dos labels. O Grok aprovou a abertura e, após
score e auditoria independente, decidiu `preview`: 148 TP, 4 FP, 15 FN e
242 TN; precisão 0,973684; limite inferior Wilson 95% 0,934296; recall
0,907975. O gate Wilson e o gate de zero FP falharam. O relatório canônico está
em
[`docs/hermes-pont-001-holdout-evaluation-v1.md`](docs/hermes-pont-001-holdout-evaluation-v1.md).

O WIP de avaliação de `HERMES-PT-PONT-001` está fechado. Seus 19 erros ficam
selados e o detector não será ajustado com este holdout. Se um rework futuro os
abrir, eles se tornam challenge e uma nova promoção exige outro holdout
independente. A delegação operacional ao Grok está registrada em
[`docs/hermes-governance.md`](docs/hermes-governance.md).

PT4 foi aberto em 2026-08-16 somente no escopo documental. O contrato separa
tokens de superfície de palavras sintáticas, preserva offsets Unicode exatos e
mantém tipos de SDK fora do domínio; o protocolo pré-registra corpora, métricas,
incerteza, gates e desempate antes de qualquer inferência. Nenhum backend foi
escolhido, instalado ou executado. O candidato Stanza continua inelegível até
resolver a licença dos language packs; essa condição não pode ser decidida pelo
Grok. Artefatos:

- [`ADR-019`](docs/adr/0019-local-ptbr-linguistic-analysis.md);
- [`docs/hermes-pt4-bakeoff-protocol.md`](docs/hermes-pt4-bakeoff-protocol.md);
- [`docs/hermes-pt4-grok-opening-review.md`](docs/hermes-pt4-grok-opening-review.md),
  com `approve_with_conditions` e gate `open_pt4_documentation` sobre o bundle
  v2; as condições pré-inferência são vinculantes.

Gate 0 foi aceito com condições em 2026-08-16. O wheelhouse spaCy foi congelado
fora do repositório; manifests, lock, licenças e prova de
carga sem texto estão em
[`artifacts/hermes/pt4-gate0/`](artifacts/hermes/pt4-gate0/) e
[`docs/hermes-pt4-gate0-eligibility-v1.md`](docs/hermes-pt4-gate0-eligibility-v1.md).
O parecer está em
[`docs/hermes-pt4-gate0-grok-review-v1.md`](docs/hermes-pt4-gate0-grok-review-v1.md).
spaCy está `eligible` somente para o bake-off; Stanza está
`ineligible-license` sem aquisição.
Nenhum candidato foi escolhido e nenhuma dependência entrou no produto. O
harness PT4 é o próximo WIP; inferência, adapter e PT5 permanecem fechados até
sua validação.

O WIP=1 de corpora/ambiente materializou PetroGold `r2.18`, fixou o ambiente de
referência e produziu uma proposta autoral com 160 casos, 40 por família. O
estado e os hashes estão em
[`docs/hermes-pt4-corpora-environment-v1.md`](docs/hermes-pt4-corpora-environment-v1.md).
A revisão Kimi da v1 revelou sete inconsistências linguísticas confirmadas pelo
contrato; a proposta v2 corrigiu esses casos sem consultar saída de candidato.
Validação mecânica e Maritaca, Grok e Kimi 2.7 aprovaram 160/160. O corpus
canônico foi congelado com SHA-256
`45716b0581ae7c90897a3d088953ac8efde13882e6c4ef7ecfa87c6764928f5d`.
Não há gate humano. O WIP avança para implementação do harness, ainda sem
inferência.

### Invariantes vigentes

- o linter determinístico continua utilizável offline e sem credenciais;
- semântica remota exige opt-in explícito por execução e aviso de egress;
- `sabiazinho-4` é o único modelo do motor semântico inicial;
- `sabia-4-thinking` é o único modelo do avaliador rigoroso inicial;
- prompts, schemas, credenciais e artefatos dos dois papéis são separados;
- toda resposta registra modelo solicitado/retornado, hashes, response ID,
  tokens, data, latência e estado de validação do schema;
- falha remota não altera nem invalida diagnósticos determinísticos;
- resultado de modelo não é sozinho ground truth, regra normativa ou autofix;
- ground truth novo exige unanimidade Maritaca + Grok + Kimi 2.7 e validação
  mecânica; divergência causa nova versão e novo painel;
- testes de usuário são conduzidos pela Himavai em builds executáveis e não
  substituem corpus ou testes automatizados;
- CI público permanece offline com doubles e fixtures sintéticas sanitizadas;
- nenhuma regra ou ID `STE-I9-*` migra para o catálogo pt-BR.

## Histórico — autoridade do plano inglês e reconciliação com o plano v2

Daqui até o fim deste documento está preservado o plano inglês anterior ao
pivot. Ele serve para rastreabilidade e para identificar contratos candidatos a
reuso, mas não governa novos incrementos de produto. Em caso de divergência,
`ADR-016`, `ADR-020` e o replan pt-BR prevalecem.

Antes do pivot, este `PLANS.md` era o plano operacional vigente. O documento
[`ste-lint-plano-v2-antifragil.md`](ste-lint-plano-v2-antifragil.md) permanece
como insumo arquitetural e histórico, não como um segundo roadmap concorrente.
Quando um gate foi recalibrado, substituído ou adiado, a decisão deve aparecer
explicitamente aqui; “fase concluída” significa que os critérios deste plano
incremental passaram, não que toda proposta do plano v2 original foi entregue.

A reconciliação de 2026-08-13 comparou o plano v2, o código, os testes, os ADRs
e as validações publicadas. Resultado:

| Área do plano v2 | Evidência atual | Estado neste plano |
|---|---|---|
| núcleo offline, contratos imutáveis, spans Unicode e dependências para dentro | domínio, parser, registry, engine, teste de dependências e smoke offline implementados | **atendido** |
| norma e vocabulário fora do repositório | postura de compliance, locators verificados, BYO vocabulary e importação JSON autorizada com hashes | **atendido;** a importação JSON substitui o comando hipotético `ste-dict compile` |
| taxonomia `pure/pos_dependent/nlp/semantic/human` | contrato público usa `deterministic/nlp/semantic/human-review`; capacidades e abstenção ficam separadas | **substituído por ADR-005/008** |
| F4 com 10–15 regras `pure` | cinco regras determinísticas e duas NLP existem, todas `preview/info` e opt-in | **recalibrado para 3–5 determinísticas; evidência de produto ainda aberta** |
| property-based e relações metamórficas | não há Hypothesis nem harness metamórfico geral | **adiado, não entregue** |
| fuzz de 100 mil documentos | há corpus adversarial e limites de tamanho, mas não o gate numérico original | **adiado, não comprovado** |
| mutation score >= 80% | não há mutation testing configurado ou métrica publicada | **adiado, não comprovado** |
| CI mecanizado, bug-to-fixture e ratchet de métricas | a política existe em `AGENTS.md` e falhas observadas geraram regressões, mas não há workflow nem `metrics.lock` | **parcial** |
| baseline para adoção em legado | fingerprint estável, escrita e supressão pós-validação implementadas | **implementado; dogfooding real pendente** |
| NLP pinado e opcional | spaCy/modelo locais pinados, contratos de offset e duas regras conservadoras | **implementado em preview; corpus ainda insuficiente para `stable`** |
| fixer seguro | ADR/spec aceitos e uma candidata passou gates quantitativos; não há provider nem `ste fix` | **bloqueado por promoção e autorização próprias** |
| Semantic Reviewer, cassettes, `models.lock` e drift | nenhum módulo ou harness correspondente existe | **futuro; não iniciado** |
| release com SARIF e dogfooding | CLI, texto, JSON, baseline e `--explain` existem; SARIF e manual real revisado não | **parcial** |

### Histórico: WIP de evidência das regras determinísticas

Antes de implementar fixer, Semantic Reviewer, SARIF ou a derivação pt-BR, o
próximo incremento recomendado é avaliar o produto atual em pelo menos um
manual/corpus técnico real, legalmente utilizável e independente das fixtures de
desenvolvimento. As cinco regras determinísticas serão executadas explicitamente
e suas emissões serão revisadas independentemente com `cursor-agent`; a decisão
humana de promoção permanece um gate separado. A revisão de promoção de
`STE-I9-LIST-001` entra como uma evidência desse fechamento; ela não transforma
o incremento inteiro em trabalho de fixer.

A abertura e o snapshot congelado deste WIP estão registrados em
[`docs/product-evidence-px4-opening.md`](docs/product-evidence-px4-opening.md).
O Cursor concluiu a primeira revisão independente com 23 TP, 1 FP e 1 caso
ambíguo. O FP de fronteira VuePress gerou fixture mínima e correção em TDD. Na
revisão pós-rework, o Cursor confirmou 25 TP, zero FP e 1 caso ambíguo em 26
emissões; todas as regras permanecem `preview` por amostra e recall insuficientes.
A expansão independente está pré-registrada em
[`docs/product-evidence-round-2-plan.md`](docs/product-evidence-round-2-plan.md);
nenhum dos dois novos corpora foi executado pelo linter. O `count-only`
independente está registrado em
[`docs/product-evidence-round-2-count-only.md`](docs/product-evidence-round-2-count-only.md):
quatro tranches ficaram dentro do limite pré-label e `STE-I9-SENT-001` exige
redução determinística revisada pelo Cursor. Após a redução, o inventário
independente gerou 1.173 registros `pending-review` em duas cópias externas
idênticas; a validação está em
[`docs/product-evidence-round-2-inventory-validation.md`](docs/product-evidence-round-2-inventory-validation.md).
A primeira tranche, `STE-I9-PUNCT-001`, teve 69/69 labels pré-execução aceitas
pelo Cursor; o gate está em
[`docs/product-evidence-round-2-punct-label-validation.md`](docs/product-evidence-round-2-punct-label-validation.md).
Após autorização humana, `STE-I9-LIST-001` teve 73/73 labels aceitas, todas
`out_of_scope`; o gate e a ausência de denominador normativo estão registrados
em [`docs/product-evidence-round-2-list-label-validation.md`](docs/product-evidence-round-2-list-label-validation.md).
Após nova autorização humana, `STE-I9-PARA-001` teve 144/144 labels aceitas
depois da adjudicação em TDD de três casos descritivos: 86 `non_violation` e 58
`out_of_scope`. O gate está registrado em
[`docs/product-evidence-round-2-para-label-validation.md`](docs/product-evidence-round-2-para-label-validation.md).
Na tranche seguinte, `STE-I9-SENT-002` teve 329/329 labels aceitas: 15
`violation`, 166 `non_violation`, quatro `ambiguous` e 144 `out_of_scope`. O
gate está registrado em
[`docs/product-evidence-round-2-sent-002-label-validation.md`](docs/product-evidence-round-2-sent-002-label-validation.md).
Na tranche final, `STE-I9-SENT-001` teve 558/558 labels aceitas: 40
`violation`, 200 `non_violation`, oito `ambiguous` e 310 `out_of_scope`. O gate
está registrado em
[`docs/product-evidence-round-2-sent-001-label-validation.md`](docs/product-evidence-round-2-sent-001-label-validation.md).

Definition of Ready:

- fonte, versão, licença e direito de uso do corpus registrados;
- documento não usado para ajustar as regras antes do congelamento;
- política de rótulos, unidade de contagem e responsável pela adjudicação definidos;
- autorização explícita para processar o documento se ele não for público e
  redistribuível;
- nenhuma implementação de regra ou fixer durante a primeira avaliação.

Definition of Done:

- todas as cinco regras determinísticas avaliadas no mesmo snapshot congelado;
- cada emissão classificada como TP, FP ou ambígua, com FP por 1.000 palavras;
- precisão e intervalo Wilson reportados por regra; recall somente quando a
  ground truth cobrir também as não emissões;
- baseline criado e reaplicado sem armazenar conteúdo do documento;
- utilidade, ruído, supressões desejadas e limitações revisados por humano;
- decisão explícita `stable`, `preview` ou `rework` para cada regra, sem promoção
  automática por contagem agregada;
- suíte, Ruff, formato, mypy, smoke offline e scan de conteúdo protegido verdes.

Após esse gate, WIP continua igual a 1: uma regra `stable` pode abrir o primeiro
provider do fixer; ausência de regra promovível retorna ao corpus/detector; valor
de produto comprovado pode priorizar integração da Fase 9. Fases 8 e 10 não
começam por conveniência para contornar falta de evidência determinística.

## 1. Objetivo e limites

Construir em Python um linter local-first para documentos técnicos em inglês:

```text
ste lint document.md
```

O comando deve produzir diagnósticos estáveis e rastreáveis para regras da Issue 9. O produto será uma ajuda à autoria e revisão; não alegará certificação, aprovação pela ASD nem garantia de conformidade integral.

O planejamento e a Fase 1 foram aprovados explicitamente pelo mantenedor em
2026-08-12; autorizações posteriores liberaram as Fases 2 e 3. Os ADRs 007,
008, 009 e 011 foram aprovados no gate da Fase 3; o ADR-010 foi aprovado no
gate da Fase 4. O ADR-013 foi aprovado no gate inicial da Fase 5 após revisão
independente com `cursor-agent` e `composer-2.5-fast`. O ADR-014, as candidatas
NLP, IDs e labels foram aprovados no gate inicial da Fase 6 após duas rodadas
de revisão independente com o mesmo revisor. As fases seguintes continuam
sujeitas aos respectivos gates.

### Restrições inegociáveis

- Issue 9 é a fonte normativa, mas seu conteúdo protegido não entra automaticamente no repositório.
- Um LLM não é fonte normativa, oráculo de compliance nem dependência do núcleo.
- Regras pertencem a exatamente uma classe pública: `deterministic`, `nlp`, `semantic` ou `human-review`.
- O caminho `parse -> lint -> diagnostics` funciona offline.
- Testes positivos, negativos e de borda acompanham cada regra no mesmo incremento.
- A política de produto favorece precisão e abstenção antes de recall.
- O vocabulário oficial e glossários corporativos são recursos versionados separados do código.

## 2. Estado inicial observado

Em 2026-08-12, o diretório contém somente `ste-lint-plano-v2-antifragil.md` e não é um repositório Git. Não existem pacote Python, configuração, catálogo, corpus nem testes. O documento existente foi usado como insumo; este `PLANS.md` é a proposta consolidada e mais enxuta.

Antes da Fase 1, ainda será necessário decidir onde inicializar o repositório e se o nome do diretório com espaço será mantido. O nome de distribuição recomendado é `ste-lint` e o pacote importável, `ste_lint`.

## 3. Premissas desafiadas

1. **“Determinístico” não significa “fácil”.** Regras que dependem de classe gramatical, voz, significado ou tipo textual não devem ser promovidas à classe determinística por conveniência.
2. **O vocabulário não deve ser o primeiro detector.** Sem reconhecer termos técnicos e usos por classe/meaning, um simples teste de lista produz muitos falsos positivos. O MVP útil começa com regras estruturais de alta precisão e aceita um vocabulário local explícito.
3. **Multi-LLM, mutation testing e fuzzing em grande escala não são fundação.** São opções posteriores. Na fundação bastam contratos, exemplos normativos derivados sem copiar texto, testes de unidade e integração offline.
4. **Não se deve prometer extrair automaticamente o PDF oficial.** A ASD distribui a norma em PDF e reserva direitos de reprodução. Importação de material fornecido pelo usuário é uma decisão jurídica e técnica separada; o MVP aceita um recurso estruturado produzido/autorizado pelo usuário.
5. **“Compliance” completo é uma alegação forte demais.** Regras `semantic` e `human-review` impedem que ausência de diagnósticos equivalha a conformidade. A CLI deve dizer “nenhuma violação detectada pelas regras habilitadas”.
6. **Issue 9 precisa estar pinada.** `rule_id` interno não deve depender de numeração que possa mudar em Issue 10. A referência normativa fica em metadados versionados.

## 4. Arquitetura proposta

Arquitetura modular em um único pacote, com dependências apontando para o domínio:

```text
Document source
      |
      v
Parser / source adapter ----> Document + spans + ignored regions
      |                              |
      |                              v
      +----------------------> Rule Engine <---- Rule Catalog
                                     ^              |
                                     |              v
                            Vocabulary Engine   Rule registry
                                     |
                                     v
                                Diagnostics
                                     |
                            text / JSON / SARIF

Later: NLP Engine -> NLP rules
       Fixer boundary -> explicit safe edits
       Semantic Reviewer -> suggestions/review queue only
```

### Módulos previstos

```text
src/ste_lint/
  domain/          modelos imutáveis e contratos
  parsing/         txt e Markdown; offsets preservados
  vocabulary/      portas, loader e lookup de recursos externos
  rules/           implementações por família
  engine/          seleção, execução, ordenação e supressão
  reporting/       text e JSON; SARIF depois
  cli/             composição e códigos de saída
  nlp/             opcional e fora do núcleo inicial
  semantic/        opcional, sem import no caminho offline
  fixer/           providers puros e planejamento; I/O somente na borda CLI
```

O catálogo contém metadados e inventário; a lógica não será uma linguagem declarativa genérica no MVP. Regex simples pode ser dado, mas algoritmos permanecem Python tipado. Isso evita criar prematuramente uma DSL difícil de depurar.

### Fluxo de dependência

- `domain` não conhece CLI, filesystem, bibliotecas NLP nem provedores externos.
- parser, vocabulário e regras implementam contratos consumidos por `engine`.
- CLI compõe adapters; o engine recebe objetos já carregados.
- `semantic` e futuros SDKs são extras opcionais e nunca importados pelo lint padrão.

## 5. Modelo de dados

### Tipos compartilhados

```python
RuleId = NewType("RuleId", str)

class RuleKind(StrEnum):
    DETERMINISTIC = "deterministic"
    NLP = "nlp"
    SEMANTIC = "semantic"
    HUMAN_REVIEW = "human-review"

class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass(frozen=True, slots=True)
class SourceLocation:
    uri: str
    start_offset: int       # offset Unicode no texto normalizado do Document
    end_offset: int         # intervalo semiaberto [start, end)
    start_line: int         # 1-based
    start_column: int       # 1-based, code points
    end_line: int
    end_column: int

@dataclass(frozen=True, slots=True)
class SourceReference:
    standard: str           # "ASD-STE100"
    issue: str              # "9"
    locator: str            # identificador curto validado pelo mantenedor
```

Offsets são a identidade canônica do span; linha/coluna são projeções para apresentação. O parser deve declarar sua política de newline e Unicode e preservar mapeamento ao arquivo original. Bytes não são a unidade pública da API Python.

### Rule

Separar metadados estáveis da implementação evita acoplamento entre catálogo e classes Python:

```python
@dataclass(frozen=True, slots=True)
class RuleMetadata:
    rule_id: RuleId
    title: str
    source: SourceReference
    kind: RuleKind
    default_severity: Severity
    summary: str
    implementation_status: Literal["planned", "preview", "stable"]
    safe_autofix: bool = False

class Rule(Protocol):
    metadata: RuleMetadata

    def check(self, context: RuleContext) -> Iterable["Diagnostic"]: ...
```

`RuleContext` fornece `Document`, configuração, vocabulário e capacidades opcionais. Uma regra não abre arquivos nem chama rede. Regra `human-review` não executa detecção: registra cobertura não automatizada para relatórios de capacidade.

### Diagnostic

```python
@dataclass(frozen=True, slots=True)
class Diagnostic:
    rule_id: RuleId
    source: SourceReference
    severity: Severity
    location: SourceLocation
    message: str
    explanation: str
    suggestion: str | None = None
    evidence: str | None = None
```

Invariantes:

- `rule_id` existe no catálogo e a `source` coincide com a regra.
- `0 <= start_offset < end_offset <= len(document.text)`.
- diagnóstico sempre aponta para texto; casos documentais sem span usam um span específico do documento, nunca coordenadas mágicas.
- ordenação estável: URI, offset inicial, offset final, `rule_id`.
- mensagens não reproduzem longos trechos normativos.
- sugestões sem correção unívoca são omitidas.
- severidade de `semantic` nunca é `error`; achados incertos devem abster-se ou usar `info`.

Campos futuros, fora do contrato mínimo: tags SARIF, `confidence`, `engine`, `related_locations`, edições de fixer e fingerprint de baseline. Serão adicionados de modo compatível quando houver um consumidor real.

## 6. Catálogo de regras

O catálogo é um inventário auditável da Issue 9, não uma cópia da norma. Cada entrada deve ser criada por uma pessoa com acesso legítimo à fonte e passar por revisão normativa.

### Schema mínimo por entrada

```yaml
rule_id: STE-I9-SENT-001
title: Sentence length
source:
  standard: ASD-STE100
  issue: "9"
  locator: "maintainer-verified locator"
kind: deterministic
default_severity: warning
automation: full          # full | partial | none
status: planned           # planned | preview | stable
summary: Short project-authored paraphrase
requires: [parser.sentences, text_type]
false_positive_controls:
  - ignore_code
  - ignore_tables
tests:
  positive: []
  negative: []
  edge: []
```

Os locators exatos e a severidade são deliberadamente `TBD` até revisão da cópia oficial. Não devemos adivinhar numeração ou obrigação normativa a partir de memória, versões anteriores ou sites secundários.

### Famílias propostas

| Família | Exemplos de detectores candidatos | Classe inicial | MVP |
|---|---|---:|---:|
| Estrutura documental | regiões ignoradas, listas, passos e parágrafos | deterministic | suporte, não diagnóstico |
| Comprimento | limite de sentença conforme tipo de texto | deterministic, se tipo declarado | sim |
| Pontuação/formato | padrões proibidos inequívocos; repetição/forma de sinais | deterministic | sim, após revisão |
| Instruções | mais de uma instrução por passo | nlp ou human-review | não |
| Voz e sujeito | voz ativa; sujeito explícito | nlp | não |
| Formas verbais | tempos/formas permitidos | nlp | não |
| Coordenação e complexidade | cláusulas, tópicos e construções complexas | nlp/human-review | não |
| Vocabulário geral | palavra aprovada por parte do discurso e significado | nlp/semantic | não como regra bloqueante no primeiro MVP |
| Palavra inequivocamente desconhecida | token ausente de vocabulário + glossário técnico | deterministic parcial | preview |
| Termos técnicos | technical nouns/verbs e glossário de projeto | deterministic + configuração | sim, como exceção/allowlist |
| Significado aprovado | uso da palavra no meaning permitido | semantic/human-review | não |
| Consistência terminológica | variantes e termos preferidos do projeto | deterministic | sim, regra local não normativa |
| Referências e identificadores | referências internas, part numbers, unidades | deterministic | sim somente quando inequívoco |
| Clareza/contexto técnico | ambiguidade, sequência lógica, adequação | human-review/semantic | não |

O catálogo terá duas namespaces:

- `STE-I9-*`: regra normativa, somente após referência Issue 9 verificada.
- `PROJECT-*`: política local útil, nunca apresentada como requisito ASD-STE100.

Isso impede que convenções internas sejam confundidas com compliance.

## 7. Fases, critérios de aceite e checkpoints

WIP = 1: uma fase por vez; a próxima só começa quando o gate anterior estiver verde ou houver decisão explícita de mudança de escopo.

### Fase 0 — base normativa e produto

Entregáveis: postura de compliance/copyright, ADRs iniciais, schema do catálogo, processo de revisão normativa e 5–8 regras candidatas do MVP com locators verificados.

Aceite:

- acesso legítimo à Issue 9 confirmado pelo mantenedor;
- decisão escrita sobre uso interno, código aberto ou distribuição comercial;
- nenhum conteúdo protegido importado para Git;
- cada candidata classificada e marcada `automation: full|partial|none`;
- exemplos de teste são autorais/sintéticos e revisados, não copiados;
- aprovação humana explícita para iniciar a Fase 1.

Kill/pivot: sem acesso autorizado suficiente para validar regra e vocabulário, o produto vira um linter genérico de estilo técnico sem alegação ASD-STE100.

### Fase 1 — fundação do pacote

Entregáveis: repositório, `pyproject.toml`, layout `src`, modelos do domínio, CLI vazia, pytest, lint e typecheck.

Aceite:

- instalação local reproduzível em Python 3.12+;
- `ste --help` funciona e `ste lint` ainda declara que não há regras estáveis;
- testes de invariantes de `Diagnostic` e registry passam;
- caminho básico roda com rede bloqueada;
- nenhuma dependência NLP/LLM instalada no conjunto base.

### Fase 2 — parser TXT/Markdown

Entregáveis: `Document`, blocos lintáveis, sentences/tokens mínimos e mapa de offsets.

Aceite:

- round-trip do texto original e spans corretos em CRLF/LF, Unicode e arquivo vazio;
- fenced/inline code, links e markup configurado não geram texto lintável indevido;
- testes positivos, negativos e edge para cada construção suportada;
- parser não trava nem lança exceção em corpus adversarial limitado por tamanho;
- `.docx`, HTML e PDF permanecem explicitamente não suportados.

### Fase 3 — engine, catálogo e diagnósticos

Entregáveis: registry, seleção de regras, configuração, supressão explícita, formatador texto e JSON.

Aceite:

- ordem e JSON determinísticos;
- todo diagnóstico satisfaz o contrato de span e referência;
- IDs duplicados ou catálogo divergente falham no startup/teste;
- regra desabilitada não executa;
- erro interno de regra resulta em falha operacional identificável, não em silêncio;
- códigos de saída documentados e testados.

### Fase 4 — MVP utilizável

Entregáveis: 3–5 regras `deterministic` de alta precisão, configuração de tipo textual, glossário técnico local e baseline simples.

Aceite por regra:

- referência Issue 9 verificada por duas pessoas ou por mantenedor + registro de revisão;
- no mínimo 3 testes de violação, 3 de não violação e 3 edge cases;
- zero falso positivo no pequeno corpus limpo inicial;
- precisão estimada >= 0,95 em corpus rotulado, com amostra e intervalo reportados; se amostra insuficiente, regra permanece `preview`;
- nenhuma sugestão quando a correção não for única.

Aceite do produto:

- `ste lint document.md` e `ste lint document.txt` funcionam offline;
- saída humana contém todos os campos requeridos;
- `--format json`, `--rules`, `--explain RULE_ID`, `--config` e `--baseline` funcionam;
- execução em um documento técnico real produz resultado útil revisado por humano;
- documentação diz claramente o subconjunto de regras coberto.

### Fase 5 — Vocabulary Engine confiável

Entregáveis: schema versionado, loader, validação, cache local, overlay de termos técnicos e ferramenta de importação somente para formatos autorizados.

Aceite:

- recurso oficial não é requisito da suíte pública; testes usam vocabulário sintético;
- provenance contém issue, formato/schema e hash do arquivo de entrada, sem armazenar o arquivo protegido;
- arquivo ausente, corrompido ou de issue errada falha com orientação clara;
- lookup é case-aware e preserva part of speech/meaning quando disponíveis;
- regras ambíguas abstêm-se ou degradam para `preview/info`;
- nenhuma release contém o vocabulário oficial sem autorização escrita.

### Fase 6 — NLP

Entregáveis: interface de NLP, modelo pinado/local e primeiras regras `nlp`.

Aceite:

- instalação opcional e núcleo base ainda funciona sem o extra;
- modelo, versão e licença registrados;
- avaliação por regra em corpus do domínio, com precision/recall e matriz de erro;
- cada regra cumpre precisão >= 0,95 para sair de `preview`;
- baixa confiança leva à abstenção, não a diagnóstico categórico.

### Fase 7 — Fixer seguro

Entregáveis: edições estruturadas e `ste fix --check|--apply` somente para correções unívocas.

Contrato aceito em 2026-08-13: [`docs/f7-fixer-spec.md`](docs/f7-fixer-spec.md) e
[`ADR-015`](docs/adr/0015-safe-fixer-contract.md), após duas revisões
independentes. O aceite é somente documental. Implementação e TDD continuam
bloqueados até os gates abaixo. Nenhuma regra atual é elegível: as sete
permanecem `preview` e `safe_autofix = false`.

O gate de evidência do primeiro provider foi executado. As Emendas 1–2 do
[`plano de expansão`](docs/f7-list-evidence-expansion-plan.md) e o primeiro
challenge de 17 labels foram aprovados em 2026-08-13. O suporte `preview` a
exatamente uma linha vazia foi validado por TDD, mas isso não promove a regra e
não autoriza nenhuma implementação do fixer.

A avaliação congelada produziu 13/30 emissões corretas no holdout e
56 emissões corretas combinadas, com zero FP e Wilson inferior 0,936. Os mínimos
de promoção falharam; a regra permanece `preview` e o fixer continua bloqueado.
Resultado: [`docs/f7-list-frozen-evaluation.md`](docs/f7-list-frozen-evaluation.md).

Uma segunda iteração de recall foi autorizada em 2026-08-13. A Emenda 3 trata
os 17 FN consumidos como challenge e exige outro holdout independente antes de
qualquer nova decisão de promoção. Esta autorização não muda os gates do fixer.

O holdout v2 congelado passou com 30 TP, 0 FP, 0 FN e 30 TN. O conjunto
combinado chegou a 104 TP, 0 FP, 9 FN e 82 TN, com Wilson inferior 0,964 e zero
emissões ambíguas. Os gates quantitativos passaram, mas `STE-I9-LIST-001`
permanece `preview/info`: revisão independente e decisão humana de promoção são
gates separados. Resultado:
[`docs/f7-list-recall-v2-validation.md`](docs/f7-list-recall-v2-validation.md).

Aceite:

- preview/diff por padrão e backup antes de `--apply`;
- idempotência;
- edição limitada ao span esperado;
- em runtime, lint após fix remove os diagnósticos alvo e o replanejamento não
  encontra edição elegível; regressões conhecidas de outras regras são gate do
  corpus e da suíte completa;
- regras sem correção inequívoca nunca têm autofix.

Definition of Ready adicional:

- ADR-015 e spec aceitos pelo mantenedor em 2026-08-13;
- uma regra determinística promovida a `stable` com evidência suficiente;
- precondição e substituição exata do primeiro provider aprovadas;
- autorização explícita para iniciar TDD.

### Fase 8 — Semantic Reviewer opcional

Entregáveis: porta de provedor, execução local/remota opt-in, cassettes e sugestões marcadas.

Aceite:

- nenhum segredo ou documento é enviado sem opt-in explícito;
- provedor/modelo/prompt versionados constam do resultado;
- semantic não emite `error` e não altera o veredito determinístico;
- testes do CI usam replay offline;
- avaliação humana documenta precisão e tipos de falha antes de release.

### Fase 9 — formatos e integração

Entregáveis candidatos: SARIF, stdin, diretórios, ignore files, editor/CI e adapters HTML/docx.

Aceite individual por adapter: fidelidade de spans, regiões excluídas explícitas, testes com arquivos reais legalmente redistribuíveis e nenhuma mudança no domínio.

### Fase 10 — superseded: derivação multilíngue para português brasileiro

Esta fase foi substituída pelo pivot pt-BR-only registrado no `ADR-016`. O texto
abaixo permanece somente como histórico do plano anterior.

Objetivo: derivar o linter para português brasileiro, com destino planejado no
projeto `hermes-STL-IA-PT`, reutilizando somente componentes independentes de
idioma. A derivação terá catálogo, corpus, perfil linguístico e alegações de
cobertura próprios; não será apresentada como tradução, certificação ou
conformidade com a ASD-STE100.

A Sabiá será uma capacidade `semantic` remota, opcional e explicitamente
habilitada. Regras locais determinísticas permanecem a autoridade para achados
reprodutíveis. Respostas do modelo serão somente `info`/sugestão para revisão
humana: nunca `error`, fonte normativa, ground truth ou autofix.

Entregáveis propostos:

- ADR para separar o núcleo compartilhado dos perfis `en` e `pt-BR`, sem
  inferência silenciosa do idioma;
- ADR de provedor, privacidade e egress da Sabiá, com porta no módulo
  `semantic` e sem tipo de SDK no domínio;
- especificação autoral de linguagem técnica controlada em pt-BR, taxonomia de
  regras e namespace próprios, sujeitos a revisão de proveniência e licença;
- parser/tokenização pt-BR, corpus legalmente redistribuível e rótulos feitos
  por revisores nativos;
- adapter para a Responses API da Maritaca, atualmente recomendada para novos
  projetos, com modelo, prompt, schema e versão registráveis no resultado;
- avaliação comparativa contra o baseline local, incluindo precisão, recall,
  abstenções, matriz de erros, custo e latência.

Invariantes de segurança e produto:

- o lint padrão continua offline e sem dependência obrigatória de LLM;
- chamadas remotas exigem opt-in explícito por execução e por documento, com
  aviso de egress; documentos confidenciais são recusados por padrão;
- somente o nome `MARITACA_API_KEY` aparece em configuração e documentação; o
  valor fica em variável de ambiente ou secret manager e nunca entra em Git,
  arquivos de configuração, fixtures, cassettes, prompts persistidos ou logs;
- conteúdo enviado é minimizado e redigido quando possível; política de
  retenção, residência de dados e termos do provedor são aprovados antes do
  primeiro uso real;
- CI e testes públicos usam doubles/cassettes sanitizados e permanecem offline;
- indisponibilidade, timeout ou ausência da chave afetam apenas a capacidade
  Sabiá opt-in e produzem falha explícita, sem degradar o lint local;
- nenhum resultado semântico promove regra, altera diagnóstico determinístico
  ou gera edição automaticamente.

Definition of Ready:

- relação, licença e fronteira de código/dados entre este repositório e
  `hermes-STL-IA-PT` decididas;
- nome do produto, namespace das regras e fonte normativa/autoral pt-BR
  aprovados;
- casos de uso, classes de documentos permitidas para egress e responsáveis
  pelo painel de validação e pelo UAT definidos;
- a seleção histórica de modelo foi substituída pelo `ADR-016`; os modelos
  vigentes são `sabiazinho-4` e `sabia-4-thinking`, com papéis separados;
- modelo, prompt, schema estruturado, limites de custo/latência, política de
  redaction e critérios de abstenção documentados e aprovados;
- corpus inicial diverso, redistribuível e rotulado por falantes nativos;
- chave exposta anteriormente revogada/rotacionada; uma nova credencial é
  configurada fora do repositório somente quando os gates anteriores estiverem
  verdes;
- autorização do mantenedor para iniciar o TDD da derivação.

Aceite do primeiro incremento:

- selecionar `pt-BR` é explícito e não muda os resultados do perfil inglês;
- desabilitar o adapter Sabiá restaura exatamente o baseline local;
- nenhum segredo ou conteúdo documental aparece em artefatos, logs ou replay;
- a avaliação reporta incerteza e tipos de falha, sem promoção baseada apenas
  em exemplos sintéticos ou autocorreção do próprio modelo;
- sugestões Sabiá mostram proveniência técnica suficiente para reprodução e
  exigem decisão humana;
- revisão de segurança, privacidade, licença e gate offline aprovados.

Fora do primeiro incremento: tradução integral da ASD-STE100, alegação de
certificação pt-BR, detecção automática de documentos multilíngues, treinamento
ou fine-tuning, uso do LLM como rotulador único e qualquer fixer gerado por LLM.

Referências operacionais consultadas em 2026-08-13:

- [Modelos Sabiá disponíveis](https://docs.maritaca.ai/pt/modelos)
- [Responses API da Maritaca](https://docs.maritaca.ai/pt/responses-api)
- [Compatibilidade com a API da OpenAI e variável de ambiente](https://docs.maritaca.ai/pt/api/openai-compatibilidade)

## 8. Decisões difíceis de alterar depois

Registrar como ADR antes ou durante a Fase 0:

| ADR | Decisão | Recomendação atual |
|---|---|---|
| 001 | identidade da norma e política de referências | `SourceReference(standard, issue, locator)` separada do `rule_id` |
| 002 | modelo de offsets/Unicode/newlines | offsets Unicode semiabertos + mapeamento preservado ao original |
| 003 | fronteira parser/documento | modelo lossless por blocos e regiões ignoradas; adapters externos |
| 004 | contrato público de Rule/Diagnostic | dataclasses imutáveis no domínio; serialização na borda |
| 005 | taxonomia de regras | exatamente as quatro classes pedidas; capacidades internas em campos separados |
| 006 | estratégia de vocabulário | recurso externo versionado + overlays, sem embed no código |
| 007 | namespace/estabilidade de IDs | IDs internos estáveis; issue e locator como metadados |
| 008 | política de severidade e abstenção | erro somente para detecção estável; semantic no máximo info/sugestão |
| 009 | configuração e precedência | defaults < arquivo de projeto < CLI; nada global implícito no MVP |
| 010 | fingerprint de baseline | hash sem offsets frágeis; projetar antes de publicar baseline |
| 011 | compatibilidade de JSON/SARIF | versionar schema desde a primeira saída JSON |
| 012 | postura jurídica e de marca | sem logo, certificação ou “fully compliant”; obter parecer antes de distribuir dados derivados |

## 9. Copyright, licença e marca

Riscos identificados:

- o documento, suas regras, entradas de dicionário e exemplos têm aviso de copyright da ASD;
- acesso gratuito ao PDF não equivale automaticamente a licença para empacotar, transformar ou redistribuir conteúdo;
- o próprio documento enumera direitos especiais para determinadas organizações, o que exige verificar se o projeto/empresa está coberto;
- `ASD-STE100 Simplified Technical English` é marca registrada; nome, documentação e marketing não podem sugerir aprovação;
- uma base de dados extraída do dicionário pode implicar direitos sobre conteúdo e/ou base de dados, mesmo se o código for aberto;
- exemplos copiados para testes, mensagens ou prompts também são redistribuição;
- modelos NLP, corpora e SDKs adicionam licenças próprias e possíveis restrições de dados.

Controles:

- repositório contém somente paráfrases curtas autorais e locators;
- vocabulário oficial fica fora do Git, releases, wheels, imagens e fixtures;
- hashes/provenance podem ser armazenados; o conteúdo-fonte não;
- usuário fornece recursos que tem direito de usar;
- mini-vocabulário de teste é inteiramente sintético;
- termos corporativos ficam em arquivo separado e sob responsabilidade do usuário;
- `NOTICE`, política de marca e parecer jurídico tornam-se gate antes de distribuição pública/comercial;
- solicitações de remoção devem poder desabilitar/remover um pacote de dados sem release de código.

Isto é avaliação arquitetural de risco, não aconselhamento jurídico.

Fontes oficiais consultadas em 2026-08-12:

- [ASD-STE100 Issue 9 — copyright notices](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf)
- [STEMG — solicitação da cópia oficial](https://www.asd-ste100.org/STE_downloads.html)
- [STEMG — orientação sobre ferramentas](https://www.asd-ste100.org/STEsoftware.html)

## 10. MVP mínimo utilizável

O menor produto que entrega valor sem prometer demais é:

- Python 3.12+, pacote instalável e comando `ste lint`;
- entrada `.md` e `.txt` (um arquivo por execução);
- parser que ignora code fences/inline code e preserva localização;
- tipo de texto declarado em configuração, sem inferência silenciosa;
- 3–5 regras determinísticas Issue 9, escolhidas somente depois da Fase 0 pela precisão observada;
- glossário/allowlist local para termos técnicos;
- diagnósticos em texto e JSON com `rule_id`, source, severity, location, explanation e suggestion opcional;
- lista/explicação das regras e indicação clara de cobertura parcial;
- baseline para adoção em documentos legados;
- operação totalmente offline e sem LLM/NLP pesado;
- suíte completa por regra e um pequeno corpus humano revisado.

Não entram no MVP: PDF/docx, autofix, “STE score”, voz passiva baseada em heurística frágil, validação de significado, LLM, dashboard, servidor ou promessa de conformidade completa.

## 11. Definition of Ready para iniciar a Fase 1

- [ ] Este `PLANS.md` aprovado pelo usuário.
- [ ] Uso pretendido (interno, open source, comercial) declarado.
- [ ] Responsável pela revisão da Issue 9 identificado.
- [ ] Estratégia provisória de vocabulário aceita.
- [ ] ADRs 001–006 abertos ou decisões registradas.
- [ ] Diretório/repositório Git escolhido.
- [ ] 3–5 regras candidatas do MVP listadas com locators verificados, sem copiar conteúdo.
- [ ] Corpus inicial legalmente redistribuível definido.

Até todos os itens aplicáveis estarem resolvidos, a Fase 1 não começa.

## 12. Definition of Done global

O objetivo de longo prazo está concluído somente quando o comando funciona nos formatos declarados, o subconjunto de Issue 9 é auditável, cada regra tem evidência de precisão e testes, o core passa offline, recursos normativos têm provenance e licença adequada, e a documentação não faz alegações de certificação ou cobertura além do implementado.
