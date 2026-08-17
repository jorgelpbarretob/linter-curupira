Sintoma:
- fila jobs-hot cresceu depois das 21h
- worker-b preso em batch antigo
- latência subiu e health flipou

Mitigação imediata:
- restart unit worker-b.service

Verificação:
- após restart: checar /health e tamanho da fila

Escalonamento:
- se fila não normalizar em 10 min: abrir SEV2 com print do painel
- não reiniciar o broker sem autorização