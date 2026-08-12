# Contrato do engine, configuração e reporting

Status: implementado na Fase 3
Data: 2026-08-12

## Catálogo e registry

O catálogo executável é uma tupla explícita de `RuleMetadata`. Na Fase 3 ela
permanece vazia: as candidatas normativas não recebem ID nem implementação antes
do incremento individual da Fase 4.

O registry valida namespace e fonte conforme ADR-007, rejeita IDs duplicados,
implementação ausente, metadados divergentes e implementação para regra
`planned` ou `human-review`. Startup termina antes do lint quando o catálogo não
corresponde às implementações disponíveis.

## Seleção e configuração

Somente regras `stable` começam habilitadas. Regras `preview` exigem opt-in. A
precedência é defaults, arquivo TOML indicado por `--config`, depois CLI. Em uma
mesma camada, um ID não pode aparecer simultaneamente em `enable` e `disable`.
IDs/chaves desconhecidos, tipos inválidos e versão diferente de `1` falham antes
de executar regras.

`--enable-rule ID` e `--disable-rule ID` são repetíveis. `text_type` aceita
`procedural`, `descriptive` ou `procedural-note`, e pode ser sobrescrito por
`--text-type`. `[glossary].terms` preserva uma allowlist local explícita; ela não
é vocabulário oficial e ainda não ativa uma regra de vocabulário. Não existe
descoberta de configuração, estado global ou supressão inline.

## Execução e validação

O engine executa somente IDs resolvidos, em ordem de ID. Cada diagnóstico é
validado contra a regra emissora, metadados do catálogo e texto do documento.
A saída final é ordenada por URI, offset inicial, offset final e `rule_id`.

Regra `preview` e `semantic` emite no máximo `info`; `human-review` não executa.
Exceção de regra vira `RuleExecutionError` com o ID responsável. Fonte, span ou
severidade divergente é falha operacional, nunca silêncio ou diagnóstico
sintético.

## Reporting

O texto humano contém URI, linha/coluna, offsets, severidade, `rule_id`, fonte,
mensagem e explicação; sugestão/evidência aparecem somente quando presentes.

O JSON segue ADR-011, usa `schema_version: "1.0"`, preserva Unicode, inclui
campos opcionais como `null` e termina com newline. Não inclui timestamp ou
estado dependente do ambiente.

## CLI e códigos de saída

- `0`: execução válida sem diagnósticos;
- `1`: execução válida com um ou mais diagnósticos;
- `2`: falha operacional de input, configuração, catálogo, parser ou regra.

Erros operacionais vão para stderr. Diagnósticos e resultados válidos vão para
stdout. Arquivos são lidos como UTF-8 com newline original preservado.

## Baseline

`--write-baseline PATH` grava atomicamente JSON `1.0` com fingerprints SHA-256
ordenados. `--baseline PATH` aplica uma baseline existente depois da execução e
validação de todas as regras. Os modos são mutuamente exclusivos.

O fingerprint segue ADR-010 e usa `rule_id`, URI, texto normalizado do span,
contexto normalizado e ordinal entre achados idênticos. Não usa offsets,
linha/coluna, mensagem ou severidade e não armazena trechos em claro.
