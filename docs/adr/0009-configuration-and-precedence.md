# ADR-009: configuração e precedência

Status: Accepted
Data: 2026-08-12

## Contexto

Configuração implícita torna execuções difíceis de reproduzir. A Fase 3 precisa
selecionar e desabilitar regras sem introduzir baseline, configuração global ou
uma DSL.

## Decisão proposta

Usar TOML lido com `tomllib`, sem dependência de runtime. A configuração de
projeto só é carregada por caminho explícito `--config`; não há descoberta nem
arquivo global no MVP.

Precedência, da menor para a maior:

1. defaults do catálogo: `stable` habilitada; `preview` e `planned`
   desabilitadas;
2. arquivo TOML de projeto;
3. opções repetíveis da CLI.

Contrato inicial:

```toml
schema_version = 1

[rules]
enable = ["PROJECT-EXAMPLE-001"]
disable = []
```

A CLI oferece `--enable-rule ID` e `--disable-rule ID`. O mesmo ID em `enable` e
`disable` na mesma camada é erro; na camada superior, a escolha explícita
substitui a inferior. ID desconhecido, chave desconhecida, versão incompatível,
tipo inválido ou arquivo ausente é falha operacional. A configuração é validada
por inteiro antes de executar qualquer regra.

Nesta fase, "supressão explícita" significa desabilitar uma regra por arquivo ou
CLI. Supressão por linha, comentário ou fingerprint fica fora do escopo; a
baseline permanece na Fase 4.

## Alternativas rejeitadas

- YAML, por exigir dependência e ampliar tipos aceitos;
- descoberta automática em diretórios pais, por introduzir estado implícito;
- configuração global de usuário, por reduzir reprodutibilidade;
- ignorar chaves/IDs desconhecidos, porque erros de digitação seriam silenciosos.

## Consequências

- o mesmo documento, catálogo, arquivo e argumentos produzem a mesma seleção;
- regras desabilitadas não têm `check` invocado;
- futuros campos exigem evolução explícita do schema.

## Aprovação necessária

Aceito explicitamente pelo mantenedor em 2026-08-12, antes de publicar o loader
e as opções CLI.
