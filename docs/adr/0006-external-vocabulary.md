# ADR-006: vocabulário externo e versionado

Status: Accepted
Data: 2026-08-12

## Contexto

O vocabulário oficial é protegido e sua interpretação pode depender de classe
gramatical e significado. Embuti-lo no código ou nos testes cria risco legal e
acoplamento de release.

## Decisão

Adotar BYO vocabulary: recurso externo ao Git, wheel, imagem, fixture e
cassette. O projeto define schema e loader; testes usam um mini-vocabulário
inteiramente sintético. Provenance registra issue, schema e hash, sem conteúdo
fonte.

## Consequências

- Instalação base e CI não dependem do recurso oficial.
- Recurso ausente, corrompido ou de issue errada deve falhar com orientação.
- Distribuição de dados derivados exige autorização e revisão jurídica próprias.

## Aprovação

Aceita explicitamente pelo mantenedor em 2026-08-12 para a arquitetura do
projeto. Uma revisão jurídica/licenciamento continua necessária antes da Fase 5
ou de qualquer distribuição de dados derivados.
