# Evidência de conclusão da Fase 4

Status: passed
Data: 2026-08-12
Python: CPython 3.12.10
Gerenciador: uv 0.11.14

## Escopo entregue

- cinco regras Issue 9 determinísticas como `preview/info`;
- 65 labels humanas exercitadas por testes de corpus;
- tipo textual explícito em TOML e CLI;
- glossário técnico local preservado no `RuleContext`;
- `--rules` e `--explain RULE_ID`;
- baseline JSON `1.0`, fingerprints sem offsets e gravação atômica;
- avaliação com matriz de erro e intervalo Wilson por regra.

Nenhuma regra foi promovida a `stable`. Nenhum vocabulário oficial, NLP, LLM ou
dependência de runtime foi adicionado.

## TDD observado

1. A regra de ponto e vírgula expôs um falso positivo em entidade HTML; uma
   fixture minimizada levou o parser a ignorar a entidade completa.
2. As regras de sentença começaram sem módulo e passaram após contador
   conservador com abstenção explícita.
3. Parágrafo e lista foram implementados somente para estruturas inequívocas.
4. Configuração, descoberta CLI e baseline começaram em Red por símbolos/opções
   ausentes e foram implementados pelo menor contrato aprovado.
5. O baseline passou testes de estabilidade a inserção anterior, mudança de
   contexto, repetição, JSON estrito e integração CLI atômica.

## Comandos e resultados

| Comando | Resultado |
|---|---|
| `uv --version` | passed; uv 0.11.14 |
| `uv lock --check` | passed; 12 pacotes resolvidos |
| `uv sync --locked` | passed; 12 pacotes verificados |
| `uv run --no-sync python --version` | passed; Python 3.12.10 |
| `uv run --no-sync pytest` | passed; 139 testes em 1,17 s |
| `uv run --no-sync ruff check .` | passed |
| `uv run --no-sync ruff format --check .` | passed; 47 arquivos formatados |
| `uv run --no-sync mypy src` | passed; 22 arquivos |
| `uv run --no-sync ste --rules` | passed; cinco regras `preview` |
| `uv run --no-sync ste --explain STE-I9-PUNCT-001` | passed; fonte e cobertura rastreáveis |
| lint real do `README.md` com as cinco regras | exit `1`; exatamente dois achados aprovados |
| `uv tree --no-dev` | passed; nenhum pacote de runtime externo |
| `uv build --no-sources` | passed; sdist e wheel criados |
| inspeção do wheel | passed; pacote, metadados, `LICENSE` e `NOTICE` |
| inspeção do sdist | passed; código, documentação e testes da Fase 4 presentes |
| inspeção por `.pdf`, `.docx`, `.bin`, `.ste-dict*` | passed; nenhum recurso protegido encontrado |
| `git diff --check` | passed |

Os testes de integração exercitam TXT e Markdown offline, JSON/texto, arquivo de
configuração, glossário, regras preview, baseline válida/inválida e gravação
atômica. O corpus testado contém as 65 labels humanas aprovadas.

## Falhas durante a execução

- a primeira regra expôs entidade HTML classificada como prosa; uma regressão
  minimizada corrigiu o parser antes de admitir a regra;
- o primeiro gate Ruff encontrou import e fixtures longas; as correções foram
  verificadas pela suíte completa;
- o primeiro `ruff format --check` final encontrou 15 arquivos novos; a
  formatação mecânica foi aplicada e todos os gates foram repetidos;
- a expansão do README introduziu um terceiro ponto e vírgula não revisado; ele
  foi corrigido editorialmente, e o smoke final confirmou somente os dois
  achados aprovados;
- nenhum timeout foi tratado como sucesso.

## Não verificado

- precisão em corpus amplo ou documentos técnicos de outro domínio;
- regras `stable`, vocabulário oficial e lookup por parte do discurso/meaning;
- Python 3.13, outros sistemas operacionais e CI remoto.

## Revisão humana

O mantenedor classificou os dois diagnósticos de ponto e vírgula no `README.md`
como úteis e corretos em 2026-08-12. Uma terceira ocorrência introduzida durante
a documentação foi corrigida editorialmente antes do smoke final e não foi
contabilizada como achado revisado.

## Próximo gate

A Fase 5, Vocabulary Engine confiável, aguarda aprovação do mantenedor.
