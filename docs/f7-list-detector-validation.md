# Validação do endurecimento de `STE-I9-LIST-001`

Status: independently-reviewed-not-promoted
Data: 2026-08-13
Python: CPython 3.12.13
Gerenciador: uv 0.11.14 executado isoladamente por `uvx`

Nota histórica: este documento registra o baseline do commit `0c5bee6`. A
Emenda 3 posterior substitui a restrição de uma única sentença; resultados e
comandos abaixo não foram reescritos retroativamente.

## Escopo

Esta tranche endurece somente o detector `preview` existente para exigir:

- terminal `these <single-plural-head>.`;
- exatamente uma sentença completa e contígua cobrindo a linha do lead-in;
- os controles Markdown/lintabilidade/lista direta já existentes.

Não adiciona fixer, provider, comando, schema, `safe_autofix` ou promoção para
`stable`.

## TDD observado

1. RED: o caso de pronome nu `these` seguido por ações independentes produziu um
   diagnóstico indevido.
2. GREEN: o terminal lexical estreito removeu o achado e preservou os três
   positivos unitários existentes.
3. RED: duas sentenças na mesma linha ainda produziram diagnóstico.
4. GREEN: a regra passou a exigir uma única `Sentence` completa, contígua e
   coincidente com o conteúdo aparado da linha.
5. A tranche aprovada foi ligada à API pública `Rule.check`; todo diagnóstico
   emitido também prova span exato `.`.

## Contrato quantitativo

Decisão: avaliar readiness para expansão, não promoção. Unidade: um documento
sintético aprovado contendo uma lista candidata. Source of truth:

- 13 labels seed aprovadas em 2026-08-12;
- 16 labels F7 aprovadas pelo mantenedor em 2026-08-13 e revisadas externamente.

Métrica primária: precisão por emissão com Wilson bilateral de 95%. Casos
ambíguos são contados separadamente; emissão ambígua é unsafe.

## Resultado independente

| Métrica | Resultado |
|---|---:|
| Casos totais | 29 |
| TP | 11 |
| FP | 0 |
| FN | 3 |
| TN | 9 |
| Emissões ambíguas | 0 |
| Abstenções ambíguas | 6 |
| Precisão | 1,000 |
| Wilson 95% da precisão | 0,741–1,000 |
| Recall | 0,786 |

Na tranche F7 isolada, a política anterior tinha 6/10 emissões desejadas,
precisão provisória 0,60. Depois do endurecimento, são 6/6, delta absoluto
+0,40 e relativo +66,7%. A comparação usa as mesmas 16 labels, mas elas foram
criadas para desafiar a falha observada e não estimam prevalência operacional.

## Sensibilidade e incerteza

- 72/72 emissões corretas dão limite inferior 0,949348827404: falha o gate.
- 73/73 dão 0,950007992044: primeiro total que passa com zero FP.
- com as 11 emissões corretas atuais, faltam no mínimo 62 sem FP;
- com um FP, o mínimo sobe para 110 emissões totais.

Wilson por caso é a convenção do projeto, mas os casos compartilham templates e
não são observações IID de produção. A matemática está confirmada; validade
externa e data fitness continuam insuficientes para promoção.

## Veredicto quantitativo

`CONFIRMED_WITH_CAVEATS` para o endurecimento: o resultado reproduz as labels
aprovadas e remove as quatro emissões fora da política na tranche F7.

`INSUFFICIENT_EVIDENCE` para `stable` e autofix: o limite inferior é 0,741, a
amostra é sintética/correlacionada e não há corpus técnico amplo independente.

## Validações executadas

| Comando | Resultado |
|---|---|
| testes focados antes da mudança | 10 passed |
| RED pronome nu | falhou como esperado |
| GREEN pronome + positivos existentes | 4 passed |
| RED duas sentenças | falhou como esperado |
| GREEN duas sentenças + positivos | 4 passed |
| regra + corpora seed/F7 | 14 passed |
| suíte completa | 208 passed, 4 skips NLP esperados |
| `ruff check .` | passed |
| `ruff format --check .` | passed após formatação mecânica de um teste |
| `mypy src` | passed; 33 arquivos |
| smoke `ste lint` sem regra estável | passed; exit 0 |

O runtime `prime-quant` indicado pela skill quantitativa e seu comando de sync
não existem no host. O cálculo foi rederivado sem dependências no Python 3.12.13
pinado do projeto; nenhum resultado anterior foi usado como fórmula de entrada.

## Revisão independente pós-implementação

Após autorização explícita do mantenedor para os nove arquivos, o
`cursor-agent --mode ask --model composer-2.5-fast` aprovou o endurecimento
`preview` para commit sem bloqueio material. O parecer confirmou alinhamento
estático com as 29 labels e o span exato do ponto final, e reiterou que a
evidência não autoriza `stable`, `safe_autofix` nem implementação do fixer.

Os achados não bloqueantes foram tratados assim:

- linha em branco antes da lista e indentação fora de 0–3 espaços foram
  registradas como limites conservadores de recall;
- o default `safe_autofix = false` foi confirmado no contrato de
  `RuleMetadata`, e regras `preview` continuam desabilitadas por default em
  `resolve_enabled_rule_ids`; um teste específico protege o metadata da regra;
- a fotografia quantitativa antiga da spec do fixer foi atualizada de 5 para
  11 emissões corretas e de Wilson 0,566 para 0,741;
- o corpus seed passou a conferir também que todo diagnóstico aponta exatamente
  para `.`.

## Próximo gate

1. expansão com famílias diversas e controles adversariais adicionais;
2. aprovação humana das novas labels;
3. nova avaliação antes de qualquer promoção/provider.
