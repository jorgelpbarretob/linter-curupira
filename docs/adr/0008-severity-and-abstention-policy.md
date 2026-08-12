# ADR-008: política de severidade e abstenção

Status: Accepted
Data: 2026-08-12

## Contexto

Severidade comunica certeza operacional. Uma regra incerta não pode parecer
equivalente a uma detecção estável, e ausência de achado não significa
conformidade completa.

## Decisão proposta

- `stable` pode emitir a severidade registrada no catálogo;
- `preview` emite no máximo `info`;
- `semantic` emite no máximo `info`, mesmo quando estável;
- `human-review` não executa e não emite `Diagnostic`;
- baixa confiança ou pré-condição ausente produz abstenção, representada por
  zero diagnósticos, sem mensagem sintética de sucesso;
- uma regra não pode elevar sua severidade acima do permitido pelo catálogo.

O engine valida cada diagnóstico contra documento, registry e metadados. Span
inválido, fonte divergente, severidade proibida ou exceção de regra é falha
operacional identificável; não é convertido em silêncio nem em diagnóstico de
compliance.

## Alternativas rejeitadas

- emitir `warning` com baixa confiança, porque transfere incerteza para o autor;
- capturar exceções e continuar silenciosamente, porque oculta cobertura perdida;
- introduzir `confidence` agora, porque ainda não existe consumidor ou modelo
  calibrado que sustente o campo.

## Consequências

- formatadores recebem somente diagnósticos já validados;
- erros do engine seguem caminho e código de saída distintos dos achados;
- promover `preview` para `stable` continua condicionado ao quality gate.

## Aprovação necessária

Aceito explicitamente pelo mantenedor em 2026-08-12, antes de implementar
validação de severidade e tratamento público de falhas.
