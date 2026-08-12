# Contrato do parser TXT/Markdown

Status: implementado na Fase 2
Data: 2026-08-12

## Entrada e identidade de texto

Os adapters recebem texto Unicode já decodificado e não abrem arquivos. O
`Document.text` preserva exatamente a `str` recebida, inclusive LF, CRLF e
caracteres Unicode. Offsets são índices de code points em intervalos semiabertos
`[start, end)`; linha e coluna são projeções 1-based sobre o texto original.

Regiões e tokens formam partições contíguas do texto. A concatenação dos tokens
e dos recortes das regiões reproduz a entrada. Sentenças são uma visão mínima
somente das regiões lintáveis; a pontuação `.`, `!` e `?` encerra sentença e um
fragmento final pode ficar marcado como incompleto.

O limite inicial é 1.000.000 de code points por documento. Acima dele, o parser
se abstém com `DocumentTooLargeError` antes de classificar markup.

## Formatos

- `.txt`: todo o conteúdo é lintável.
- `.md` e `.markdown`: prosa visível é lintável; a sintaxe configurada abaixo é
  ignorada de forma conservadora.
- `.docx`, `.html`, `.pdf` e extensões desconhecidas: não suportadas e rejeitadas
  explicitamente por `UnsupportedFormatError`.

## Subconjunto Markdown suportado

São ignorados front matter fechado por `---` ou `...`, headings ATX e Setext,
fenced code, indented code, tabelas pipe, definições de referência, marcadores de
lista/citação, inline code, autolinks, imagens, tags HTML, destinos e delimitadores
de links, escapes e delimitadores simples de ênfase. O label visível de um link e
a prosa após marcadores de lista/citação continuam lintáveis.

Um fence não fechado é ignorado até o fim do documento. Pontuação incompleta que
não forma uma construção reconhecida permanece prosa. O parser não promete
compatibilidade integral com CommonMark e não produz AST; construções ambíguas
devem ser tratadas por abstenção ou por evolução acompanhada de testes.

## Limites e segurança

O parser é determinístico, usa apenas a biblioteca padrão e não acessa rede,
filesystem, vocabulário oficial ou serviços externos. Ele não interpreta HTML,
não executa código e não representa uma análise normativa ASD-STE100.
