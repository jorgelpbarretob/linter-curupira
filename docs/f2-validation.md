# Evidência de conclusão da Fase 2

Status: passed
Data: 2026-08-12
Python: CPython 3.12.10
Gerenciador: uv 0.11.14

## Escopo entregue

- modelo `Document` lossless com regiões lintáveis/ignoradas;
- spans Unicode semiabertos e projeção 1-based para linha/coluna;
- tokens lossless e sentenças mínimas restritas à prosa lintável;
- adapters para TXT, `.md` e `.markdown` sem I/O ou rede;
- rejeição explícita de PDF, DOCX, HTML e formatos desconhecidos;
- limite de tamanho e corpus adversarial sintético determinístico;
- contrato e limitações Markdown documentados.

Nenhuma regra normativa, vocabulário, NLP, LLM ou dependência de runtime foi
adicionada.

## TDD observado

1. O primeiro Red falhou na coleta pela ausência de `RegionKind` e do pacote
   `ste_lint.parsing`.
2. A implementação mínima fez os 20 testes iniciais de parser/domínio passarem.
3. Um Red de composição mostrou que markup inline dentro de lista/citação era
   classificado como prosa.
4. A correção mínima permitiu classificar inline e bloco de forma composta; os
   14 testes Markdown passaram.

## Comandos e resultados

| Comando | Resultado |
|---|---|
| `uv --version` | passed; uv 0.11.14 |
| `uv lock --check` | passed; 12 pacotes resolvidos |
| `uv sync --locked` | passed; 12 pacotes verificados |
| `uv run --no-sync python --version` | passed; Python 3.12.10 |
| `uv run --no-sync pytest` | passed; 42 testes em 0,56 s |
| `uv run --no-sync ruff check .` | passed |
| `uv run --no-sync ruff format --check .` | passed; 18 arquivos formatados |
| `uv run --no-sync mypy src` | passed; 9 arquivos |
| `uv run --no-sync ste --help` | passed |
| `uv run --no-sync ste lint` | passed; informa ausência de regras estáveis |
| `uv build --no-sources` | passed; sdist e wheel criados |
| inspeção do wheel | passed; pacote, metadados, `LICENSE` e `NOTICE` |
| inspeção do sdist | passed; somente fontes e artefatos textuais do projeto |
| `uv tree --no-dev` | passed; nenhum pacote de runtime externo |
| inspeção por `.pdf`, `.docx`, `.bin` | passed; nenhum encontrado fora de ambientes/artefatos ignorados |
| `git status --short` | revisado; arquivos ainda não commitados |

A fitness function confirmou que o domínio permanece sem dependência de camadas
externas. O teste de integração offline bloqueou sockets durante o caminho base.

## Falhas durante a execução

- o primeiro lint encontrou duas quebras de linha e uma simplificação local; as
  correções manuais foram verificadas por uma nova execução limpa;
- o primeiro teste adicional de composição não coletou por falta de `import
  pytest`; corrigido o teste, o Red funcional expôs o escape de markup inline em
  listas/citações e levou à correção mínima;
- nenhum timeout foi tratado como sucesso.

## Não verificado

- compatibilidade integral com CommonMark, que não faz parte do contrato;
- leitura/decodificação de bytes pelo filesystem, que pertence a um adapter
  futuro;
- Python 3.13 e outros sistemas operacionais;
- CI remoto e publicação no GitHub.

## Gate posterior

O mantenedor aprovou a Fase 3 e, no checkpoint inicial, aprovou explicitamente
os ADRs 007, 008, 009 e 011.
