# Mitigação — fila jobs-hot / worker-b

## Sintoma
- Fila `jobs-hot` crescendo após 21h
- `worker-b` aparenta preso em batch antigo
- Latência alta e health instável
- Drain não esvaziou a fila

## Mitigação imediata
1. Restart da unit `worker-b.service` (já estabilizou caso parecido)
2. Não reiniciar o broker sem autorização

## Verificação
- Checar `/health`
- Conferir tamanho da fila `jobs-hot`
- Observar se a fila para de subir

## Escalonamento
- Se não normalizar em **10 min**: abrir **SEV2** com print do painel
- Manter broker intacto até autorização explícita
