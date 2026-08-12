# ste-lint: Plano v2 (anti-frágil, multi-LLM)

Revisão do plano v1. O esqueleto do v1 permanece (núcleo determinístico offline, LLM na borda, catálogo antes de código, precision antes de recall). O que muda: o projeto passa a ter mecanismos explícitos que convertem falha em patrimônio, testes com múltiplas LLMs ancorados em ground truth humano, e gates numéricos em toda fase.

---

## 0. Delta em relação ao v1

| Status | Item |
|---|---|
| Mantido | Núcleo determinístico offline; LLM só como sugestão (nunca ERROR); catálogo YAML antes de código; interface única Rule/Diagnostic; spans antes de fixer; SARIF; precision > recall |
| Corrigido | Copyright do dicionário vira decisão arquitetural (BYO dictionary), não nota de rodapé; evals saem da Fase 10 e viram fundação (F1) + trilho contínuo; POS tagging reclassificado (não é determinístico); gates ganham números; "STE score" removido do MVP; docx sai do MVP |
| Novo | Taxonomia de determinismo por regra; contratos e invariantes verificados por meta-teste; property-based + metamorphic + fuzzing + mutation testing; harness multi-LLM com anti-circularidade, cassettes e drift job; políticas de CI (Bug-to-Fixture, ratchet); fitness functions arquiteturais; baseline para adoção em docs legados; kill criteria por fase |

---

## 1. Anti-frágil operacionalizado

Robusto resiste ao estressor. Anti-frágil melhora com ele. A diferença não é adjetivo, é mecanismo:

| Mecanismo | Implementação concreta neste projeto |
|---|---|
| Estressor vira ativo | Todo FP, FN ou crash encontrado vira fixture minimizada ANTES do fix ser mergeado (política 10.1). O corpus só cresce, e cresce a partir das falhas. |
| Diversidade redundante | Cinco técnicas de teste independentes (unit, property, fuzz, mutation, eval em corpus) + juízes LLM de vendors distintos. Falhas correlacionadas de uma técnica são pegas por outra. |
| Barbell | Núcleo hiper-conservador (puro, offline, com contratos e asserts em produção) + borda especulativa (sugestões LLM sempre marcadas com engine e confidence). Nada no meio. |
| Opcionalidade | LLM é extra opcional de instalação (`ste-lint[semantic]`); dicionário é fornecido pelo usuário; qualquer peça da borda pode ser removida sem tocar no núcleo. |
| Via negativa | Lista de proibições estruturais (seção 11), várias delas impostas por construção, não por disciplina. |
| Ratchet | Métricas de qualidade gravadas em lockfile; PR que piora qualquer métrica falha. Baseline de diagnostics em docs legados só pode encolher. |

---

## 2. Riscos existenciais e resposta arquitetural

Tratados primeiro porque, se algum deles estiver errado, o resto do plano não importa.

### R1: Licenciamento do dicionário ASD-STE100

O dicionário é propriedade intelectual da ASD e é o coração da Vocabulary Engine. Sem ele o produto não existe; com ele dentro do repositório, existe problema legal. O v1 identificou o risco e não o resolveu.

Resposta (ADR-001): **BYO dictionary**.
- O usuário baixa a cópia oficial gratuita no site da ASD (registro individual).
- `ste-dict compile <fonte>` gera um artefato local (`~/.ste-lint/dict/issue9.bin`) com sha256 e versão da norma embutidos. O artefato nunca entra em repositório nem em release.
- O repositório contém apenas: o schema do dicionário, o compilador e um **mini-dicionário sintético** (palavras inventadas) usado por 100% dos testes. Nenhum teste depende do dicionário real.
- Diagnostics referenciam a norma por seção (`norm_ref: "Part 1, Section 1"`), nunca por texto reproduzido. Isso vale também para docstrings e fixtures.
- Reavaliar licença comercial se o produto sair de uso interno.

### R2: POS tagging probabilístico dentro de regra "determinística"

O STE aprova palavras por classe gramatical e por significado. Logo a regra mais básica de vocabulário depende de um tagger estatístico, e o v1 listou POS entre as técnicas do MVP determinístico. Isso converte silenciosamente regra "certa" em regra com taxa de erro herdada.

Resposta (ADR-002): taxonomia de determinismo no catálogo.

```text
pure           lexical puro, independe de POS
               (ex.: palavra não aprovada em NENHUMA classe)
pos_dependent  depende do tagger; degrada para WARN
               quando a confiança do tagger < limiar
nlp            depende de parsing sintático
semantic       depende de interpretação de significado (LLM)
human          não é seguro automatizar
```

