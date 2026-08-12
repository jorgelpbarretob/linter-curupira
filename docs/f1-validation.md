# Evidência de conclusão da Fase 1

Status: passed
Data: 2026-08-12
Python: CPython 3.11.15
Gerenciador: uv 0.11.14

O registro abaixo preserva a execução original da Fase 1. Após a decisão de
fixar Python 3.12, o projeto foi revalidado em CPython 3.12.10; veja a seção
"Revalidação do ambiente".

## Escopo entregue

- repositório Git local em `main`, com remoto privado `origin` configurado;
- código Apache-2.0 com `LICENSE` e `NOTICE`;
- pacote `ste_lint` em layout `src` e entry point `ste`;
- modelos imutáveis de domínio e validação de spans;
- contrato `Rule`, `RuleContext` e registry determinístico;
- CLI vazia que declara não haver regras estáveis;
- dependências de desenvolvimento pinadas no `uv.lock`;
- testes unitários, integração offline e fitness function de dependências.

Nenhuma regra, parser, vocabulário, NLP, LLM ou acesso de rede foi adicionado ao
caminho de lint.

## Comandos e resultados

| Comando | Resultado |
|---|---|
| `uv lock --check` | passed; 12 pacotes resolvidos |
| `uv sync --locked` | passed em Python 3.11.15 |
| `uv run --no-sync pytest` | passed; 12 testes |
| `uv run --no-sync ruff check .` | passed |
| `uv run --no-sync mypy src` | passed; 6 arquivos |
| `uv run --no-sync ste --help` | passed |
| `uv run --no-sync ste lint` | passed; informa ausência de regras estáveis |
| `uv build --no-sources` | passed; sdist e wheel criados |
| inspeção do wheel | passed; somente código, metadados, LICENSE e NOTICE |
| inspeção por `.pdf`, `.docx`, `.bin` | passed; nenhum encontrado fora de ambientes ignorados |
| `git status --short` | revisado; todos os arquivos ainda não commitados |

## TDD observado

1. Primeira execução: quatro erros de coleta por `ModuleNotFoundError`, antes da
   criação do pacote.
2. Implementação mínima: 11 testes passaram.
3. Segundo Red: span fora do documento falhou por ausência de `validate_for`.
4. Implementação mínima: suíte final com 12 testes passou.

## Falhas durante a execução

- Ruff encontrou formatação de import em `__main__.py`; o autofix restrito ao
  arquivo foi aplicado e a verificação posterior passou.
- Nenhum timeout foi tratado como sucesso.

## Não verificado

- auditoria de vulnerabilidades com ferramenta dedicada, pois o pacote não tem
  dependências de runtime e nenhuma ferramenta de auditoria foi adicionada;
- CI remoto, publicação no GitHub e instalação em outros sistemas operacionais;
- Python 3.13.

## Revalidação do ambiente

Em 2026-08-12, `.python-version`, `requires-python`, Ruff e mypy foram alinhados
em Python 3.12. O projeto também passou a exigir exatamente uv 0.11.14.

| Comando | Resultado |
|---|---|
| `uv --version` | passed; uv 0.11.14 |
| `uv lock` | passed |
| `uv sync --locked` | passed; ambiente recriado em CPython 3.12.10 |
| `uv run --no-sync python --version` | passed; Python 3.12.10 |
| `uv run --no-sync pytest` | passed; 12 testes da Fase 1 |
| `uv run --no-sync ruff check .` | passed |
| `uv run --no-sync mypy src` | passed |
| `uv build --no-sources` | passed |

## Gate posterior

A autorização do mantenedor para seguir liberou a Fase 2. O incremento começou
com testes de round-trip e offsets para TXT, sem regra normativa.
