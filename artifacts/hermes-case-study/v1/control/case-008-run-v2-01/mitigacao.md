# Mitigação — fila jobs-hot / worker-b

## Sintoma
- Fila `jobs-hot` cresce (após 21h)
- `worker-b` parece preso em batch antigo
- Latência alta e health instável
- Drain não esvaziou a fila

## Mitigação imediata
- Reiniciar a unit `worker-b.service` (restart já ajudou em caso parecido)
- Não reiniciar o broker sem autorização

## Verificação
- Checar `/health`
- Conferir tamanho da fila `jobs-hot`

## Escalonamento
- Se não normalizar em 10 min: abrir SEV2 com print do painel
- Se a fila continuar subindo após o restart: SEV2 com evidência do painel
