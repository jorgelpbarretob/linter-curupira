# Mitigação — fila jobs-hot / worker-b

## Sintoma
- Fila `jobs-hot` cresce após 21h
- `worker-b` parece preso em batch antigo
- Latência alta e health instável
- Drain não esvaziou a fila

## Mitigação imediata
1. Restart da unit `worker-b.service` (já ajudou em caso parecido)
2. Não reiniciar o broker sem autorização
3. Se não normalizar em 10 min, tratar como SEV2

## Verificação
- Checar `/health`
- Conferir tamanho da fila `jobs-hot`
- Confirmar se `worker-b` processa de novo

## Escalonamento
- Se a fila continuar subindo: abrir SEV2 com print do painel
- Manter broker intacto até autorização explícita
