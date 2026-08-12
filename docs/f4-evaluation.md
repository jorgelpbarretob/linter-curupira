# Avaliação das regras preview da Fase 4

Status: corpus seed completo; revisão de documento real aprovada
Data: 2026-08-12

## Método

Cada regra foi executada isoladamente nos 13 casos sintéticos e humanos
aprovados de sua candidata. O conjunto total tem 65 casos legalmente
redistribuíveis. Precisão e recall são estimativas pontuais; o intervalo de
precisão é Wilson bilateral de 95% sobre os diagnósticos emitidos.

| Rule ID | TP | FP | FN | TN | Precisão | IC 95% precisão | Recall |
|---|---:|---:|---:|---:|---:|---:|---:|
| `STE-I9-PUNCT-001` | 5 | 0 | 0 | 8 | 1,00 | 0,566–1,000 | 1,00 |
| `STE-I9-SENT-001` | 6 | 0 | 0 | 7 | 1,00 | 0,610–1,000 | 1,00 |
| `STE-I9-SENT-002` | 6 | 0 | 0 | 7 | 1,00 | 0,610–1,000 | 1,00 |
| `STE-I9-PARA-001` | 5 | 0 | 0 | 8 | 1,00 | 0,566–1,000 | 1,00 |
| `STE-I9-LIST-001` | 5 | 0 | 0 | 8 | 1,00 | 0,566–1,000 | 1,00 |

Apesar de zero falso positivo no seed, o limite inferior dos intervalos está
abaixo de 0,95. Todas as regras permanecem `preview/info` e desabilitadas por
default. Sugestões são omitidas porque nenhuma correção é unívoca.

## Controles de falso positivo

- ponto e vírgula: somente token lintável; código, links, entidades e markup são
  ignorados;
- sentenças: tipo textual explícito; apenas palavras alfabéticas simples;
  números, unidades, parênteses, hifenização, markup ou sentença incompleta
  causam abstenção;
- parágrafo: somente tipo descritivo, bloco separado por linha em branco e
  sentenças completas sem regiões ignoradas;
- lista: somente Markdown, lista direta com ao menos dois itens e lead-in na
  linha imediatamente anterior contendo a palavra `these`; estruturas
  separadas, headings, fences e thematic breaks causam abstenção.

## Documento técnico real

Comando executado no `README.md` do projeto, tratado como texto descritivo e com
as cinco regras explicitamente habilitadas:

```powershell
uv run --no-sync ste lint README.md --format json --text-type descriptive `
  --enable-rule STE-I9-PUNCT-001 --enable-rule STE-I9-SENT-001 `
  --enable-rule STE-I9-SENT-002 --enable-rule STE-I9-PARA-001 `
  --enable-rule STE-I9-LIST-001
```

Resultado final: exit `1`, com dois diagnósticos `STE-I9-PUNCT-001`, nas linhas
14 e 15 da versão avaliada. Ambos apontam para ponto e vírgula em prosa visível
nas linhas de requisitos de Python e uv. O mantenedor revisou e aprovou os dois
achados como úteis e corretos em 2026-08-12.
