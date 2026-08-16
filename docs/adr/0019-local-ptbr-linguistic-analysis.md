# ADR-019: contrato da análise linguística local pt-BR

Status: Accepted
Date: 2026-08-16

## Contexto

PT4 precisa fornecer tokenização, sentenças, morfologia e dependências para
regras locais em português brasileiro sem tornar uma biblioteca de NLP parte do
domínio. A decisão afeta offsets públicos, representação de contrações,
isolamento de dependências e reprodução offline; por isso, deve ser congelada
antes de escolher ou integrar um backend.

O contrato inglês do ADR-014 é somente evidência histórica. Ele separava tipos
do projeto dos tipos do spaCy e rejeitava realinhamento silencioso, mas modelava
apenas uma sequência de tokens. Isso é insuficiente para português: uma unidade
de superfície como uma contração pode corresponder a mais de uma palavra
sintática. O Stanza também distingue `Token` de `Word` justamente nesse caso e
representa as dependências sobre palavras.[6]

## Decisão

### Fronteira da capacidade

Criar futuramente `hermes_lint.linguistics` como capacidade opcional e local.
O módulo será dono dos tipos imutáveis abaixo; os nomes são contratuais, mas a
sintaxe Python é ilustrativa até o incremento de TDD:

```python
class LocalLinguisticBackend(Protocol):
    def analyze(self, text: str) -> LinguisticAnalysis: ...

class SurfaceToken:
    text: str
    start_offset: int
    end_offset: int

class SyntacticWord:
    surface_token_index: int
    lemma: str
    upos: str
    xpos: str | None
    features: tuple[tuple[str, str], ...]
    dependency: str
    head_word_index: int | None
    sentence_index: int

class LinguisticSentence:
    start_offset: int
    end_offset: int
    first_surface_token: int
    past_last_surface_token: int
    first_word: int
    past_last_word: int

class LinguisticAnalysis:
    text: str
    surface_tokens: tuple[SurfaceToken, ...]
    words: tuple[SyntacticWord, ...]
    sentences: tuple[LinguisticSentence, ...]
    backend: str
    backend_version: str
    model: str
    model_version: str
    model_sha256: str
    configuration_sha256: str
```

`SurfaceToken` é a única unidade lexical com span próprio. Cada token deve
satisfazer, sem normalização ou busca aproximada:

```text
analysis.text[start_offset:end_offset] == token.text
```

Os spans são intervalos Unicode semiabertos relativos ao texto exato recebido
e devem ser ordenados e não sobrepostos. Lacunas de whitespace são permitidas.
`SyntacticWord` aponta para um token de superfície; duas ou mais palavras podem
apontar para o mesmo token em expansão de contração. Uma palavra expandida não
inventa span ou substring independentes. Dependências usam índices de palavras
dentro da análise; a raiz é `None`, nunca um índice mágico exposto pelo SDK.

Sentenças contêm intervalos contíguos de tokens e palavras. Seu span é o menor
envelope da primeira à última unidade de superfície, preservando todo caractere
interno. Uma análise é inválida se token, palavra, sentença ou head atravessar
seus limites declarados.

O schema linguístico interno usa UPOS, FEATS e relações de dependência da
Universal Dependencies; `xpos` é informativo e opcional. O contrato não expõe
objetos, enums ou índices nativos do backend.

### Projeção ao `Document`

O coordenador analisa somente o texto exato de um `TextSpan` contíguo e
lintável. O backend recebe `document.text[segment.start:segment.end]` sem
normalizar Unicode, newline, whitespace ou pontuação. O mapeamento ao documento
é exclusivamente:

```text
document_offset = segment.start + analysis_offset
```

Região fragmentada por markup ou conteúdo ignorado não é concatenada. Quando a
regra exigir contexto que atravessa fragmentos, ela se abstém. Nenhum backend
pode mudar `Document`, seus tokens estruturais, regiões ou offsets. A primeira
implementação deve testar LF, CRLF, caracteres combinantes, emoji, aspas,
abreviações, unidades técnicas, contrações e clíticos.

