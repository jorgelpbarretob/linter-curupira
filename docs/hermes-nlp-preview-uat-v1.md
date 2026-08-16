# UAT Himavai — NLP local pt-BR preview v1

Status: Ready for execution
Date: 2026-08-16

## Objetivo

Testar a jornada que um usuário realmente recebe, sem revisar labels: instalar
o extra opcional, analisar um `.txt`, entender a saída, reconhecer limites e
registrar um problema reproduzível.

## Roteiro

1. Em ambiente Python 3.12 limpo, instalar `hermes-lint[nlp]`.
2. Criar `procedimento.txt` com `Ligue a bomba. Depois, abra a válvula.`.
3. Executar `hermes analyze procedimento.txt --format json` com rede bloqueada.
4. Confirmar código de saída zero, JSON parseável, `status=preview`, URI e hash.
5. Conferir por slice que todo token satisfaz
   `texto[start_offset:end_offset] == token.text`.
6. Tentar um arquivo `.md` e verificar erro operacional que explique o escopo.
7. Tentar uma instalação sem o extra e verificar instrução de instalação.
8. Abrir uma issue `NLP preview` com exemplo sintético e resultado esperado.

## Registro

Registrar versão do pacote, plataforma, comandos, códigos de saída, tempo para
concluir, pontos de dúvida e se o formulário permite reproduzir o problema sem
publicar dados privados. Não anexar documento real sem autorização específica.

O resultado é `pass`, `pass-with-friction` ou `fail`, acompanhado de evidência.
Esse resultado informa usabilidade; não altera o `quality-fail` linguístico.
