# Curupira

Curupira é um linter open source, local-first, para documentação técnica em
português brasileiro. O projeto usa uma especificação autoral de português
técnico controlado; não traduz a ASD-STE100, não certifica documentos e não
promete cobertura linguística integral.

O produto oferece uma regra determinística em status `preview`:
`CURUPIRA-PT-PONT-001`, que detecta o caractere ponto e vírgula em prosa lintável.
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
- para a análise linguística opcional: `pip install "curupira-lint[nlp]"`.

```bash
uv sync --locked
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src/curupira_lint src/hermes_lint
uv run curupira --help
```

O lint determinístico é offline. O pacote-base não baixa modelos e não chama
provedores remotos. Somente `semantic-review`, quando chamado explicitamente,
envia o conteúdo do arquivo à API da Maritaca.

## Uso

Regras `preview` ficam desabilitadas por padrão e precisam de opt-in explícito.
Regras que futuramente atingirem status `stable` serão habilitadas por padrão e
poderão ser desabilitadas por configuração ou CLI:

```bash
uv run curupira lint procedimento.md --enable-rule CURUPIRA-PT-PONT-001
uv run curupira lint procedimento.md --enable-rule CURUPIRA-PT-PONT-001 --format json
uv run curupira --rules
uv run curupira --explain CURUPIRA-PT-PONT-001
```

A configuração TOML é explícita e estrita:

```toml
schema_version = 1

[rules]
enable = ["CURUPIRA-PT-PONT-001"]
disable = []
```

Use-a com `--config curupira.toml`. Opções `--enable-rule` e `--disable-rule` da
CLI têm precedência sobre o arquivo. Chaves e IDs desconhecidos causam erro
operacional; não há descoberta silenciosa de configuração global.

Uma baseline armazena somente fingerprints SHA-256, sem trechos do documento:

```bash
uv run curupira lint procedimento.md --enable-rule CURUPIRA-PT-PONT-001 \
  --write-baseline curupira-baseline.json
uv run curupira lint procedimento.md --enable-rule CURUPIRA-PT-PONT-001 \
  --baseline curupira-baseline.json
```

| Código | Resultado |
|---:|---|
| `0` | execução concluída sem diagnóstico remanescente |
| `1` | execução concluída com diagnóstico, inclusive `info` de regra `preview` habilitada |
| `2` | erro operacional de configuração, entrada, catálogo ou parser |

O parser aceita UTF-8 em `.txt`, `.md` e `.markdown`, preserva offsets por ponto
de código Unicode e mantém LF/CRLF sem normalização. Links simbólicos são
seguidos pelo sistema operacional; o linter lê exatamente o caminho fornecido.

### Análise linguística pt-BR preview

Depois de instalar o extra `nlp`, analise um arquivo de texto sem enviá-lo a um
serviço remoto:

```bash
uv run curupira analyze procedimento.txt --format json
```

A saída canônica informa `status: preview`, hash do texto-fonte, offsets Unicode,
palavras sintáticas, sentenças e proveniência completa. O texto original não é
duplicado no JSON. Nesta primeira entrega, `analyze` aceita somente `.txt`;
Markdown é recusado antes de carregar o modelo para evitar concatenar prosa
separada por markup e produzir offsets enganosos.

O extra fixa `spacy==3.8.15` e busca o wheel upstream
`pt_core_news_sm==3.8.0` pelo SHA-256 publicado no contrato do projeto. O modelo
é de português geral, não um modelo pt-BR exclusivo; a aplicação brasileira
vem da especificação autoral Curupira. Ele é CC BY-SA 4.0 e deriva das fontes
declaradas no próprio pacote. A execução não baixa nada em runtime; instalação
e execução são etapas separadas.

### Motor semântico Sabiázinho preview

O motor semântico opt-in usa o modelo brasileiro Sabiázinho 4 da Maritaca para
levantar observações de ambiguidade, agente implícito, múltiplas ações e
terminologia. Ele não cria diagnósticos normativos: cada observação precisa citar
um trecho exato e único, e os offsets são calculados localmente antes da saída.

```bash
export MARITACA_API_KEY="..."
curupira semantic-review procedimento.txt --format json
# residência de dados no Brasil, quando contratada:
curupira semantic-review procedimento.txt --model sabiazinho-4-br-sp
```