### Ativação e falhas

- instalação base e regras determinísticas continuam sem dependência NLP;
- backend e modelo são importados e carregados de modo lazy somente quando uma
  regra `nlp` explicitamente habilitada exigir a capacidade;
- ausência, versão divergente, checksum divergente ou componente ausente é erro
  operacional, não `Diagnostic` e não abstenção silenciosa;
- erro sobre um segmento é isolado e rastreável, mas uma regra explicitamente
  pedida não pode fingir sucesso parcial;
- runtime não abre rede nem baixa modelo, manifesto, tokenizer ou configuração;
- NER, constituency parsing, language detection e componentes sem consumidor
  são desabilitados;
- execução de referência é CPU; GPU não participa do gate inicial;
- resultado registra versões, hashes e identidade de todos os artefatos que
  podem alterar a análise.

## Candidatos admitidos ao gate de elegibilidade

Nenhum backend é escolhido por este ADR. O bake-off do
`docs/hermes-pt4-bakeoff-protocol.md` compara somente configurações que primeiro
passarem licença, integridade, instalação reproduzível e runtime sem rede.
Sua evidência técnica principal será o treebank pt-BR PetroGold, revisado
manualmente e licenciado sob CC BY-SA 4.0.[9]

### Candidato A — spaCy

- biblioteca: `spacy==3.8.15`, MIT e com suporte publicado a Python 3.12;[3]
- modelo: `pt_core_news_sm==3.8.0`;
- wheel SHA-256:
  `c304fa04db3af73cd08a250feacf560506e15a2ec2469bd1b09f06847f6b455c`;
- modelo CC BY-SA 4.0, treinado a partir de UD Portuguese Bosque v2.8 e
  WikiNER; inclui morphologizer, parser, lemmatizer e segmentação de
  sentenças.[1]

O adapter pode consultar `Token.idx` e os atributos oficiais de morfologia,
dependência, head e início de sentença.[2] `Token.idx` é somente uma pista de
implementação: não estabelece uma bijeção automática entre `spacy.Token` e
`SurfaceToken`. A superfície emitida continua obrigada a satisfazer o slice
Unicode exato; palavras expandidas apenas reutilizam `surface_token_index`. Se
o SDK não permitir essa projeção sem inventar span ou substring, o adapter deve
abster-se ou declarar a capacidade indisponível. O modelo é de notícias e
precisa provar desempenho no domínio técnico; sua licença share-alike exige
atribuição e revisão da forma de distribuição.

### Candidato B — Stanza

- biblioteca: `stanza==1.14.0`, Apache-2.0 e Python 3.12 suportado;[4]
- configuração: pacote português `default_fast`, limitado a `tokenize=bosque`,
  `mwt=bosque`, `lemma=bosque_nocharlm`, `pos=bosque_nocharlm` e
  `depparse=bosque_nocharlm`;
- manifesto upstream `resources_1.14.0.json`, SHA-256 localmente recomputado:
  `4e41c1df152146fa26ed0c006a08feea7a60bb3414bb6d57dbda24ad2e3cb99c`;
- checksums MD5 upstream, respectivamente:
  `5a270fd4df72d7877021aaee2acc616d`,
  `6e7909d03728aca5772d35a127efe2e2`,
  `3f4346596d965b508a8c4fb4e185f86f`,
  `93082695b66c8d8068c2b8fa8907daaf`,
  `889c42b77c7497ba76980ef00b7f13b1`; pretrain `conll17`:
  `d712e2572902749a7614e9ba4afcd91b`.[5]

