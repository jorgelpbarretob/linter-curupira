---
name: curupira-preflight
description: Valida documentação técnica em português brasileiro com o Curupira antes da entrega. Use ao criar, revisar ou alterar arquivos Markdown ou TXT pt-BR no Hermes Agent, especialmente procedimentos, manuais, instruções operacionais e documentação de software.
---

# Curupira preflight

Executar uma verificação local e rastreável antes de entregar documentação
técnica pt-BR. Tratar o Curupira como apoio em preview, não como certificação.

## Fluxo

1. Identificar os arquivos `.md` e `.txt` criados ou alterados na tarefa.
2. Executar, para cada arquivo:

   ```bash
   curupira lint ARQUIVO --enable-rule CURUPIRA-PT-PONT-001 --format json
   ```

3. Interpretar o código de saída: `0` significa nenhum finding, `1` significa
   preflight reprovado e tarefa ainda incompleta, e `2` significa erro
   operacional. Nunca finalizar como sucesso depois de código `1`.
4. Se houver finding, escolher a correção pela relação semântica: nova sentença,
   dois-pontos ou lista. Não substituir pontuação cegamente. Para duas ações
   imperativas claramente sequenciais, preferir duas sentenças e explicitar a
   sequência, por exemplo: `Feche a válvula. Em seguida, desligue a bomba.`
5. Executar o comando novamente. Limitar a dois ciclos. Somente código `0`
   permite entregar o arquivo como concluído; se ainda falhar, declarar falha e
   relatar o finding residual com arquivo e span.
6. Informar no resultado final quantos arquivos foram verificados, quantos
   findings foram corrigidos e quantos permaneceram.

Para um `.txt` que precise de evidência estrutural, executar opcionalmente:

```bash
curupira analyze ARQUIVO --format json
```

Não alegar qualidade linguística estável com essa análise; o contrato NLP ainda
é preview.

Executar `curupira semantic-review ARQUIVO` somente quando a tarefa autorizar
explicitamente o envio do documento à API Maritaca. Esse comando não é parte do
preflight local padrão. Tratar observações do Sabiázinho como hipóteses ancoradas,
não como diagnósticos normativos.

## Falhas e limites

- Se `curupira` não existir, não declarar o documento limpo. Informar a ausência
  e sugerir `pip install "curupira-lint[nlp]"` quando a análise NLP for necessária
  ou `pip install curupira-lint` para lint determinístico.
- Não enviar o documento a APIs ou modelos para executar o preflight. O comando
  deve funcionar localmente e offline depois da instalação.
- Não usar corpus, rótulos ou resultados de holdout como material de revisão.
- Não alterar código, URLs, destinos de link ou trechos excluídos apenas para
  satisfazer o linter.