Esse comando envia o texto à API. Não o use com documento confidencial sem base
legal e autorização aplicáveis. O padrão fixado é
`sabiazinho-4-2026-01-06`; uso, modelo solicitado/retornado e hash do texto ficam
registrados no JSON. A requisição usa HTTPS com a validação TLS padrão do Python,
`store: false` e respeita proxies configurados no ambiente; não use proxy não
confiável. Redirecionamentos HTTP seguem o comportamento padrão de `urllib`.
Chave ausente ou em branco termina com código `2`, sem chamar a rede. A política
de retenção do provedor continua regida pelo contrato da conta. Consulte os
[modelos oficiais da Maritaca](https://docs.maritaca.ai/pt/modelos).

O plano de comparação com o fluxo sem Curupira e o formulário de feedback estão
em [Lançamento do Curupira preview](docs/curupira-preview-launch-v1.md).

## Especificação, avaliação e limites

- [Especificação Curupira 0.1](docs/curupira-controlled-portuguese-spec-0.1.md)
- [Migração Hermes → Curupira](docs/adr/0021-curupira-identity-migration.md)
- [Taxonomia de regras](docs/hermes-rule-taxonomy.md)
- [Replan do produto](docs/pt-br-product-replan.md)
- [Protocolo do corpus de CURUPIRA-PT-PONT-001](docs/hermes-pt2-corpus-protocol.md)

O corpus de desenvolvimento é sintético e público. O primeiro holdout é mantido
sob custódia separada e não é usado para implementar ou ajustar o detector. A
execução única foi concluída; a regra permaneceu `preview` porque falhou os
gates do limite inferior Wilson e de zero falso positivo conhecido. Veja o
[relatório agregado](docs/hermes-pont-001-holdout-evaluation-v1.md).

O candidato NLP também falhou o gate linguístico rígido do bake-off. Sua
publicação opt-in é uma decisão explícita de aprendizado de produto, não uma
promoção, certificação ou seleção de backend estável.

## Hermes Agent: primeiro caso de uso

Curupira nasce como preflight local para o
[Hermes Agent da Nous Research](https://github.com/NousResearch/hermes-agent).
A skill instalável em `integrations/hermes-agent/curupira-preflight` ensina o
agente a validar documentação técnica pt-BR antes da entrega. O protocolo
compara a mesma tarefa sem e com Curupira por chamadas, esclarecimentos, erros
residuais, retrabalho e tempo até aceite; tokens reais entram quando a superfície
do agente os expõe.

Instale diretamente no Hermes Agent:

```bash
hermes skills install \
  https://raw.githubusercontent.com/jorgelpbarretob/linter-curupira/main/integrations/hermes-agent/curupira-preflight/SKILL.md \
  --yes
```

No piloto sintético inicial, a invocação interativa reduziu findings residuais
de 1 para 0, com uma chamada de ferramenta adicional; tokens não foram medidos
nessa superfície. Veja o
[relatório completo](docs/curupira-hermes-agent-pilot-v1.md). Use a skill pelo
slash command `/curupira-preflight`; o preload em modo one-shot não é suportado
neste preview.

O pacote não publica um comando `hermes`: esse nome pertence ao Hermes Agent.

## Compatibilidade da linha histórica Hermes

A versão 0.3.x ainda inclui o pacote Python `hermes_lint` para reproduzir fluxos
0.2. Integrações novas devem usar Curupira. IDs e baselines não são convertidos
silenciosamente; consulte o
[ADR-021](docs/adr/0021-curupira-identity-migration.md).

## Linha inglesa histórica

O diretório `src/ste_lint` e seus testes registram o protótipo inglês congelado
e não fazem parte do pacote `curupira-lint`. A decisão e a evidência de encerramento
estão em [ADR-016](docs/adr/0016-portuguese-first-and-maritaca-roles.md) e
[Fechamento da linha inglesa](docs/english-line-closure.md).

## Licenças

Código, configuração executável e testes de software usam Apache-2.0. A
especificação Curupira, a documentação linguística e o corpus autoral usam CC BY
4.0. Textos de terceiros preservam a licença da fonte e não são relicenciados
pelo projeto. Consulte [a política de identidade e licenças](docs/hermes-identity-and-licensing.md).