Gate: regras `pos_dependent` só sobem para ERROR depois que o tagger pinado atingir acurácia >= 95% em amostra rotulada do domínio (n >= 500 tokens). Abaixo disso, WARN permanente.

### R3: Segmentação de sentenças e tipo de texto

O limite de sentença do STE difere entre texto procedural e descritivo, e o linter não sabe qual é qual sem ajuda. Abreviações, part numbers, listas, tabelas e markup quebram sentenciadores ingênuos e viram fábrica de falso positivo.

Resposta:
- O modelo de documento separa prosa lintável de markup (code blocks, tabelas e headings não são sentenças).
- Tipo de texto vem de configuração ou front-matter; na ausência, heurística com origem declarada no diagnostic: `text_type: procedural (declared | inferred)`. Incerteza reportada, nunca escondida.
- **docx fora do MVP.** Markdown e txt primeiro; docx entra depois que o modelo de documento estiver estável (a conversão docx -> modelo é um adapter, não muda o núcleo).

### R4: Falso positivo mata adoção

Um manual legado com 4.000 diagnostics bloqueando CI enterra a ferramenta na primeira semana de uso.

Resposta:
- `ste lint --baseline .ste-baseline.json`: snapshot dos diagnostics existentes; CI falha apenas em diagnostics novos (padrão PHPStan/Betterer).
- Ratchet: a contagem do baseline só pode diminuir.
- Supressão inline exige justificativa: `<!-- ste: ignore[STE-VOCAB-001] reason: termo contratual -->`. Supressões são contadas e reportadas: atrito do usuário vira sinal mensurável (política 10.5).

---

## 3. Arquitetura v2 (hexagonal)

Dependency rule: dependências apontam para dentro. `domain` não importa nada das outras camadas; `semantic` é adapter opcional.

```text
        cópia oficial ASD-STE100 (fornecida pelo usuário)
                          │
                   ste-dict compile
                          │
              dict artifact (hash + versão)
                          │ (port: DictionarySource)
                          ▼
  Document ──► Parser ──► Rule Engine ◄── rules/catalog.yaml
                 │             │
                 │      Vocabulary Engine
                 │             │
                 └──────► Diagnostics ──► Baseline filter ──► CLI / JSON / SARIF
                               │
                        Fixer (safe | suggested)
                               │
              Semantic Reviewer (multi-LLM, extra opcional)
                               │ (port: JudgeModel)
                    adapters: vendor A, vendor B, CassetteReplay
```

```text
ste-lint/
├── AGENTS.md                  # contrato neutro entre agentes (bridge files por agente)
├── PLANS.md
├── pyproject.toml             # extras opcionais: [nlp], [semantic]; deps pinadas via lockfile
├── models.lock                # LLMs e tagger com versão pinada
├── docs/
│   ├── adr/                   # MADR v3 (ADR-001..005, seção 12)
│   ├── architecture.md
│   └── compliance-posture.md  # o que o produto NÃO alega
├── src/ste_lint/
│   ├── domain/                # Document, Token, Span, Rule, Diagnostic (puro, zero I/O)
│   ├── application/           # use cases: lint, fix, eval
│   ├── infrastructure/
│   │   ├── dictionary/        # compiler + loaders (BYO)
│   │   ├── tagging/           # adapter do tagger (modelo pinado)
│   │   ├── semantic/          # adapters LLM + cassettes (só instala com extra)
│   │   └── output/            # formatters, baseline
│   └── interfaces/
│       └── cli.py             # Typer
├── rules/catalog.yaml
├── corpus/
│   ├── labeled/               # ground truth humano (inglês)
│   ├── clean/                 # docs sabidamente conformes (mede piso de ruído)
│   └── cassettes/             # record/replay de interações LLM
├── fixtures/synthetic_dict/   # mini-dicionário inventado, usado pelos testes
└── tests/
    ├── unit/  property/  fuzz/  eval/  fitness/
```

Stack: Python 3.11+, pytest, Hypothesis, Ruff, mypy ou pyright, Typer, Pydantic (validação nas bordas), mutmut ou cosmic-ray, import-linter. NLP e SDKs de LLM só nos extras.

---

## 4. Contratos e invariantes do núcleo (negative space)

Borda valida (Pydantic, exceções amigáveis); núcleo confia e assertia. AssertionError não se trata, se investiga. Asserts de domínio ficam em produção.

