# Mitigação — fila jobs-hot / worker-b

## Sintoma
- Fila `jobs-hot` voltou a crescer após 21h
- `worker-b` parece preso em batch antigo
- Latência subiu e health flipou
- Drain não esvaziou a fila

## Mitigação imediata
- Restart da unit `worker-b.service` (já funcionou ontem em caso parecido)
- Não reiniciar o broker sem autorização
- Se não normalizar em 10 min tratar como SEV2

## Verificação
- Checar `/health` após o restart
- Conferir tamanho da fila `jobs-hot`

## Escalonamento
- Se a fila continuar subindo abrir SEV2 com print do painel
