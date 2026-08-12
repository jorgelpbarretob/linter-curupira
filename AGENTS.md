# AGENTS.md — ste-lint

Estas instruções são específicas deste projeto e complementam as instruções do workspace Maltaria. Em conflito, segurança e instruções explícitas do usuário prevalecem.

## Estado do projeto

O projeto está em planejamento. Leia `PLANS.md` por completo antes de agir. Não inicie a Fase 1, não crie o pacote Python e não implemente regras até aprovação explícita do plano pelo usuário.

## Missão

Construir `ste-lint`, um linter Python local-first que ajuda autores a encontrar violações detectáveis do ASD-STE100 Simplified Technical English Issue 9 e produz diagnósticos rastreáveis. A ferramenta não é a norma, não certifica documentos e não substitui revisão humana.

## Regras inegociáveis

1. Issue 9 é a fonte normativa. Não invente locators, obrigações ou exemplos.
2. Não copie para o repositório regras, entradas do dicionário, exemplos, tabelas ou texto extenso protegido. Use referência e paráfrase autoral curta.
3. O vocabulário oficial é recurso externo ao código e não entra em Git, wheel, imagem, fixture ou cassette sem autorização escrita.
4. Classifique cada regra como `deterministic`, `nlp`, `semantic` ou `human-review`.
5. LLM não é fonte de compliance nem ground truth. O lint padrão funciona offline e sem credenciais.
6. Todo `Diagnostic` contém `rule_id`, `source`, `severity`, `location`, `explanation` e `suggestion` opcional.
7. Prefira abstenção a falso positivo. Uma regra que não atinge o gate fica `preview` ou não é emitida.
8. Testes pertencem ao incremento da regra. Não aceite “implementar agora, testar depois”.
9. Não misture política local com norma: IDs `STE-I9-*` exigem fonte verificada; IDs `PROJECT-*` são explicitamente não normativos.
10. Não alegue “ASD approved”, “certified”, “fully compliant” ou equivalente; não use logos da ASD.

## Arquitetura e dependências

- `domain` permanece puro e não importa CLI, filesystem, NLP, semantic ou SDKs externos.
- Regras recebem `RuleContext`; não abrem arquivos e não acessam rede.
- Parsers preservam offsets e distinguem conteúdo lintável de markup.
- Metadados do catálogo e implementação Python são separados; não crie uma DSL genérica sem ADR e necessidade comprovada.
- `nlp` e `semantic` são extras opcionais. Nada deles pode ser importado no caminho padrão de lint.
- Saída deve ser estável e ordenada para a mesma entrada/configuração.

## Processo por regra

Antes de implementar uma regra:

1. confirme a referência na cópia legítima da Issue 9;
2. escreva uma paráfrase curta e registre a classe de automação;
3. descreva condições de abstenção e controles de falso positivo;
4. prepare exemplos autorais: ao menos 3 violações, 3 não violações e 3 edge cases;
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
- confirmação de que nenhum recurso protegido foi adicionado;
- `git status` revisado no repositório correto.

Não trate timeout como sucesso e não esconda falhas preexistentes.

## Mudanças difíceis de reverter

Antes de alterar modelo de offsets, schema JSON, IDs de regras, contrato `Rule`/`Diagnostic`, formato do vocabulário, precedência de configuração, fingerprint de baseline ou postura de licença, registre/atualize um ADR e obtenha aprovação humana.

## Dados, segredos e serviços externos

- Nunca imprima tokens, chaves, senhas ou conteúdo técnico confidencial.
- Não envie documentos a APIs externas sem opt-in explícito para aquela execução.
- Testes e CI não dependem de rede.
- Cassettes futuras devem ser sanitizadas e legalmente redistribuíveis.

## Escopo incremental

Trabalhe com WIP 1 e respeite os gates de `PLANS.md`. Não antecipe NLP, fixer, semantic reviewer, formatos adicionais ou infraestrutura de escala para resolver um requisito da fase atual.

## Relatório final

Use: Resumo | arquivos alterados | validações executadas | resultados | riscos. Inclua comandos realmente executados e deixe explícito o que não foi verificado.
