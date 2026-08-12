# ste-lint — plano de desenvolvimento

Status: Fases 1–4 concluídas em 2026-08-12; Fase 5 aguarda aprovação
Base normativa pretendida: ASD-STE100 Simplified Technical English, Issue 9 (2025-01-15)
Última revisão: 2026-08-12

## 1. Objetivo e limites

Construir em Python um linter local-first para documentos técnicos em inglês:

```text
ste lint document.md
```

O comando deve produzir diagnósticos estáveis e rastreáveis para regras da Issue 9. O produto será uma ajuda à autoria e revisão; não alegará certificação, aprovação pela ASD nem garantia de conformidade integral.

O planejamento e a Fase 1 foram aprovados explicitamente pelo mantenedor em
2026-08-12; autorizações posteriores liberaram as Fases 2 e 3. Os ADRs 007,
008, 009 e 011 foram aprovados no gate da Fase 3; o ADR-010 foi aprovado no
gate da Fase 4. As fases seguintes continuam sujeitas aos respectivos gates.

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
       Fixer -> explicit safe edits
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

Aceite:

- preview/diff por padrão e backup antes de `--apply`;
- idempotência;
- edição limitada ao span esperado;
- lint após fix remove o diagnóstico alvo e não cria regressões conhecidas;
- regras sem correção inequívoca nunca têm autofix.

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
