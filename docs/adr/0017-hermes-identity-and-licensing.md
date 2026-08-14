# ADR-017: identidade Hermes e fronteiras de licenciamento

Status: Accepted
Date: 2026-08-13

## Contexto

O pivot pt-BR do ADR-016 deixou nome, pacote, comando, namespace e licenças como
gates do PT1. A identidade precisa ser decidida antes de migrar contratos ou
publicar regras, mas o repositório atual ainda contém a linha inglesa congelada.

O código já está sob Apache License 2.0. Essa licença concede permissões amplas
de uso, modificação e distribuição e inclui uma licença expressa de patentes,
sujeita às suas condições.[1]

CC BY 4.0 permite compartilhar e adaptar material, inclusive comercialmente,
desde que haja atribuição adequada, link para a licença e indicação de
alterações.[2]

## Decisão

### Identidade alvo

- produto: **Hermes**;
- repositório: `hermes-STL-IA-PT`;
- distribuição Python: `hermes-lint`;
- pacote importável: `hermes_lint`;
- comando: `hermes`;
- namespace de regras: `HERMES-PT-*`.

O diretório, pacote `ste-lint`, módulo `ste_lint` e comando `ste` atuais ficam
inalterados até PT3. Não haverá renomeação parcial.

### Licenças

- código, configuração executável e testes de software: `Apache-2.0`;
- especificação Hermes, guia de anotação, documentação linguística, exemplos
  autorais, rótulos humanos autorais e corpus inteiramente criado pelo projeto:
  `CC-BY-4.0`;
- textos, corpora, modelos, léxicos e outros recursos de terceiros: licença de
  origem, sem relicenciamento pelo Hermes;
- metadados factuais e hashes não alteram os direitos do conteúdo a que se
  referem.

Um cabeçalho SPDX ou manifesto por diretório identificará a licença aplicável.
Nenhum diretório com fontes mistas receberá uma licença abrangente ambígua.

### Contribuições

Contribuições de código são submetidas sob Apache-2.0 conforme a política do
repositório. Contribuições de especificação, exemplos, corpus autoral e rótulos
exigem declaração CC BY 4.0 e confirmação de autoria ou autorização.

Texto externo só pode ser incluído com URL de origem, titular quando conhecido,
licença, versão/snapshot, transformações e confirmação de redistribuição. Uma
licença incompatível bloqueia inclusão; não será contornada por paráfrase
automática ou saída de modelo.

Respostas brutas da Maritaca são artefatos operacionais, não corpus público por
padrão. Somente estruturas sanitizadas, necessárias e humanamente adjudicadas
podem virar evidência publicada depois de revisão de termos, privacidade e
direitos.

## Consequências

- A identidade pública fica estável antes da migração, evitando nomes mistos no
  contrato novo.
- Apache-2.0 existente é preservada; não há relicenciamento retroativo.
- A separação Apache/CC BY exige manifestos e checagem de paths na release.
- CC BY 4.0 não torna automaticamente redistribuível um texto de terceiro.
- `NOTICE` e README continuam descrevendo a linha inglesa até a migração PT3.
- Esta decisão é política de projeto e não substitui aconselhamento jurídico.

## Implementação documental

- política: `docs/hermes-identity-and-licensing.md`;
- especificação proposta: `docs/hermes-controlled-portuguese-spec-0.1.md`;
- governança proposta: `docs/hermes-governance.md`;
- taxonomia proposta: `docs/hermes-rule-taxonomy.md`.

## Aprovação

Aceito explicitamente pelo mantenedor em 2026-08-13 ao autorizar a configuração
recomendada de identidade e licenças e mandar continuar o PT1. A grafia da
identidade alvo foi corrigida pelo mantenedor no mesmo dia, sem mudança da
decisão de produto.

## Sources

[1] https://www.apache.org/licenses/LICENSE-2.0 — Apache License 2.0
[2] https://creativecommons.org/licenses/by/4.0 — Creative Commons Attribution 4.0
