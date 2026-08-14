# Rodada 2 — validação do inventário `pending-review`

Data: 2026-08-13

Status: duas cópias geradas e verificadas em `/tmp`; revisão Cursor pré-label
pendente

## Escopo

O sexto gate Cursor autorizou somente implementar `--emit-inventory` e gerar
duas cópias de metadados com `truth=review_status=pending-review`. Nenhum label,
rationale, texto-fonte ou resultado do linter foi produzido. Os JSONL não estão
no repositório.

## TDD e implementação

O incremento começou com quatro regressões vermelhas para:

- spans brutos e hashes preservados após projeção de markup;
- classificação exaustiva de `;` visível e mascarado;
- sentinels LIST sem lead-in;
- coordenada EOF e serialização JSONL canônica.

Depois da implementação, 11 testes específicos passaram. O scanner continua
fora de `src/ste_lint`, e o teste AST proíbe imports do produto.

## Geração autorizada

Comando:

```text
.venv/bin/python tools/product_evidence/round2_scanner.py \
  --emit-inventory \
  --dapr-root /tmp/ste-round2-dapr-docs \
  --otel-root /tmp/ste-round2-opentelemetry-docs
```

O scanner auditou os 16 arquivos, construiu e validou o inventário duas vezes em
memória e só então escreveu:

- `/tmp/ste-lint-product-evidence-round2-inventory-a.jsonl`;
- `/tmp/ste-lint-product-evidence-round2-inventory-b.jsonl`.

## Resultado congelado

| Tranche | Registros |
|---|---:|
| `STE-I9-SENT-001` | 558 |
| `STE-I9-SENT-002` | 329 |
| `STE-I9-PARA-001` | 144 |
| `STE-I9-PUNCT-001` | 69 |
| `STE-I9-LIST-001` | 73 |
| **Total** | **1.173** |

Cada cópia tem 1.173 linhas e 1.043.742 bytes. `cmp` confirmou bytes idênticos.
SHA-256 de ambas:

```text
bebbabe41b28f59e87250e188fe946b237152f9293c8765a06d1322cb3d94c38
```

Uma terceira reprodução lógica, usando o hash acima como
`--expected-output-sha256`, passou sem divergência.

## Invariantes verificadas

- auditoria O2 completa antes da extração;
- round-trip e SHA-256 de cada recorte e lead-in presente;
- offsets, coordenadas, enums, schema e sentinels válidos;
- chaves e `case_id` globalmente únicos;
- ordenação e serialização canônicas;
- totais exatos `558/329/144/69/73`;
- exclusão de `secrets-quickstart.md` somente em `STE-I9-SENT-001`;
- todos os 1.173 registros com `truth` e `review_status` iguais a
  `pending-review`;
- ausência dos campos `text`, `context`, `excerpt`, `preview`, `rationale`,
  `reviewer` e `reviewed_at`;
- nenhuma cópia JSONL adicionada ao Git.

O próximo gate é revisão estrutural/hash-only do Cursor. Labeling e execução do
linter permanecem bloqueados.
