# Hermes

Hermes é um linter open source, local-first, para documentação técnica em
português brasileiro. O projeto usa uma especificação autoral de português
técnico controlado; não traduz a ASD-STE100, não certifica documentos e não
substitui revisão técnica ou linguística humana.

O produto oferece uma regra determinística em status `preview`:
`HERMES-PT-PONT-001`, que detecta o caractere ponto e vírgula em prosa lintável.
Código, destinos de links, URLs, metadados e outras regiões Markdown suportadas
são excluídos antes da análise. A regra não sugere nem aplica correção.

Ausência de diagnósticos significa somente que as regras habilitadas não
encontraram ocorrências no escopo que conseguem analisar.

Também existe uma análise linguística local pt-BR em `preview`. Ela expõe
tokenização, sentenças, morfologia e dependências para experimentação e
integração por agentes, mas ainda não sustenta regra normativa nem alegação de
qualidade estável.

## Requisitos e desenvolvimento

- Python 3.12 ou mais recente;
- `uv` 0.11.14, fixado em `pyproject.toml`;
- nenhuma dependência de runtime no pacote-base;
- para a análise linguística opcional: `pip install "hermes-lint[nlp]"`.

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

### Análise linguística pt-BR preview

Depois de instalar o extra `nlp`, analise um arquivo de texto sem enviá-lo a um
serviço remoto:

```bash
uv run hermes analyze procedimento.txt --format json
```

A saída canônica informa `status: preview`, hash do texto-fonte, offsets Unicode,
palavras sintáticas, sentenças e proveniência completa. O texto original não é
duplicado no JSON. Nesta primeira entrega, `analyze` aceita somente `.txt`;
Markdown é recusado antes de carregar o modelo para evitar concatenar prosa
separada por markup e produzir offsets enganosos.

O extra fixa `spacy==3.8.15` e busca o wheel upstream
`pt_core_news_sm==3.8.0` pelo SHA-256 publicado no contrato do projeto. O modelo
é CC BY-SA 4.0 e deriva das fontes declaradas no próprio pacote. A execução não
baixa nada em runtime; instalação e execução são etapas separadas.

O plano de comparação com o fluxo sem Hermes e o formulário de feedback estão
em [Lançamento do preview NLP](docs/hermes-nlp-preview-launch-v1.md).

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

O candidato NLP também falhou o gate linguístico rígido do bake-off. Sua
publicação opt-in é uma decisão explícita de aprendizado de produto, não uma
promoção, certificação ou seleção de backend estável.

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