Invariantes globais, verificadas automaticamente para TODA regra por meta-teste (um teste protege N regras; é o teste que escala):

1. `0 <= d.start < d.end <= len(doc.text)`
2. `doc.text[d.start:d.end] == d.quoted` (o span prova o apontamento)
3. Determinismo do core: mesma entrada produz a mesma lista ordenada de diagnostics. Nenhuma regra do núcleo pode usar rede, relógio ou random sem seed.
4. `rule_id` único e presente no catálogo; `severity` no enum; regra `semantic` nunca emite ERROR.
5. Parser round-trip: a concatenação dos spans (tokens carregam whitespace, modelo lossless) reconstrói o texto original byte a byte.
6. Fixer: idempotente (`fix(fix(x)) == fix(x)`); `lint(fix(x))` não contém diagnostics das regras corrigidas; safe fix nunca altera bytes fora do span reportado.

```python
@pytest.mark.parametrize("rule", registry.all(), ids=lambda r: r.id)
@given(doc=documents())                       # gerador Hypothesis
def test_rule_contract(rule: Rule, doc: Document) -> None:
    """Pós-condições de Rule.check, válidas para qualquer regra e qualquer doc."""
    diags = rule.check(doc)
    for d in diags:
        assert 0 <= d.start < d.end <= len(doc.text), f"span inválido: {d}"
        assert doc.text[d.start:d.end] == d.quoted, f"span não prova o quoted: {d}"
    assert diags == sorted(diags, key=lambda d: (d.start, d.rule_id)), "saída não determinística/ordenada"
```

---

## 5. Fitness functions arquiteturais

Testes que verificam propriedades da arquitetura, rodando no CI como qualquer teste:

| Fitness function | Ferramenta | Verifica |
|---|---|---|
| Dependency rule | import-linter | `domain` não importa `application`, `infrastructure` nem `interfaces`; nada do caminho de lint importa `semantic` |
| Núcleo offline | teste de integração com rede bloqueada (socket guard) | `ste lint` completa sem nenhuma chamada de rede |
| Extra opcional real | job de CI que instala SEM `[semantic]` | suíte do núcleo passa sem SDKs de LLM instalados |
| Nenhum texto da norma no repo | grep gate sobre fixtures/docs | apenas referências por seção, nunca conteúdo |

---

## 6. Camadas de teste

| Camada | Técnica | Oráculo | O que pega | Gate (inicial, calibrável) |
|---|---|---|---|---|
| L0 | unit table-driven, fixtures do catálogo | espec da regra | erro de lógica óbvio | toda regra com >= 5 positivos, >= 5 negativos, >= 3 edge; coverage domain+application >= 90% (piso, não prova) |
| L1 | property-based (Hypothesis) + relações metamórficas | invariantes da seção 4 | bugs não antecipados; resolve o oracle problem parcial | contratos valem para entradas geradas; perfil CI >= 1.000 exemplos por propriedade |
| L2 | fuzzing (unicode arbitrário + mutação de corpus) | "não crasha, não trava" | robustez do parser | 0 crash/hang em 1e5 docs, timeout 2 s/doc; crasher minimizado vira fixture |
| L3 | mutation testing em `domain/` e `rules/` | suíte L0+L1 | testes fracos que passam por acaso | mutation score >= 80%; mutante sobrevivente vira teste novo |
| L4 | golden evals em corpus rotulado + corpus limpo | humano | precision/recall reais por regra; piso de ruído | precision >= 0,95 por regra; <= 1 FP por 1.000 palavras no corpus limpo; recall >= 0,60 aceitável no MVP; ratchet ativo |
| L5 | multi-LLM (seção 7) | humano (ancoragem) | vieses de modelo, drift, casos semânticos | juiz admitido só com kappa >= 0,70 vs humano |

Relações metamórficas (declaradas por regra no catálogo, executadas pelo harness):

- **MR-V1 (isolamento):** em doc sem diagnostics, substituir 1 palavra aprovada por 1 não aprovada produz exatamente +1 diagnostic, da regra de vocabulário, no span certo; nenhum outro diagnostic muda.
- **MR-S1 (localidade):** permutar sentenças de um parágrafo mantém invariantes os diagnostics de regras sentenciais (módulo offsets); apenas regras de parágrafo podem mudar.
- **MR-W1 (whitespace):** variação de espaçamento não altera o conjunto de diagnostics (módulo offsets).
- **MR-C1 (case):** variação de caixa não altera diagnostics de vocabulário onde a norma for case-insensitive; exceções (siglas, technical names) declaradas na regra.

