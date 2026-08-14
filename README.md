# Hermes

Hermes é um linter open source, local-first, para documentação técnica em
português brasileiro. O projeto usa uma especificação autoral de português
técnico controlado; não traduz a ASD-STE100, não certifica documentos e não
substitui revisão técnica ou linguística humana.

O incremento atual oferece uma regra determinística em status `preview`:
`HERMES-PT-PONT-001`, que detecta o caractere ponto e vírgula em prosa lintável.
Código, destinos de links, URLs, metadados e outras regiões Markdown suportadas
são excluídos antes da análise. A regra não sugere nem aplica correção.

Ausência de diagnósticos significa somente que as regras habilitadas não
encontraram ocorrências no escopo que conseguem analisar.

## Requisitos e desenvolvimento

- Python 3.12 ou mais recente;
- `uv` 0.11.14, fixado em `pyproject.toml`;
- nenhuma dependência de runtime no pacote-base.

```bash
uv sync --locked
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src/hermes_lint
uv run hermes --help
```

O lint determinístico é offline. O pacote-base não baixa modelos e não chama
provedores remotos.

## Uso

Regras `preview` ficam desabilitadas por padrão e precisam de opt-in explícito:

```bash
uv run hermes lint procedimento.md --enable-rule HERMES-PT-PONT-001
uv run hermes lint procedimento.md --enable-rule HERMES-PT-PONT-001 --format json
uv run hermes --rules
uv run hermes --explain HERMES-PT-PONT-001
```

A configuração TOML é explícita e estrita:

```toml
schema_version = 1

[rules]
enable = ["HERMES-PT-PONT-001"]
disable = []
```

Use-a com `--config hermes.toml`. Opções `--enable-rule` e `--disable-rule` da
CLI têm precedência sobre o arquivo. Chaves e IDs desconhecidos causam erro
operacional; não há descoberta silenciosa de configuração global.

Uma baseline armazena somente fingerprints SHA-256, sem trechos do documento:

```bash
uv run hermes lint procedimento.md --enable-rule HERMES-PT-PONT-001 \
  --write-baseline hermes-baseline.json
uv run hermes lint procedimento.md --enable-rule HERMES-PT-PONT-001 \
  --baseline hermes-baseline.json
```

| Código | Resultado |
|---:|---|
| `0` | execução concluída sem diagnóstico remanescente |
| `1` | execução concluída com diagnóstico |
| `2` | erro operacional de configuração, entrada, catálogo ou parser |

O parser aceita UTF-8 em `.txt`, `.md` e `.markdown`, preserva offsets por ponto
de código Unicode e mantém LF/CRLF sem normalização.

## Especificação, avaliação e limites

- [Especificação Hermes 0.1](docs/hermes-controlled-portuguese-spec-0.1.md)
- [Taxonomia de regras](docs/hermes-rule-taxonomy.md)
- [Replan do produto](docs/pt-br-product-replan.md)
- [Protocolo do corpus de HERMES-PT-PONT-001](docs/hermes-pt2-corpus-protocol.md)

O corpus de desenvolvimento é sintético e público. O primeiro holdout é mantido
sob custódia separada e não é usado para implementar ou ajustar o detector. A
execução única foi concluída; a regra permaneceu `preview` porque falhou os
gates do limite inferior Wilson e de zero falso positivo conhecido. Veja o
[relatório agregado](docs/hermes-pont-001-holdout-evaluation-v1.md).

## Linha inglesa histórica

O diretório `src/ste_lint` e seus testes registram o protótipo inglês congelado
e não fazem parte do pacote `hermes-lint`. A decisão e a evidência de encerramento
estão em [ADR-016](docs/adr/0016-portuguese-first-and-maritaca-roles.md) e
[Fechamento da linha inglesa](docs/english-line-closure.md).

## Licenças

Código, configuração executável e testes de software usam Apache-2.0. A
especificação Hermes, a documentação linguística e o corpus autoral usam CC BY
4.0. Textos de terceiros preservam a licença da fonte e não são relicenciados
pelo projeto. Consulte [a política de identidade e licenças](docs/hermes-identity-and-licensing.md).
