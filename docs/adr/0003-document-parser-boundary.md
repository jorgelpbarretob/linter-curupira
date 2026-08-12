# ADR-003: fronteira entre documento e parser

Status: Accepted
Data: 2026-08-12

## Contexto

Markdown mistura prosa e markup. Regras não devem interpretar filesystem nem
repetir lógica para code fences, links, tabelas ou regiões ignoradas.

## Decisão proposta

Adapters de parser produzem um `Document` lossless com blocos lintáveis, regiões
ignoradas e spans mapeados ao original. O MVP suporta TXT e Markdown; PDF, HTML
e DOCX ficam fora do escopo inicial.

## Consequências

- Regras recebem `RuleContext` e nunca abrem arquivos.
- Round-trip e mapeamento de spans são gates do parser.
- Novos formatos entram como adapters sem alterar o domínio.

## Aprovação necessária

Aceito pelo mantenedor em 2026-08-12, antes da Fase 2.