O adapter deve desligar downloads (`download_method=None`) e usar somente um
diretório de recursos preparado e verificado antes da execução.[7] A
documentação oficial alerta que os direitos dos language packs treinados sobre
UD não são inteiramente claros e oferece ODC-By apenas na extensão dos direitos
da universidade.[8] Portanto, o candidato B permanece **condicional**: a
divergência entre licença do código, do repositório de modelos e dos dados de
treino deve ser resolvida por um registro de licença antes de baixar ou executar
os pesos. O Grok não tem autoridade para resolver esse gate.

### Alternativas não admitidas nesta rodada

- `pt_core_news_md`/`lg`: não entram inicialmente porque vetores não são uma
  capacidade requerida e ampliariam footprint sem hipótese pré-registrada;
- Trankit: oferece as capacidades necessárias e código Apache-2.0, mas o
  projeto ainda orienta instalação a partir do source por problema de servidor
  e baixa modelos durante a inicialização.[11] Pode voltar em nova versão do
  protocolo, com instalação e cache offline reproduzíveis;
- heurísticas locais: são baseline estrutural, não substituem morfologia e
  dependências avaliadas;
- serviço remoto ou LLM: fora do escopo de PT4 e proibido no bake-off.

## Licença e corpus de treino

A licença declarada do pacote não substitui a licença dos pesos e das fontes de
treinamento. UD Portuguese Bosque contém variedades europeia e brasileira,
gênero de notícias e licença CC BY-SA 4.0.[10] Cada candidato precisa de uma
matriz `código → modelo → dados de treino → redistribuição` antes da aquisição.
Incerteza bloqueia o candidato; não se infere compatibilidade por semelhança de
licenças.

## Consequências

- contrações permanecem rastreáveis sem fabricar offsets;
- regras podem consumir uma representação uniforme de sentenças, morfologia e
  dependências;
- o primeiro adapter exige mais tipos que o contrato inglês histórico;
- fragmentos Markdown levam à abstenção conservadora até existir ADR próprio
  para projeção descontínua;
- nenhum backend entra no wheel base nem é escolhido antes do bake-off;
- upgrade de biblioteca, modelo, dados de treino, checksum ou configuração
  exige novo registro e reexecução da evidência aplicável.

## Não decisões

Este ADR não implementa a porta, não adiciona dependência, não baixa modelo,
não cria regra PT5 e não promove `HERMES-PT-PONT-001`. Os 4 FP e 15 FN do
holdout consumido continuam selados.

## Gate de aceite

O gate foi satisfeito em 2026-08-16. O Grok, atuando pela delegação operacional
de `docs/hermes-governance.md`, retornou `approve_with_conditions` e
`open_pt4_documentation` sobre o bundle v2. As condições vinculantes antes de
qualquer inferência e os hashes da execução estão em
`docs/hermes-pt4-grok-opening-review.md`.

A aceitação abre somente o WIP documental. Licença ainda condicional impede
adquirir ou executar o candidato afetado; Gate 0, backend, modelo, dependência,
corpus materializado, TDD da porta e PT5 continuam fechados.

## Sources

[1] https://github.com/explosion/spacy-models/releases/tag/pt_core_news_sm-3.8.0 — spaCy pt_core_news_sm 3.8.0 release
[2] https://spacy.io/api/token — spaCy Token API
[3] https://pypi.org/project/spacy — spaCy PyPI
[4] https://pypi.org/project/stanza — Stanza PyPI
[5] https://raw.githubusercontent.com/stanfordnlp/stanza-resources/main/resources_1.14.0.json — Stanza 1.14.0 resource manifest
[6] https://stanfordnlp.github.io/stanza/data_objects.html — Stanza data objects and annotations
[7] https://stanfordnlp.github.io/stanza/download_models.html — Stanza model download and offline use
[8] https://stanfordnlp.github.io/stanza/performance.html — Stanza model performance and licensing note
[9] https://universaldependencies.org/treebanks/pt_petrogold/index.html — UD Portuguese PetroGold
[10] https://github.com/UniversalDependencies/UD_Portuguese-Bosque — UD Portuguese Bosque
[11] https://github.com/nlp-uoregon/trankit — Trankit repository
