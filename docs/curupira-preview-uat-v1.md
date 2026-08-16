# UAT do Curupira preview v1

Status: protocolo executável
Date: 2026-08-16

## Objetivo

Validar com o Himavai a jornada que um usuário realmente executará, sem acesso
a corpus selado, prompts de desenvolvimento ou respostas do painel técnico.

## Ambiente

Use um ambiente virtual novo e instale o wheel produzido para
`curupira-lint==0.3.0`. O teste deve ocorrer offline depois da instalação. Use
somente documentos sintéticos criados para esta jornada.

## Jornadas

1. Execute `curupira lint` em um `.txt` contendo um ponto e vírgula em prosa e
   confirme o diagnóstico `CURUPIRA-PT-PONT-001` no span correto.
2. Execute o mesmo comando em texto sem ponto e vírgula e confirme a saída sem
   diagnóstico.
3. Execute `curupira analyze` em um `.txt` e confirme o schema
   `curupira-linguistic-analysis/v1` e ausência de envio do documento à rede.
4. Tente habilitar `HERMES-PT-PONT-001` no comando `curupira` e confirme a
   orientação explícita para `CURUPIRA-PT-PONT-001`.
5. Em um ambiente com Hermes Agent, instale a skill `curupira-preflight`, peça
   uma revisão de documentação pt-BR e confirme que ela executa `curupira` sem
   substituir o executável `hermes`.
6. Com texto sintético e `MARITACA_API_KEY`, execute `semantic-review` e confirme
   modelo solicitado/retornado, tokens de uso, hash da fonte e offsets locais.
   Sem a chave, confirme erro operacional sem vazamento de segredo.

## Registro

Registre versão do wheel, SHA-256, ambiente, comandos, códigos de saída e um
resultado `pass` ou `fail` por jornada. Um `fail` bloqueia a publicação; não é
permitido transformar uma falha em aceite por interpretação manual.