---

## 7. Harness multi-LLM

### 7.1 Princípio anti-circularidade

LLM nunca é ground truth. Usar um modelo para rotular e outro para julgar é medir a régua com a própria régua: modelos compartilham vieses de treino e erram junto. O humano ancora a verdade; os modelos multiplicam a vazão. Concordância entre modelos é evidência fraca; concordância com o humano em amostra de calibração é o critério de admissão.

### 7.2 Papéis (vendors distintos por construção)

| Papel | Quem | Função | Regra |
|---|---|---|---|
| Generator | modelo do vendor A | gera pares contrastivos por regra: sentença violadora + correção mínima conforme (ataca o linter) | saída deduplicada e minimizada antes de entrar na fila |
| Labeler 1 e 2 | modelos dos vendors B e C | rotulam os candidatos às cegas (sem ver a saída do linter nem um do outro) | prompts versionados; temperatura 0 quando disponível |
| Adjudicator | humano | decide TODOS os desacordos + amostra de 5 a 10% dos acordos (auditoria) | única fonte de ground truth |
| Code Reviewer | agente de vendor distinto do executor | revisa PRs do agente implementador | executor != revisor != destilador; encaixa no review-gate/run_skill e no reviewers.yaml já existentes |

Opcional de custo zero: um modelo aberto pequeno rodando local pode entrar como terceiro labeler e como baseline estável de drift. Sem expectativa: ele só é admitido se passar no mesmo gate de kappa dos demais, e em hardware modesto provavelmente não passa. Testar é barato; assumir que funciona não é.

### 7.3 Fluxo de geração adversarial (corpus que cresce sozinho, ancorado)

```text
Generator (vendor A)
      │  pares contrastivos por regra
      ▼
dedup + minimização
      │
      ▼
Labeler 1 (B)   Labeler 2 (C)     [às cegas, em paralelo]
      │               │
      └──── acordo? ──┘
        │           │
       sim         não
        │           │
        ▼           ▼
  weak label   fila humana  ◄── Disagreement-to-Label:
  (amostrado       │            o conflito entre modelos é
   p/ auditoria)   ▼            exatamente onde está a informação
        └────► corpus/labeled/  (só cresce)
```

### 7.4 Avaliação do Semantic Reviewer

- O reviewer roda sobre o corpus rotulado; precision/recall por modelo, por regra. Seleção e peso de juiz por desempenho medido, não por reputação de vendor.
- Runtime (opcional): ensemble de N modelos; unanimidade eleva confidence; divergência rebaixa para INFO ou omite. Saída sempre `STE-SUGGESTION` com `engine` e `confidence`, nunca ERROR.
- Calibração: kappa de Cohen juiz vs humano, por família de regra, em amostra n >= 100 itens. Kappa < 0,70: o juiz não entra para aquela família.

### 7.5 Determinismo, drift e custo

- **Cassettes (record/replay):** toda interação LLM é gravada como JSON, chaveada por `hash(model@version + prompt)`. O CI roda 100% offline contra cassettes: verde/vermelho nunca depende de API viva.
- **Drift job semanal:** reexecuta os prompts ao vivo e difere contra as cassettes. Delta de labels > 5% abre issue automática com o diff. Drift é sinal a investigar, não quebra de build.
- **models.lock:** vendor, model id, versão e data de pin. Trocar modelo é PR com reavaliação de kappa, nunca upgrade silencioso.
- **Custo:** PR roda só cassettes (custo zero); nightly roda subset estratificado ao vivo se habilitado; drift job roda o conjunto completo. Teto de gasto mensal em variável de ambiente; estourou, o job degrada para cassettes e avisa.

### 7.6 Métricas publicadas por build

precision/recall/F1 por regra por engine; kappa por juiz por família; drift delta; top regras suprimidas; tamanho do corpus (deve só crescer); mutation score.

---

## 8. Fases v2 (gates numéricos e kill criteria)

Números marcados como iniciais: calibrar com o primeiro corpus real. O trilho de corpus e evals não é fase, é fluxo contínuo desde F0.

