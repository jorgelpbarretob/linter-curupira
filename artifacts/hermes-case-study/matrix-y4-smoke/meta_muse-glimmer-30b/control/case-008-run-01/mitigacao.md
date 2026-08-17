# Mitigação — worker-b / jobs-hot

Sintoma
- fila jobs-hot cresce desde 21h
- latência alta
- health flipou
- drain não esvazia
- worker-b parece preso em batch antigo

Mitigação imediata
- aguardar até 10 min
- restart unit `worker-b.service`

Verificação
- checar /health
- medir tamanho da fila jobs-hot

Escalonamento
- se fila continuar subindo abrir SEV2
- anexar print do painel
- não reiniciar broker sem autorização
