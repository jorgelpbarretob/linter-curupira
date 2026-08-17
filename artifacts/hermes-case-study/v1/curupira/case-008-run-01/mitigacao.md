# Mitigação — fila jobs-hot / worker-b

## Sintoma
- Fila `jobs-hot` cresce após 21h.
- `worker-b` parece preso em batch antigo.
- Latência subiu e o health flipou.
- Drain não esvaziou a fila.

## Mitigação imediata
1. Reiniciar a unit `worker-b.service` (já restabeleceu em caso parecido).
2. Não reiniciar o broker sem autorização.
3. Se não normalizar em 10 min, tratar como SEV2.

## Verificação
- Conferir `/health`.
- Conferir tamanho da fila `jobs-hot`.

## Escalonamento
- Se a fila continuar subindo: abrir SEV2 com print do painel.