| Fase | Entregável | Gate | Kill / pivot |
|---|---|---|---|
| F0 Espec | catálogo v2 (schema da seção 9) com classificação de determinismo por regra; corpus seed >= 10 exemplos rotulados por regra candidata do MVP; ADR-001 e ADR-002 | catálogo revisado por humano; toda regra com determinism, oracle e MRs declarados | se > 50% das regras caírem em semantic/human, repensar o escopo do produto antes de escrever código |
| F1 Fundação | repo, CI, contratos, meta-testes, harness de eval e fitness functions ANTES da primeira regra | pipeline executa L0-L4 vazio com sucesso; deps pinadas; CI sem rede comprovado | nenhum |
| F2 Parser | modelo de documento md/txt com spans lossless | round-trip 100%; fuzz 1e5 docs sem crash/hang | round-trip falhando em markdown real: reduzir escopo para txt e tratar md como adapter |
| F3 Rule Engine | registry + contratos executados por meta-teste | mutation score >= 80% no engine | nenhum |
| F4 MVP | 10 a 15 regras `pure` | precision >= 0,95 e <= 1 FP/1.000 palavras por regra | regra que não bate o gate fica atrás de `--preview`, não bloqueia release |
| F5 Dicionário | `ste-dict compile` + Vocabulary Engine + mini-dicionário sintético | lookup 100% coberto por testes sintéticos; zero dependência do dicionário real na suíte | compilação da fonte oficial inviável: entrada assistida manual como fallback |
| F6 NLP | tagger pinado + regras `pos_dependent` | acurácia POS >= 95% em amostra de domínio (n >= 500 tokens) | abaixo do gate: regras ficam WARN permanente e o roadmap segue |
| F7 Fixer | safe fixes | idempotência + invariantes da seção 4; zero alteração fora de span | nenhum |
| F8 Semantic Reviewer | ensemble + cassettes + drift job | kappa >= 0,70 vs humano por juiz admitido | nenhum juiz atinge o gate: feature vira experimento interno, não release |
| F9 Release | CLI, JSON, SARIF, `--baseline`, `--explain RULE-ID` | dogfooding em >= 1 manual real do domínio com baseline ativo | nenhum |

---

## 9. Schema do catálogo de regras v2

```yaml
id: STE-VOCAB-001
name: approved-word-check
issue: 9
norm_ref: "Part 1, Section 1"       # referência por seção, nunca texto da norma
category: vocabulary
determinism: pos_dependent           # pure | pos_dependent | nlp | semantic | human
severity: error
degrade_to: warning                  # aplicado quando confiança do tagger < limiar
oracle: human-labeled-corpus
fp_budget: 0.05                      # 1 - precision mínima
fixtures:
  positive: 5
  negative: 5
  edge: 3
metamorphic: [MR-V1, MR-W1, MR-C1]
autofix: suggested                   # none | safe | suggested
status: {implementation: pending, tests: pending, eval: pending}
```

---

## 10. Políticas de CI (curtas e mecanizáveis)

1. **Bug-to-Fixture:** PR de bugfix (FP, FN ou crash) sem fixture nova de regressão é rejeitado; checagem simples: o diff precisa tocar `fixtures/` ou `corpus/`. A fixture entra minimizada.
2. **Disagreement-to-Label:** desacordo entre labelers nunca é descartado; entra na fila humana e a decisão humana entra no corpus.
3. **Metric Ratchet:** precision/recall por regra e mutation score gravados em `metrics.lock`; PR que reduz qualquer valor falha, salvo alteração explícita do lock com justificativa no PR.
4. **Model Pinning:** nenhuma chamada LLM sem versão pinada em `models.lock`; CI offline por construção (fitness function da seção 5).
5. **Suppression Review:** relatório mensal das regras mais suprimidas nos docs lintados; top 3 entram em revisão obrigatória (a regra pode estar errada, não o usuário).

---

## 11. Via negativa (o que é proibido)

- CI não acessa rede; interação LLM só via cassette.
- Nenhuma dependência sem pin em lockfile.
- `domain/` e o caminho de lint não importam `semantic/` nem SDKs de LLM (imposto por import-linter e por extra de instalação).
- Nenhum texto do ASD-STE100 no repositório: nem em fixtures, nem em docstrings, nem em prompts versionados. Referências por seção.
- Nenhum autofix sem teste de idempotência e de contenção no span.
- Nenhuma saída de LLM com severidade ERROR.
- Nenhum score agregado no CLI até existir definição documentada de denominador (o "STE score: 91.4" do v1 sai do MVP: contradiz o próprio aviso do plano sobre não alegar conformidade).
- Nenhum diagnostic sem `quoted` + span verificável.
- Nenhuma promoção de spike direto para produção: se virar produto, refaz com contratos.

---

