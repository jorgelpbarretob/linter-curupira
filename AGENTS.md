# AGENTS.md — Hermes

Estas instruções são específicas deste projeto e complementam as instruções do workspace Maltaria. Em conflito, segurança e instruções explícitas do usuário prevalecem.

## Estado do projeto

O pivot pt-BR foi aceito em 2026-08-13 e está registrado no `ADR-016`. Leia
`PLANS.md` por completo antes de agir. PT1 está aceito. O lado de corpus de
`PT2 — corpus e protocolo de avaliação`, limitado a `HERMES-PT-PONT-001`, foi
congelado em 2026-08-14. PT3 foi autorizado, implementado, revisado externamente
e congelado em 2026-08-14. A primeira execução isolada no holdout foi concluída
e avaliada na mesma data. O resultado ficou `preview`; manifesto, hashes,
métricas agregadas e decisão estão em
`docs/hermes-pont-001-holdout-evaluation-v1.md`.

PT4 foi aberto documentalmente em 2026-08-16. O contrato aceito está no
`ADR-019`, o protocolo pré-registrado em
`docs/hermes-pt4-bakeoff-protocol.md` e o gate Grok em
`docs/hermes-pt4-grok-opening-review.md`. Ainda não há backend escolhido, modelo
ou dependência integrado ao projeto ou regra PT5 aberta. Não antecipe essas
etapas. O candidato Stanza permanece condicional a um gate de licença que o
Grok não pode resolver.

Gate 0 de PT4 foi aceito com condições pelo parecer operacional delegado em
2026-08-16. spaCy 3.8.15 + `pt_core_news_sm` 3.8.0 está `eligible` somente para
o bake-off; Stanza está `ineligible-license` sem download. Evidência:
`docs/hermes-pt4-gate0-eligibility-v1.md` e
`docs/hermes-pt4-gate0-grok-review-v1.md`. O modelo spaCy foi apenas instalado e
carregado sem texto em ambiente externo; não entrou no projeto.

O ADR-020 substituiu gates humanos prospectivos por unanimidade de um painel
isolado com `sabia-4-thinking`, `grok-4.6` e `kimi-k2.7-code:cloud`; testes de
usuário pertencem à Himavai. PetroGold `r2.18` e o ambiente estão congelados. A
proposta autoral v2 corrigiu sete inconsistências, passou validação mecânica e
recebeu três votos válidos `approve` em 160/160 casos. O corpus canônico foi
congelado com SHA-256
`45716b0581ae7c90897a3d088953ac8efde13882e6c4ef7ecfa87c6764928f5d`.
O harness PT4 e o adapter experimental spaCy foram implementados em TDD,
congelados e aprovados por unanimidade do painel em 2026-08-16. Código, testes,
projeções e hashes estão em `docs/hermes-pt4-harness-v1.md`,
`docs/hermes-pt4-spacy-adapter-v1.md` e `artifacts/hermes/pt4-*`. O próximo WIP
é a primeira inferência controlada e o selamento dos outputs em custódia
externa. Escolha de backend, porta de produto e PT5 continuam fechadas; nenhuma
inferência candidata ocorreu até este estado.

O piloto de 40 labels já foi aceito e congelado. O snapshot pt-BR do Kubernetes
foi aceito como fonte de holdout em 2026-08-14 e o manifesto sem labels foi
congelado conforme `docs/hermes-pt2-holdout-source-assessment.md`. Não gere
labels, não execute o linter e não use casos do holdout para ajustar detector,
prompt, threshold ou fixture. O pacote histórico de revisão cega foi preparado
fora do repositório com 409 decisões inicialmente `pending-human-review`; esse
estado foi resolvido no ciclo PT2 já congelado e não define o fluxo prospectivo.
Em 2026-08-14, o mantenedor autorizou Grok como revisor delegado e aprovou a
emenda operacional em `docs/hermes-pt2-grok-review-protocol.md`. A revisão Grok
foi concluída sem fila crítica. O mantenedor aprovou o hash do ground truth e os
bytes foram congelados sob custódia externa. Depois do congelamento do detector,
o mantenedor autorizou a primeira execução e delegou ao Grok os gates
operacionais rotineiros. O Grok aprovou a abertura dos labels e decidiu
`preview` após o score. Labels não entram no Git.

Este holdout está consumido e não pode ser reutilizado para ajustar ou promover
o detector. Não abra os 4 FP nem os 15 FN para implementação, threshold,
exceção ou fixture neste ciclo. Somente uma decisão explícita de `rework` pode
movê-los para challenge; uma promoção posterior exigirá novo holdout
independente.

A identidade aceita e aplicada à distribuição é: produto Hermes, repositório
`hermes-STL-IA-PT`, pacote `hermes_lint`, CLI `hermes` e namespace
`HERMES-PT-*`. `src/ste_lint` permanece somente como linha histórica congelada
e não entra no wheel Hermes.

## Missão

