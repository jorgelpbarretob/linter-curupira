# Mitigação — worker-b / jobs-hot (16/08)

## Sintoma
- fila jobs-hot voltou a crescer após 21h.
- worker-b preso em batch antigo.
- Latência subiu e o health flipou.
- Drain tentado e não esvaziou.

## Mitigação imediata
1. Restart unit `worker-b.service` (funcionou ontem em caso parecido).
2. Não reiniciar o broker sem autorização.

## Verificação
- Checar /health.
- Checar tamanho da fila.

## Escalonamento
- Sem normalizar em 10 min: mitigação SEV2 (pedido do supervisor).
- Fila continuar subindo após o restart: abrir SEV2 com print do painel.
