# Evidência de conclusão da Fase 3

Status: passed
Data: 2026-08-12
Python: CPython 3.12.10
Gerenciador: uv 0.11.14

## Escopo entregue

- catálogo executável explícito e vazio até a Fase 4;
- registry estrito para IDs, fonte, metadados e implementações;
- engine determinístico com validação de cada diagnóstico;
- seleção de regra com defaults, TOML explícito e override CLI;
- desabilitação explícita antes de executar a regra;
- formatadores de texto e JSON `1.0` determinísticos;
- CLI para um arquivo TXT/Markdown e códigos de saída `0`, `1` e `2`;
- erro interno de regra identificado sem expor traceback ou ser silenciado.

Nenhuma regra normativa, ID candidato definitivo, vocabulário, NLP, LLM ou
dependência de runtime foi adicionada.

## TDD observado

1. Engine/registry começaram com erro de import; após a implementação mínima,
   11 testes passaram.
2. Configuração começou sem os símbolos públicos; após o loader e resolver,
   nove testes passaram.
3. Reporting começou sem pacote; os três testes de texto/JSON passaram após a
   implementação mínima.
4. A composição CLI começou com sete falhas; depois passou os nove testes de
   integração da CLI antiga e nova.
5. Auditoria contra os ADRs produziu dois Reds adicionais: TOML aceitava boolean
   como versão inteira e `semantic` estável aceitava `warning`. Ambos foram
   corrigidos e os 17 testes afetados passaram.
6. O catálogo explícito começou com erro de import e passou após a composição
   vazia validada.

## Comandos e resultados

| Comando | Resultado |
|---|---|
| `uv --version` | passed; uv 0.11.14 |
| `uv lock --check` | passed; 12 pacotes resolvidos |
| `uv sync --locked` | passed; 12 pacotes verificados |
| `uv run --no-sync python --version` | passed; Python 3.12.10 |
| `uv run --no-sync pytest` | passed; 75 testes em 1,23 s |
| `uv run --no-sync ruff check .` | passed |
| `uv run --no-sync ruff format --check .` | passed; 29 arquivos formatados |
| `uv run --no-sync mypy src` | passed; 15 arquivos |
| `uv run --no-sync ste --help` | passed |
| `uv run --no-sync ste lint` | passed; informa ausência de regras estáveis |
| `uv run --no-sync ste lint README.md` | passed; nenhuma regra executável habilitada |
| `uv run --no-sync ste lint README.md --format json` | passed; JSON `1.0` vazio |
| `uv tree --no-dev` | passed; nenhum pacote de runtime externo |
| `uv build --no-sources` | passed; sdist e wheel criados |
| inspeção do wheel | passed; somente pacote, metadados, `LICENSE` e `NOTICE` |
| inspeção do sdist | passed; fontes e artefatos textuais do projeto |
| inspeção por `.pdf`, `.docx`, `.bin` | passed; nenhum encontrado fora de ambientes/artefatos ignorados |
| `git status --short` | revisado; arquivos ainda não commitados |

O teste offline bloqueou sockets enquanto a CLI leu e processou um TXT real. O
fitness test de dependências inspecionou corretamente imports `ste_lint.*` e
confirmou que `domain` não importa camadas externas.

## Falhas durante a execução

- o primeiro `ruff format --check .` encontrou seis arquivos novos; a
  formatação mecânica foi aplicada e todos os gates foram repetidos;
- a auditoria dos ADRs expôs e corrigiu os dois casos descritos no histórico
  TDD: boolean aceito como versão TOML e `warning` semantic;
- nenhum timeout foi tratado como sucesso.

## Não verificado

- regras reais e IDs definitivos, deliberadamente reservados para a Fase 4;
- baseline, supressão inline, SARIF e descoberta automática de configuração;
- Python 3.13, outros sistemas operacionais e CI remoto;
- publicação ou push no GitHub.

## Próximo gate

A Fase 4, primeiro MVP com regras determinísticas revisadas, aguarda aprovação
do mantenedor.
