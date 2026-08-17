# Mitigação — worker-b / fila jobs-hot

## Sintoma
- Fila `jobs-hot` voltou a crescer depois das 21h.
- Latência subiu e o health flipou.
- `worker-b` parece preso em um batch antigo.
- Tentativa de drain não esvaziou a fila.

## Mitigação imediata
- Fazer o restart da unit `worker-b.service`.
- Esse restart já funcionou ontem em um caso parecido.

## Verificação
- Checar `/health`.
- Checar o tamanho da fila `jobs-hot`.

## Escalonamento
- Se não normalizar em 10 min, abrir SEV2 com print do painel.
- Se a fila continuar subindo após o restart, abrir SEV2.
- Não reiniciar o broker sem autorização.
