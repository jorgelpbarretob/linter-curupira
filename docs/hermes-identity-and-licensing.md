# Identidade e política de licenciamento do Hermes

Status: Accepted
Date: 2026-08-13

## Identidade

| Superfície | Identidade alvo |
|---|---|
| Produto | Hermes |
| Repositório | `hermes-STL-IA-PT` |
| Distribuição Python | `hermes-lint` |
| Pacote Python | `hermes_lint` |
| CLI | `hermes` |
| Regras | `HERMES-PT-*` |

A identidade existente `ste-lint`/`ste_lint`/`ste` é histórica e só será
migrada de forma atômica em PT3, com testes de caracterização e compatibilidade
explicitamente decidida.

## Matriz de licenças

| Material | Licença | Regra de inclusão |
|---|---|---|
| código e testes de software | Apache-2.0 | contribuição sob a licença do repositório |
| especificação e guias linguísticos autorais | CC BY 4.0 | autoria/proveniência declarada |
| exemplos sintéticos do projeto | CC BY 4.0 | sem conteúdo confidencial ou derivação protegida |
| rótulos e adjudicações autorais | CC BY 4.0 | texto-fonte redistribuível ou somente referência/hash |
| corpus criado integralmente pelo projeto | CC BY 4.0 | consentimento e revisão de privacidade |
| corpus, léxicos e modelos externos | licença de origem | compatibilidade e redistribuição verificadas por recurso |
| respostas brutas de modelos | não públicas por padrão | termos, privacidade e necessidade avaliados antes de publicar |

Apache-2.0 inclui permissões de reprodução, modificação e distribuição e uma
licença de patentes sujeita às condições do texto oficial.[1] CC BY 4.0 permite
compartilhar e adaptar com atribuição, link para a licença e indicação de
mudanças.[2]

## Regras operacionais

1. Cada diretório de conteúdo terá `LICENSE`, cabeçalho SPDX ou manifesto
   inequívoco antes da primeira release.
2. Fonte externa registra URL, titular quando conhecido, licença, snapshot,
   hash, transformações e direito de redistribuição.
3. A licença do rótulo não relicencia o texto rotulado.
4. Texto não redistribuível pode participar apenas de avaliação privada, com
   artefatos públicos limitados a métricas e hashes permitidos.
5. Saída de LLM não limpa copyright, confidencialidade nem incompatibilidade de
   licença da entrada.
6. `NOTICE` lista atribuições exigidas pelas dependências e corpora efetivamente
   distribuídos, não ferramentas usadas apenas como referência.
7. Dúvida de licença bloqueia merge e release até decisão documentada.

Isto é política arquitetural de risco, não aconselhamento jurídico.

## Sources

[1] https://www.apache.org/licenses/LICENSE-2.0 — Apache License 2.0
[2] https://creativecommons.org/licenses/by/4.0 — Creative Commons Attribution 4.0
