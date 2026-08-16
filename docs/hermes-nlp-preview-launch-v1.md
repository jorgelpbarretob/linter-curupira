# Lançamento do preview NLP local pt-BR v1

Status: Preview autorizado
Date: 2026-08-16

## Decisão

O mantenedor autorizou colocar a capacidade em uso antes de atingir perfeição,
receber problemas e contribuições por issues e pull requests e evoluir com uso
real. Esta é uma exceção explícita de lançamento: o resultado `quality-fail` do
bake-off permanece verdadeiro e não foi reinterpretado.

O candidato spaCy + `pt_core_news_sm` não foi selecionado como backend estável.
Ele é disponibilizado somente por uma instalação opcional e pelo comando
explicitamente denominado `analyze` em status `preview`. Nenhuma regra normativa
nova depende desta capacidade.

## Jornada publicada

```bash
pip install "hermes-lint[nlp]"
hermes analyze procedimento.txt --format json > analise.json
```

O documento é processado localmente. O runtime não baixa modelo e não chama LLM
ou serviço remoto. O JSON não repete o texto-fonte; registra seu URI e SHA-256,
as unidades linguísticas, os offsets e a proveniência do backend.

A instalação inicial usa rede para obter dependências e o wheel upstream, salvo
quando um cache ou wheelhouse local já estiver preparado. É o comando
`hermes analyze`, depois da instalação, que opera integralmente offline.
O SHA-256 registrado corresponde ao wheel upstream específico
`pt_core_news_sm-3.8.0-py3-none-any.whl`; cache, mirror ou wheelhouse deve
fornecer bytes idênticos, e o lockfile verifica esse digest na instalação.

O escopo v1 aceita apenas UTF-8 `.txt`. Markdown é recusado antes de carregar o
backend porque o ADR-019 proíbe concatenar regiões lintáveis descontínuas.

## Hipótese de valor

Hermes cria valor quando um agente ou usuário consegue completar a mesma tarefa
com menos consumo e menos ambiguidade que no fluxo sem análise estruturada. O
preview não presume que isso já ocorreu: a hipótese será testada em pares A/B.

Para cada tarefa repetível, registrar:

| Medida | Fonte válida | Melhor direção |
|---|---|---:|
| tokens de entrada e saída | usage real do provedor | menor |
| chamadas de modelo/ferramenta | log da execução | menor |
| perguntas de esclarecimento | contagem da conversa | menor |
| erros ou requisitos omitidos | verificação determinística da tarefa | menor |
| ciclos de retrabalho | histórico da issue/execução | menor |
| tempo até resultado aceito | timestamps da execução | menor |

A comparação usa a mesma tarefa, documento, modelo, versão, prompt de objetivo e
critério de aceite. O braço A não usa Hermes; o braço B pode consumir a saída do
Hermes. Ordem alternada e pelo menos três repetições reduzem efeito de warmup e
ordem. Bytes ou caracteres não serão convertidos em “tokens economizados”; só o
contador real do provedor sustenta essa alegação.

## Feedback e evolução

Defeitos reproduzíveis entram como issues usando o formulário `NLP preview`.
Correções podem chegar por pull request com teste de regressão e sem incluir
documento privado. Relatos devem preferir exemplos mínimos, sintéticos ou
explicitamente autorizados para publicação.

O preview pode evoluir sem promoção enquanto os contratos de schema e offsets
forem preservados. Mudança incompatível exige novo schema. Promoção para
`stable` continua bloqueada até novo corpus independente, gates aprovados e
painel válido; feedback de usuário não transforma automaticamente dado de
produção em ground truth.

## Critérios operacionais

Uma release do preview é aceitável quando instalação opcional, execução local,
JSON válido, offsets exatos, ausência de import NLP no pacote-base e erros de
setup são verificados. Crash, alteração de texto, offset inválido, acesso de rede
em runtime ou vazamento de documento é defeito bloqueante.

## Evidência de implementação

A suíte contém uma verificação subprocessada de que importar a CLI base não
carrega `spacy` nem `pt_core_news_sm`. Quando as versões opcionais fixadas estão
instaladas, um teste de integração carrega o modelo e analisa texto com CRLF
enquanto DNS e conexões de socket estão negados, conferindo todos os slices de
token. Em instalação base, somente esse teste opcional é ignorado; o erro de
setup e os contratos continuam cobertos por doubles locais.

O freeze histórico v1 de HERMES-PT-PONT-001 permanece intocado. Como o
manifesto conservador inclui todo `src/hermes_lint`, a adição desta capacidade
gerou `pont-001-detector-freeze-v2`: ele registra o estado pós-lançamento sem
reescrever a evidência usada na avaliação anterior e sem reavaliar o holdout.

## UAT Himavai

O roteiro de UAT executável está em `docs/hermes-nlp-preview-uat-v1.md`. Himavai
registra experiência da jornada e não rotula corpus, decide qualidade
linguística ou promove o backend.

## Painel técnico

Maritaca `sabia-4-thinking`, Grok `grok-4.6` e Kimi
`kimi-k2.7-code:cloud` aprovaram unanimemente o delta final depois de rework
determinístico. O registro público, hashes e histórico de findings estão em
`artifacts/hermes/nlp-preview/model-panel-review-v1.json`. O painel confirmou
que não recebeu corpus, outputs do bake-off, PONT-001 ou documento de usuário e
que não fez alegação de qualidade estável.
