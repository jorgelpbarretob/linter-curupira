# Mitigação — jobs-hot / worker-b (SEV2)

## Sintoma
- Fila jobs-hot voltou a crescer depois das 21h.
- worker-b parece preso em batch antigo.
- Latência subiu e o health flipou.
- Drain tentado, mas a fila não esvaziou.

## Mitigação imediata
1. Reiniciar a unit `worker-b.service`.
2. Motivo: o restart já resolveu caso parecido ontem.
3. Não reiniciar o broker sem autorização.

## Verificação (pós-restart)
- Checar `/health` do worker-b.
- Checar o tamanho da fila jobs-hot.

## Escalonamento
- Prazo: normalizar em 10 min.
- Se a fila continuar subindo: abrir SEV2 com print do painel.
