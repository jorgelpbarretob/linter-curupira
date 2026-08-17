# Estudo de caso Hermes × Curupira — protocolo v1

Status: draft operacional  
Data: 2026-08-16  
Fonte de desenho: anexo mesa `Desenho do estudo.md` (gate inbound 7 findings PONT-001 na origem)

## Objetivo

Transformar a comparação sem/com Curupira em experimento **pareado**, versionado e verificável.

Para cada tarefa de documentação técnica pt-BR, executar Hermes **sem Curupira** e **com** `/curupira-preflight`. Manter constantes: modelo, prompt-base, repositório, orçamento e critérios de aceite.

O resultado separa:

1. **tokens de sessão** (KPI primário de custo)
2. **legibilidade** do artefato para o usuário/operador (KPI primário de valor)
3. qualidade residual (lint) e requisitos técnicos (gates)
4. custo operacional (tools, tempo) e impacto específico do preflight

Detalhe: `product-goals-tokens-readability.md`.

## Desenho

| Elemento | Definição |
|---|---|
| Unidade experimental | Uma tarefa fechada de documentação técnica em pt-BR |
| Controle | Hermes sem skill Curupira |
| Tratamento | Hermes com `/curupira-preflight` |
| Pareamento | Mesma tarefa nas duas condições, execuções independentes |
| Constantes | Modelo, versão Hermes, prompt-base, permissões, repo, tempo e orçamento de chamadas |
| Variável | Skill Curupira e lint registrado |
| Avaliação | Rubrica cega, checks automatizados e aceite humano |
| Repetições | ≥3 por condição/tarefa se o agente for não determinístico. Reportar mediana e dispersão |

Defina “pronto” **antes** de cada rodada: artefato esperado, restrições, teste de aceite, evidência exigida e condição de parada do agente.

## Banco de tarefas

Conjunto alvo: **12 a 20** tarefas em `cases/`, dificuldade variada.

Evite tarefas abertas do tipo “melhore este documento”. Prefira entregáveis objetivos com:

- arquivo inicial
- mudança solicitada
- critérios de aceite observáveis

Tipos:

| Tipo | Exemplo | O que mede |
|---|---|---|
| Criação | Procedimento de recuperação de serviço | Estrutura, precisão, clareza |
| Revisão | Corrigir instrução sem mudar fatos | Ambiguidade e preservação de sentido |
| Atualização | Runbook após mudança de API/CLI | Consistência fonte↔doc |
| Transformação | Notas → procedimento Markdown | Passos acionáveis e cobertura |
| Incidente | Pós-incidente a partir de logs sanitizados | Rastreabilidade, sem inferência indevida |
| Regressão | Inserir problemas cobertos por regras Curupira | Prevenção/remoção de achados conhecidos |

Misture tarefas reais anonimizadas (com autorização) e semissintéticas. Preserve holdouts separados. Não ajuste o fluxo ao conjunto de avaliação.

## Protocolo por rodada

1. **Congelar o caso.** Versione entradas, artefato inicial, fontes, rubrica e comandos de validação. Gere hash do pacote (`manifest.json`).
2. **Executar controle.** Hermes sem Curupira. Registrar transcrição, chamadas, duração, artefato final, diffs e falhas.
3. **Executar tratamento.** Mesma tarefa com `/curupira-preflight`. Exigir correção ou justificativa para cada finding aplicável.
4. **Validar automaticamente.** Testes do repo, links/Markdown e `curupira lint` com regras do aceite. Rodar o lint também no artefato do **controle**, só depois da entrega, para medir residual.
5. **Avaliar cegamente.** Remover identificação de condição. Dois revisores aplicam a rubrica.
6. **Resolver divergências.** Concordância entre revisores. Acima do limiar, desempate por terceiro revisor documentado.
7. **Registrar aceite.** Classes: aceito, aceito com retrabalho menor, rejeitado com retrabalho maior, bloqueado.

Não altere prompts, critérios ou casos depois de observar a primeira execução de avaliação. Mudança de protocolo exige **nova versão** e relatório separado.

## Métricas

Publicar valores **por tarefa** e agregados. Preferir mediana a média para tempos e chamadas.

| Dimensão | Métrica | Cálculo |
|---|---|---|
| Qualidade Curupira | Achados residuais habilitados | Diagnósticos no artefato final com as mesmas regras nas duas condições |
| Qualidade editorial | Nota da rubrica | Média ou mediana cega por critério e total |
| Aceite | Taxa na 1ª revisão | Aceitas sem retorno / concluídas |
| Retrabalho | Ciclos até aceite | Devoluções ou edições humanas |
| Eficiência | Tempo até aceite | Início → aprovação final (com retrabalho) |
| Custo de agente | Chamadas e turnos | Contagem por rodada. Comparar acréscimo do preflight |
| Custo de modelo | Tokens e custo | Só se a superfície Hermes expor |
| Segurança factual | Erros técnicos críticos | Contagem da rubrica, sempre separada |
| Aderência | Violações de requisitos | Obrigatórios falhos / total |
| Valor percebido | Utilidade do revisor | Escala 1–5 pós-revisão |

Piloto sintético inicial: findings 1→0 com +1 chamada. Tokens não medidos. Trate como sinal preliminar, não como generalização.

## Critério de sucesso

Sucesso é balanço qualidade×custo, não só queda de findings:

- redução consistente de achados residuais nas tarefas aplicáveis
- ganho ou manutenção da taxa de aceite na 1ª revisão
- nenhum aumento de erros técnicos críticos
- aumento de chamadas/tempo dentro de orçamento explícito (ex.: +1 chamada se elimina retrabalho)
- revisores consideram o resultado ao menos tão útil quanto o controle
- evidência reprodutível publicada (casos, versões, rubrica, dados, limitações)

## Ligação operacional (esta mesa)

- Coleta diária de uso: cron `curupira-uso-diario`
- Funil improve: `curupira_improve_collect.py` (semantic só com provenance)
- Gate inbound mesa: anexos md/txt + paste ≥600 chars (lint only)
- Execução A/B de casos: este protocolo + `tools/curupira/run_case_study_round.py` (esqueleto)

## Versão

- protocol-v1
- curupira-lint alvo: 0.3.0-preview
- skill: `curupira-preflight`
