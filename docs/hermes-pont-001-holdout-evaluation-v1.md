# Avaliação holdout v1 de HERMES-PT-PONT-001

Status: Accepted — decisão `preview`
Date: 2026-08-14

## Resultado

O detector congelado de `HERMES-PT-PONT-001` foi executado uma única vez no
holdout Kubernetes congelado. A execução ocorreu antes da abertura dos labels,
persistiu somente identificadores, hashes, offsets e contagens e não gravou
texto-fonte. O Grok, atuando como aprovador delegado pelo mantenedor, autorizou
a abertura do ground truth depois de verificar o isolamento e os hashes.

O score reproduzido foi:

| Medida | Resultado |
|---|---:|
| TP / FP / FN / TN | 148 / 4 / 15 / 242 |
| Precisão | 0,973684 |
| IC Wilson 95% da precisão | [0,934296; 0,989720] |
| Recall | 0,907975 |
| IC Wilson 95% do recall | [0,853726; 0,943438] |
| Span accuracy | 0,973684 |
| FP por 1.000 palavras lintáveis | 0,026628 |
| Erros de offset / diagnósticos sem unidade | 0 / 0 |
| Erros de região | 4 |

Foram avaliados 409 casos: 163 `violation`, 173 `out_of_scope` e 73
`non_violation`. A execução produziu 152 diagnósticos em 150.220 palavras
lintáveis. Os identificadores dos 4 falsos positivos e 15 falsos negativos
permanecem sob custódia e não foram incorporados a testes ou fixtures.

## Gates e decisão

| Gate pré-registrado | Resultado |
|---|---|
| precisão pontual >= 0,95 | passou |
| limite inferior Wilson 95% >= 0,95 | falhou: 0,934296 |
| zero falso positivo conhecido | falhou: 4 FP |
| ao menos 73 unidades positivas | passou: 163 |
| recall e abstenção publicados | passou |

O parecer estruturado pós-holdout do Grok foi `preview`. A regra é útil e
reproduzível, mas não satisfaz os gates de promoção a `stable`. Uma análise de
sensibilidade mostrou que, mantidos os quatro falsos positivos, seriam
necessários mais 50 verdadeiros positivos sem erro apenas para elevar o limite
inferior Wilson a 0,95; isso ainda não atenderia ao gate de zero FP.

O detector não será ajustado com base neste holdout. Os 19 casos de erro ficam
selados neste ciclo. Se uma decisão futura abrir rework, eles passam a conjunto
de challenge e qualquer nova promoção exigirá outro holdout independente.

## Artefatos e custódia

- detector freeze manifest SHA-256:
  `29bfebaeab126a33d7d0f4aaae44f83d53dd22f03496e30758693d0d9212bae8`;
- detector SHA-256:
  `972a1c67e14d4316afc388df523838f4338a60d5866ab13710d19bda1fc016b9`;
- holdout manifest SHA-256:
  `3eaf4069017593c4f9e0d0c573736899ccbf137e3792ba97161e94d0663f86e7`;
- ground truth SHA-256:
  `6cab9e0a4090df19fc5c3cc5a8e93122413160f523e032367ec25849567abab6`;
- primeira execução SHA-256:
  `eac833da22cf7c6d81a53a273cd067e32bbb734af075d0bb92f5b766db142333`;
- métricas SHA-256:
  `ec38740c65dd2c5d081f8e1080f637264f237e121580fd29c322d1a971144e37`;
- auditoria quantitativa independente SHA-256:
  `195baf37109a4db937ce40ff1707cbfa851548a79bb433110e6aa0d727306fed`;
- aprovação delegada para abrir labels SHA-256:
  `fba62fb4d1f87336e9b721c406b26dee7a97591e588599120589611cee424eb8`;
- decisão delegada pós-holdout SHA-256:
  `b0e6f0c62ef7656a053dbd6222492267a322dfb4b17d32130acb59039009f623`.

Resultados, labels e aprovações estruturadas permanecem em
`/home/jorge/.hermes/holdout-custody/`; somente métricas agregadas e hashes são
publicados no Git.

## Aprovações delegadas

Na abertura dos labels, `grok-4.6-build` retornou `approve_open_labels`, sem
findings, para o bundle SHA-256
`f8a258839275a254abbd63d4f0bbf3c0471c00748f8754bc99ded25b8faec874`.
Request ID: `66a881fd-0b9e-43f6-b972-8b3431741fd3`; custo reportado:
US$ 0,04791314.

Na decisão final, o mesmo modelo retornou `preview` para o bundle SHA-256
`68af485fe971a5be0135107ae1f79c8bc5a4f60f936fcf4dd6caeef908bff422`.
Request ID: `5af47aaa-4546-4a9f-8bd3-a0b1acc37781`; custo reportado:
US$ 0,02746214. Prompts, schemas, IDs de sessão e contagens de tokens constam
nos registros estruturados sob custódia.

## Auditoria independente

`tools/hermes/audit_pont_001_metrics.py` recomputou matriz, precisão, recall,
intervalos Wilson completos, span accuracy, erros de região, taxa de FP,
recortes por domínio e gates sem importar o scorer. O veredito foi `CONFIRMED`,
com deltas absoluto e relativo iguais a zero. Os comandos
`prime-quant` e `prime-quant-sync` não estavam disponíveis neste ambiente; a
recomputação foi executada no virtualenv do projeto usando somente a biblioteca
padrão do Python, e o caminho independente recebeu testes próprios.
