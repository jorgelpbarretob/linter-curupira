# Mitigação — fila jobs-hot / worker-b

## Sintoma
- Fila `jobs-hot` cresce após 21h
- `worker-b` parece preso em batch antigo
- Latência alta e health instável
- Drain não esvaziou a fila

## Mitigação imediata
- Restart da unit `worker-b.service` (já resolveu caso parecido)
- Não reiniciar o broker sem autorização
- Se não normalizar em 10 min: abrir SEV2

## Verificação
- Checar `/health`
- Conferir tamanho da fila `jobs-hot`

## Escalonamento
- Se a fila continuar subindo: abrir SEV2 com print do painel
