# ADR-011: compatibilidade da saída JSON

Status: Accepted
Data: 2026-08-12

## Contexto

A primeira saída JSON vira API para scripts e CI. Ela precisa ser determinística,
versionada e distinta do texto destinado a pessoas.

## Decisão proposta

Emitir um único objeto UTF-8 por execução, terminado por newline, com esta forma
inicial:

```json
{
  "schema_version": "1.0",
  "diagnostics": []
}
```

Cada diagnóstico contém, em ordem estável: `rule_id`, `source`, `severity`,
`location`, `message`, `explanation`, `suggestion` e `evidence`. Os dois últimos
campos aparecem como `null` quando ausentes. `source` contém `standard`, `issue`
e `locator`; `location` contém URI, offsets e linha/coluna inicial/final.

Diagnósticos são ordenados por URI, offset inicial, offset final e `rule_id`.
A serialização usa Unicode sem escape ASCII obrigatório e não inclui timestamps,
paths absolutos acrescentados pelo engine ou campos dependentes do ambiente.

Mudança incompatível incrementa a versão major. Campo opcional aditivo incrementa
a minor; consumidores devem rejeitar major desconhecida e podem ignorar campos
aditivos de uma minor mais nova. Falha operacional não vira diagnóstico JSON:
vai para stderr e usa código de saída operacional.

## Alternativas rejeitadas

- JSON Lines, porque uma execução também precisa representar zero diagnósticos;
- array nu, porque não oferece identidade de schema;
- omitir campos nulos, porque cria formas estruturais diferentes para o mesmo
  tipo público;
- `sort_keys=True`, porque ordem alfabética não documenta a ordem semântica do
  contrato.

## Consequências

- snapshots byte a byte podem verificar determinismo;
- SARIF permanece fora desta fase;
- qualquer campo novo exige decisão explícita de compatibilidade.

## Aprovação necessária

Aceito explicitamente pelo mantenedor em 2026-08-12, antes de expor
`--format json`.
