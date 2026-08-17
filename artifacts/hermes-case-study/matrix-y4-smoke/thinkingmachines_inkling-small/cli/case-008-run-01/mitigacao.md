Sintoma: worker-b preso. Fila jobs-hot cresce. Latência alta. Health flipou.
Mitigação imediata: restart unit worker-b.service. Prazo 10 min. SEV2.
Verificação: /health. Tamanho fila jobs-hot.
Escalonamento: se fila subir abrir SEV2 com painel. Não reiniciar broker sem autorização.
