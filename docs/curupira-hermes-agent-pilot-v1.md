# Piloto Curupira no Hermes Agent v1

Status: evidência sintética inicial
Date: 2026-08-16

## Pergunta

O preflight Curupira reduz erro residual em uma tarefa conservadora de revisão
pt-BR no Hermes Agent, comparado à mesma tarefa sem o preflight?

## Desenho

Os dois braços usaram Hermes Agent 0.20.1, Grok 4.6, raciocínio `low`, CLI
interativa, o mesmo texto sintético e a mesma tarefa. O tratamento diferiu pela
invocação explícita `/curupira-preflight`. O avaliador determinístico foi
`CURUPIRA-PT-PONT-001` aplicado ao artefato final.

| Métrica observada | Sem Curupira | Com Curupira | Delta |
|---|---:|---:|---:|
| findings residuais | 1 | 0 | -1 |
| chamadas de ferramenta | 9 | 10 | +1 |
| mensagens | 11 | 12 | +1 |
| duração da sessão | 41 s | 40 s | -1 s |

O braço baseline preservou `Feche a válvula; desligue a bomba.`. O tratamento
produziu `Feche a válvula. Em seguida, desligue a bomba.` e confirmou zero
findings na segunda execução do linter.

## Materiais de reprodução

- tarefa exata: `corpus/curupira/hermes-agent-pilot-v1/task-single.md`;
- documento de entrada: `corpus/curupira/hermes-agent-pilot-v1/inputs/bomba.md`;
- skill do tratamento: `integrations/hermes-agent/curupira-preflight/SKILL.md`;
- saídas finais: `artifacts/curupira/hermes-agent-pilot-v1/baseline/procedimento.md`
  e `artifacts/curupira/hermes-agent-pilot-v1/curupira/procedimento.md`;
- comparador para rodadas com telemetria de uso:
  `tools/curupira/hermes_agent_ab.py`.

Para reproduzir, iniciar duas sessões interativas limpas com Hermes Agent
0.20.1, Grok 4.6 e raciocínio `low`. Na primeira, enviar a tarefa exata. Na
segunda, prefixar a mesma tarefa com `/curupira-preflight`. Os IDs das sessões
observadas estão no artefato `summary.json`; transcrições do provedor não são
publicadas nem necessárias para verificar os arquivos finais e os findings.

## Interpretação

O piloto demonstra um ganho observado: um erro residual foi removido. O custo
foi uma chamada de ferramenta e uma mensagem adicionais. A diferença de um
segundo é ruído e não sustenta alegação de velocidade. Tokens não foram
comparados porque a superfície interativa que processa slash commands não emite
`--usage-file` no Hermes Agent 0.20.1.

É uma única tarefa sintética, escolhida para testar a regra disponível. Não
prova redução geral de tokens, perguntas ou erros e não estima impacto em
produção. Esses efeitos serão medidos com issues e jornadas autorizadas.
O avaliador de findings residuais é a mesma regra determinística usada no
preflight. Portanto, o resultado demonstra consistência interna do fluxo e não
constitui validação independente de qualidade linguística.

## Limitações descobertas

- `hermes --oneshot --skills curupira-preflight` não aplicou a skill neste
  build; não usar essa rota no preview;
- `hermes chat -s curupira-preflight` carregou contexto, mas não impôs o gate;
- a invocação interativa `/curupira-preflight` foi a única rota que aplicou o
  fluxo completo;
- o primeiro texto da skill detectou o finding, mas não impediu a entrega. O
  contrato foi endurecido para tratar código 1 como tarefa incompleta antes do
  UAT válido.

Dados canônicos e saídas estão em
`artifacts/curupira/hermes-agent-pilot-v1/summary.json`.
