# Painel independente do Curupira preview v1

Status: aprovado por unanimidade  
Date: 2026-08-16

O snapshot final do preview foi revisado isoladamente por três modelos. O
bundle incluiu código, documentação, testes, skill do Hermes Agent, tarefa e
entrada sintéticas, saídas dos dois braços e artefatos agregados. Não incluiu
holdout selado, documentos de usuário ou segredos.

| Provedor | Modelo solicitado e retornado | Veredito | Findings | SHA-256 do voto |
|---|---|---|---:|---|
| Maritaca | `sabia-4-thinking` | approve | 0 | `8f2de786b6a23e5c6cc64cb24f5286049277ab1f6451f4d349af5a3f61159985` |
| xAI | `grok-4.6` | approve | 0 | `76c06ed19dfb9e83736c769e9b555a68a6c62bcd423cdabd2cec80f3e97899c3` |
| Ollama Cloud | `kimi-k2.7-code:cloud` | approve | 0 | `7c6ec35c4c8cf44b73f5ef1b731581f77ad12f7c576a771b10a3a76bf2969b31` |

O manifest canônico do bundle tem SHA-256
`8f0598cb6f6f9c1b9e6ef14b3b70cb5fb748fc939475a065ad50e36628493f3b`.
Cada voto confirmou as mesmas fronteiras: viu o piloto sintético; não viu dados
selados nem documentos de usuário; não atribuiu qualidade estável ao preview.

## Processo

A primeira rodada revelou duas correções funcionais reais e lacunas de teste:
o caminho de `lint` era opcional e uma chave Maritaca composta apenas por
espaços atravessava a validação. A segunda rodada confirmou as correções e
apontou contexto de teste e reprodução ausente no bundle. Após ampliar testes,
documentar os limites de rede e tornar o piloto auto-reprodutível, a terceira
rodada aprovou por unanimidade com zero findings.

Os votos brutos, requests, respostas, metadados e manifest permanecem sob
custódia externa em
`/home/jorge/.curupira/rebrand/20260816-v1/evidence-v3`. Somente esta síntese e
os hashes entram no repositório público para não transformar respostas de
provedores em código ou regra normativa.
