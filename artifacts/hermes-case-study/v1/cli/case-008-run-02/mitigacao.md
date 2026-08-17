# Mitigação — fila jobs-hot / worker-b

## Sintoma
- Fila jobs-hot cresce após 21h
- worker-b parece preso em batch antigo
- Latência subiu e health flipou
- Drain não esvaziou a fila

## Mitigação imediata
- Restart da unit `worker-b.service`
- Não reiniciar o broker sem autorização

## Verificação
- Checar `/health`
- Checar tamanho da fila jobs-hot
- Janela de normalização: 10 min

## Escalonamento
- Se a fila continuar subindo após 10 min: abrir SEV2
- Anexar print do painel