Construir um linter Python open source, português-first, que ajude autores a
produzir documentação técnica clara e consistente em português brasileiro. O
produto combina regras locais reproduzíveis com análise semântica remota
opt-in, produz diagnósticos rastreáveis e separa validação por painel de modelos
dos testes de usuário conduzidos pela Himavai.

## Regras inegociáveis

1. A fonte de produto será uma especificação autoral aberta de português técnico
   controlado. Não traduza nem reutilize IDs, obrigações ou exemplos da
   ASD-STE100.
2. Não copie para o repositório regras, entradas de dicionários, exemplos,
   tabelas ou texto extenso protegido. Dados e exemplos devem ter licença e
   proveniência explícitas.
3. Corpus, vocabulários e glossários externos não entram em Git, wheel, imagem,
   fixture ou cassette sem licença compatível e autorização registrada.
4. Classifique novas regras como `deterministic`, `nlp` ou `semantic`.
   `human-review` é histórico e depreciado pelo ADR-020.
5. `sabiazinho-4` é o motor `semantic`; `sabia-4-thinking` é o
   voto Maritaca do painel. Nenhum modelo é sozinho ground truth; novos
   artefatos exigem unanimidade com Grok e Kimi 2.7. O núcleo determinístico
   funciona offline e sem credenciais.
6. Todo `Diagnostic` contém `rule_id`, `source`, `severity`, `location`, `explanation` e `suggestion` opcional.
7. Prefira abstenção a falso positivo. Uma regra que não atinge o gate fica `preview` ou não é emitida.
8. Testes pertencem ao incremento da regra. Não aceite “implementar agora, testar depois”.
9. IDs `STE-I9-*` pertencem somente à linha inglesa congelada. O namespace pt-BR
   será definido antes da primeira regra e não poderá sugerir vínculo com a ASD.
10. Não alegue certificação, cobertura integral ou conformidade além das regras
    avaliadas e publicadas.

## Arquitetura e dependências

- `domain` permanece puro e não importa CLI, filesystem, NLP, semantic ou SDKs externos.
- Regras recebem `RuleContext`; não abrem arquivos e não acessam rede.
- Parsers preservam offsets e distinguem conteúdo lintável de markup.
- Metadados do catálogo e implementação Python são separados; não crie uma DSL genérica sem ADR e necessidade comprovada.
- `nlp` local e `semantic` remoto são capacidades opcionais. SDKs externos não
  atravessam suas portas nem são importados pelo caminho determinístico.
- o provider semântico e o avaliador são módulos separados, com prompts,
  schemas, credenciais, budgets e artefatos independentes.
- Saída deve ser estável e ordenada para a mesma entrada/configuração.

## Processo por regra

Antes de implementar uma regra:

1. confirme o locator na versão publicada da especificação autoral pt-BR;
2. escreva o enunciado autoral e registre a classe de automação;
3. descreva condições de abstenção e controles de falso positivo;
4. prepare exemplos pt-BR autorais: ao menos 3 violações, 3 não violações e 3 edge cases;
5. implemente o teste que falha;
6. implemente a menor lógica que o faz passar;
7. rode unitários, integração offline e corpus rotulado;
8. só marque `stable` se cumprir o gate de precisão de `PLANS.md`.

Bug de produção, falso positivo, falso negativo ou crash deve gerar fixture de regressão minimizada no mesmo change set.

## Verificação mínima

Quando a Fase 1 definir as ferramentas, mantenha comandos canônicos no README/PLANS. Uma entrega de código não está pronta sem:

- testes relevantes;
- lint;
- typecheck;
- smoke offline da CLI;
- confirmação de licença e proveniência de todo dado adicionado;
- `git status` revisado no repositório correto.

Não trate timeout como sucesso e não esconda falhas preexistentes.

## Mudanças difíceis de reverter

Antes de alterar modelo de offsets, schema JSON, IDs de regras, contrato
`Rule`/`Diagnostic`, formato do vocabulário, precedência de configuração,
fingerprint de baseline ou postura de licença, registre/atualize um ADR e
aplique o gate do ADR-020. A aprovação explícita do mantenedor continua válida
para mudar a própria governança.

## Dados, segredos e serviços externos

- Nunca imprima tokens, chaves, senhas ou conteúdo técnico confidencial.
- Não envie documentos a APIs externas sem opt-in explícito para aquela
  execução e sem enquadramento na classe de egress aprovada.
- Use somente `MARITACA_API_KEY` em variável de ambiente ou secret manager;
  nunca persista seu valor.
- Registre alias solicitado e modelo retornado, hashes de prompt/schema/entrada,
  response ID, tokens, latência e data sem persistir conteúdo confidencial.
- Testes e CI não dependem de rede.
- Cassettes futuras devem ser sanitizadas e legalmente redistribuíveis.

## Escopo incremental

Trabalhe com WIP 1 e respeite os gates de `PLANS.md`. Não antecipe NLP, fixer, semantic reviewer, formatos adicionais ou infraestrutura de escala para resolver um requisito da fase atual.

## Relatório final

Use: Resumo | arquivos alterados | validações executadas | resultados | riscos. Inclua comandos realmente executados e deixe explícito o que não foi verificado.
