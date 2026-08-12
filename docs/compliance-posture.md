# Postura de compliance, copyright e marca

Status: aprovada para a fundação open source
Escopo: código, documentação, testes, dados e comunicação do `ste-lint`

Distribuição pretendida: open source. Essa decisão aplica-se ao código; não
autoriza publicar a norma, o vocabulário oficial ou dados derivados protegidos.
O código usa Apache-2.0. O repositório remoto pode permanecer privado durante o
desenvolvimento e deve passar por revisão de conteúdo antes de ficar público.

## O que o produto é

`ste-lint` é uma ajuda local à autoria e à revisão de documentos técnicos em
inglês. Ele produz diagnósticos rastreáveis para um subconjunto explicitamente
habilitado de detectores. A decisão final continua humana.

## O que o produto não alega

- Não é a ASD-STE100 e não substitui a cópia oficial.
- Não certifica, aprova ou garante conformidade integral.
- Não é endossado, autorizado ou aprovado pela ASD ou pelo STEMG.
- Não usa logos da ASD.
- Ausência de diagnósticos significa apenas que as regras habilitadas não
  detectaram uma violação.

## Controles de conteúdo

- O repositório armazena somente referências curtas e paráfrases autorais.
- Regras, exemplos, tabelas, entradas de dicionário e trechos extensos da norma
  não entram em Git, wheel, imagem, fixture, cassette ou prompt versionado.
- O vocabulário oficial é um recurso BYO externo, fornecido por usuário que tenha
  direito de usá-lo.
- Testes públicos usam somente dados sintéticos ou conteúdo com licença e
  provenance registradas.
- Hash, issue e versão de schema podem ser registrados sem persistir o conteúdo
  protegido.
- Distribuição pública ou comercial exige revisão jurídica e de marca separada.
- Antes da primeira publicação, o mantenedor deve escolher a licença do código e
  confirmar que cada arquivo de corpus é sintético ou tem licença compatível.

## Controles de automação

- A Issue 9 é a única fonte normativa para IDs `STE-I9-*`.
- LLM não cria obrigação, locator ou ground truth.
- Regras locais usam IDs `PROJECT-*` e são apresentadas como política do projeto.
- Detectores incertos abstêm-se ou permanecem `preview`.
- O lint padrão funciona offline e não envia documentos a serviços externos.

## Evidência oficial consultada

Consultado em 2026-08-12:

- https://www.asd-ste100.org/ — identifica Issue 9, data da edição e titularidade
  de copyright e marca.
- https://www.asd-ste100.org/STE_downloads.html — orienta a solicitar uma cópia
  oficial e reforça que IA não substitui a referência e a revisão profissional.
- https://www.asd-ste100.org/STEsoftware.html — declara que ferramentas são
  auxiliares, não são certificadas/endossadas e podem produzir feedback incorreto.

Esta postura é controle arquitetural de risco, não parecer jurídico.
