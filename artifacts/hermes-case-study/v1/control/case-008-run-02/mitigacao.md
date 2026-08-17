# Mitigação — fila jobs-hot / worker-b

## Sintoma
- Fila `jobs-hot` cresce após 21h
- `worker-b` parece preso em batch antigo
- Latência alta e health instável
- Drain não esvaziou a fila

## Mitigação imediata
- Reiniciar unit `worker-b.service`
- Não reiniciar o broker sem autorização
- Se não normalizar em 10 min: tratar como SEV2

## Verificação
- Checar `/health`
- Conferir tamanho da fila `jobs-hot`

## Escalonamento
- Se a fila continuar subindo: abrir SEV2 com print do painel
