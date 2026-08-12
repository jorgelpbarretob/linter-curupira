# ADR-010: fingerprint e formato de baseline

Status: Accepted
Data: 2026-08-12

## Contexto

Uma baseline permite adotar o linter em documentos existentes sem ocultar novos
achados. Fingerprints baseados diretamente em offsets quebram quando linhas são
inseridas antes do diagnóstico; fingerprints vagos demais podem suprimir outro
achado por colisão semântica.

## Decisão proposta

Usar um arquivo JSON estrito e local:

```json
{
  "schema_version": "1.0",
  "fingerprints": ["sha256:..."]
}
```

Cada fingerprint é SHA-256 sobre uma representação canônica UTF-8 composta por:

1. versão interna do algoritmo;
2. `rule_id`;
3. URI recebida pela CLI, normalizada somente para `/`;
4. texto exato do span do diagnóstico com whitespace colapsado;
5. linha ou bloco contextual que contém o span, com whitespace colapsado;
6. ordinal entre achados com a mesma identidade de conteúdo no documento.

Offsets, linha/coluna, mensagem, severidade e locator não entram no hash. Assim,
inserções anteriores não invalidam a entrada, enquanto mudança no conteúdo alvo,
arquivo ou regra produz nova identidade. O ordinal diferencia repetições
idênticas, embora inserir outra repetição idêntica antes possa deslocá-lo; essa é
uma limitação aceita e documentada.

`--baseline PATH` carrega e aplica um arquivo existente. `--write-baseline PATH`
executa as regras selecionadas e grava atomicamente uma baseline nova. Os dois
modos são mutuamente exclusivos. Fingerprints são ordenados e deduplicados;
versão, JSON, hash ou chave desconhecida falha de forma operacional. Baseline
suprime somente reporting/exit code, nunca impede a execução ou validação da
regra.

## Alternativas rejeitadas

- offsets ou linha/coluna no hash, por serem frágeis a edições anteriores;
- somente `rule_id` e texto do span, porque pontuação curta se repete;
- mensagem/explicação, porque uma melhoria editorial invalidaria a baseline;
- fuzzy matching, porque poderia ocultar achados novos sem correspondência exata;
- armazenar trechos em claro, porque replica conteúdo técnico no artefato.

## Consequências

- a baseline não contém texto do documento, somente hashes;
- renomear o arquivo ou mudar o conteúdo contextual exige regeneração;
- qualquer mudança incompatível no algoritmo ou formato incrementa a versão
  major;
- falsos positivos continuam devendo virar regressão; baseline não substitui
  correção nem promoção responsável de `preview`.

## Aprovação necessária

Aceito explicitamente pelo mantenedor em 2026-08-12, antes da implementação de
`--baseline` e `--write-baseline`.