## 12. ADRs a registrar (MADR v3)

| ADR | Decisão | Alternativa descartada |
|---|---|---|
| 001 | BYO dictionary com compilador local e mini-dicionário sintético para testes | dicionário embarcado (risco legal); negociar licença agora (prematuro para uso interno) |
| 002 | Taxonomia de determinismo com degradação para WARN | tratar POS como determinístico (erro do v1) |
| 003 | Ground truth exclusivamente humano; LLMs como anotadores fracos admitidos por kappa | LLM-as-judge como oráculo (circular) |
| 004 | CI offline com cassettes; drift job separado | CI chamando APIs vivas (flaky, caro, não reproduzível) |
| 005 | md/txt no MVP; docx como adapter posterior | docx no MVP (custo de parsing alto antes do modelo estabilizar) |

---

## 13. Prompt inicial revisado (agent-agnostic)

Contrato durável em `AGENTS.md` neutro, com bridge files por agente. O prompt abaixo funciona para qualquer agente de código (Codex, Claude Code ou outro):

```text
Contexto: construir o ste-lint, linter profissional para ASD-STE100
Simplified Technical English (Issue 9), em Python, arquitetura hexagonal.

Leia AGENTS.md e PLANS.md antes de qualquer ação.

Princípios inegociáveis:

1. ASD-STE100 Issue 9 é a fonte normativa. Nenhum texto da norma entra
   no repositório; apenas referências por seção.
2. O dicionário oficial é fornecido pelo usuário (BYO). O repo contém o
   compilador (ste-dict compile) e um mini-dicionário sintético usado
   por 100% dos testes.
3. LLM nunca é fonte de compliance nem ground truth. Saída de LLM é
   sempre STE-SUGGESTION com engine e confidence, nunca ERROR.
4. Classifique cada regra: pure | pos_dependent | nlp | semantic | human.
   Regras pos_dependent degradam para WARN sob baixa confiança do tagger.
5. O núcleo funciona offline. CI não acessa rede; interações LLM rodam
   contra cassettes gravadas com modelos de versão pinada (models.lock).
6. Todo diagnostic tem: rule_id, norm_ref, severity, span verificável
   (doc.text[start:end] == quoted), explanation e suggestion opcional.
7. O harness de avaliação (corpus rotulado, métricas por regra,
   meta-testes de contrato, property-based, fuzz, mutation, fitness
   functions) é construído ANTES da primeira regra.
8. Toda regra nasce com fixtures (>= 5 positivos, >= 5 negativos,
   >= 3 edge) e relações metamórficas declaradas no catálogo.
9. Otimize precision antes de recall. Gate: precision >= 0,95 por regra
   e <= 1 falso positivo por 1.000 palavras em corpus conforme.
10. Bugfix sem fixture nova de regressão é rejeitado.

Agora:
1. examine o repositório;
2. proponha PLANS.md com as fases F0-F9 e os gates numéricos;
3. proponha o schema do catálogo de regras;
4. liste decisões difíceis de reverter (candidatas a ADR);
5. NÃO implemente nada até o plano ser aprovado.

Questione premissas quando necessário. Prefira soluções determinísticas
simples a chamadas de LLM. Testes fazem parte da implementação, não de
uma etapa posterior.
```

---

## 14. Decisões pendentes (dono: você)

| # | Decisão | Minha recomendação |
|---|---|---|
| 1 | Quem rotula o ground truth (o custo real do projeto está aqui, não no código) | você adjudica só os desacordos; os modelos fazem a triagem; medir horas gastas desde F0 |
| 2 | Orçamento do harness multi-LLM | PR só cassettes; drift job semanal; nightly ao vivo desligado até o corpus justificar |
| 3 | Alvo de falso positivo | precision >= 0,95 e <= 1 FP/1.000 palavras; apertar depois do primeiro dogfooding |
| 4 | docx no MVP | cortar; md/txt primeiro (ADR-005) |

---

## 15. Lacunas declaradas

O que este plano assume sem confirmação, para você validar:

- Uso interno primeiro; distribuição pública mudaria a postura de licenciamento (R1) e a prioridade do SARIF.
- Os manuais alvo são em inglês (STE é uma norma de inglês; o corpus rotulado é em inglês, ainda que a UI e os docs do projeto sejam em português).
- Volume alvo: dezenas de documentos, não milhares; nada aqui foi dimensionado para throughput massivo.
- Os números de gate são chutes educados; a primeira rodada de F4 recalibra todos.
