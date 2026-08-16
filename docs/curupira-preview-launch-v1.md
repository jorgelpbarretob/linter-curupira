# Lançamento do Curupira preview v1

Status: Preview autorizado
Date: 2026-08-16

Curupira 0.3.0 preserva a implementação local avaliada na linha Hermes e muda
sua identidade pública conforme o ADR-021. A capacidade NLP continua opt-in e
o bake-off continua `quality-fail`.

## Instalação e uso

```bash
pip install "curupira-lint[nlp]"
curupira lint procedimento.md --enable-rule CURUPIRA-PT-PONT-001
curupira analyze procedimento.txt --format json
curupira semantic-review procedimento.txt --format json
```

A instalação pode usar rede para obter wheels fixados. Depois de instalada, a
execução de `lint` e `analyze` é local e não baixa modelo nem envia documento a
provedor remoto. `semantic-review` é uma exceção explícita: envia o `.txt` à API
Maritaca, usa por padrão `sabiazinho-4-2026-01-06` e registra uso e proveniência.

## Migração

| Hermes 0.2 | Curupira 0.3 |
|---|---|
| `hermes-lint` | `curupira-lint` |
| `hermes_lint` | `curupira_lint` |
| `hermes` | `curupira` |
| `HERMES-PT-PONT-001` | `CURUPIRA-PT-PONT-001` |
| `hermes-linguistic-analysis/v1` | `curupira-linguistic-analysis/v1` |

O pacote Python `hermes_lint` permanece no wheel 0.3.x para transição. O comando
`hermes` não é publicado porque pertence ao Hermes Agent da Nous Research.
Baselines devem ser regeneradas porque o ID participa do fingerprint.

## Primeiro caso de uso: Hermes Agent

O preview inclui a skill `curupira-preflight` para o Hermes Agent. Ela executa
o linter local antes da entrega de documentação técnica pt-BR e corrige apenas
findings observados. A adoção começa por skill porque é opt-in, progressiva e
não exige fork ou hook invisível no agente.

```bash
hermes skills install \
  https://raw.githubusercontent.com/jorgelpbarretob/linter-curupira/main/integrations/hermes-agent/curupira-preflight/SKILL.md \
  --yes
```

O storytelling do preview é um A/B reproduzível da mesma tarefa no Hermes
Agent, sem e com a skill. O protocolo prevê tokens informados pelo próprio
agente, chamadas, perguntas de esclarecimento, findings residuais, retrabalho e
tempo. O piloto inicial não expôs tokens nessa superfície; o relatório não os
estima, não converte bytes em tokens nem generaliza um caso sintético para
produção.

## Motor semântico luso-brasileiro

Sabiázinho 4 é o motor semântico opt-in inicial. O adapter aceita apenas
observações ancoradas em trecho exato e calcula offsets localmente; saída de
modelo não vira diagnóstico normativo nem promove regra. A variante
`sabiazinho-4-br-sp` pode ser selecionada para residência de dados no Brasil.
O `pt_core_news_sm` usado na análise local é um modelo de português geral e não
fornece, por si só, cobertura pt-BR. O recorte brasileiro vem da especificação
autoral e do corpus Curupira. Somente esse perfil pt-BR tem regra e dataset
executáveis nesta release; pt-PT e outros perfis lusófonos entram como evolução
orientada por corpus próprio, sem alegação antecipada de cobertura.

O smoke real com texto sintético retornou o mesmo modelo solicitado, 313 tokens
totais e duas observações com ancoragem exata. O registro está em
`artifacts/curupira/sabiazinho-smoke-v1/summary.json`.

## Medição de valor

A comparação com o fluxo sem Curupira usa chamadas, perguntas de
esclarecimento, erros, ciclos de retrabalho e tempo até aceite. Quando
disponíveis, tokens reais do provedor também entram na comparação; quando não,
ficam explicitamente ausentes. Bytes não são convertidos artificialmente em
tokens. Issues devem usar exemplos sintéticos ou autorizados, nunca documentos
privados.

## Limites

- `CURUPIRA-PT-PONT-001` permanece `preview`;
- análise NLP aceita somente `.txt` nesta versão;
- revisão semântica exige rede, chave Maritaca e envio explícito do `.txt`;
- não há certificação, cobertura integral ou backend estável selecionado;
- os erros do holdout Hermes permanecem selados e não foram usados no rebrand.

A jornada de usuário que antecede a publicação está definida no
[`UAT do Curupira preview v1`](curupira-preview-uat-v1.md).
