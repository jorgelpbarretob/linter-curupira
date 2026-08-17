Sintoma: worker-b preso em batch antigo
fila jobs-hot cresceu após 21h
latência subiu e health check flipou

Mitigação imediata: restart unit worker-b.service

Verificação: checar /health e tamanho da fila após restart

Escalonamento: se fila não normalizar em 10 min, abrir SEV2 com print do painel
não reiniciar broker sem autorização