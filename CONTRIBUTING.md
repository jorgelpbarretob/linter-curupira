# Contribuindo com o Hermes

Obrigado pelo interesse em português técnico brasileiro aberto.

## Estado atual

O código executável ainda é o protótipo inglês congelado. PT1 está definindo a
especificação e a governança; PT2 construirá o corpus; a migração de código só
começa em PT3. Propostas linguísticas e revisão documental são bem-vindas agora.
Mudanças de pacote, CLI ou regras executáveis aguardam o gate correspondente.

Leia antes de contribuir:

- `PLANS.md`;
- `docs/hermes-controlled-portuguese-spec-0.1.md`;
- `docs/hermes-governance.md`;
- `docs/hermes-identity-and-licensing.md`;
- `docs/hermes-rule-taxonomy.md`.

## Tipos de contribuição

- problema real de clareza em documentação técnica pt-BR;
- proposta autoral de regra;
- exemplos sintéticos positivos, negativos e de borda;
- revisão linguística ou de domínio;
- fonte de corpus com licença redistribuível;
- taxonomia de erro e protocolo de avaliação;
- bug reproduzível no núcleo que será migrado.

## Proposta de regra

Inclua ID provisório, enunciado, racional, público afetado, classe de automação,
unidade detectável, exemplos, abstenções, riscos, dados necessários e plano de
avaliação. Não envie implementação antes de o texto da regra e o corpus
aplicável serem aprovados.

## Licenciamento e proveniência

- código e testes de software são contribuídos sob Apache-2.0;
- especificação, guias, exemplos autorais e rótulos autorais são contribuídos
  sob CC BY 4.0;
- material externo mantém sua licença original e exige proveniência completa;
- ao enviar conteúdo, declare que você o criou ou tem autorização para
  licenciá-lo e distribuí-lo;
- não envie conteúdo confidencial, dados pessoais, norma protegida, corpus sem
  licença ou saída bruta de modelo.

A licença de um rótulo não relicencia o texto rotulado. Em caso de dúvida, abra
uma proposta sem anexar o conteúdo.

## Processo técnico

Depois que um incremento de código for autorizado:

1. siga WIP=1;
2. escreva primeiro o teste que falha;
3. implemente a menor mudança;
4. adicione regressão para cada bug ou erro observado;
5. execute testes, Ruff, formato, mypy e smoke offline;
6. registre métricas e limitações sem promover regra automaticamente.

Chamadas reais à Maritaca nunca pertencem ao CI público. Não inclua chaves,
tokens, documentos reais ou cassettes não sanitizados em issues, commits ou
logs.
