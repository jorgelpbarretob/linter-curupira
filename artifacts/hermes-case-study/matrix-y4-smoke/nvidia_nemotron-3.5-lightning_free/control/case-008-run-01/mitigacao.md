Sintoma: fila jobs-hot cresceu depois das 21h. Worker-b preso em batch antigo. Latencia subiu. Health flipou. Drain nao esvaziou.

Mitigacao imediata: restart unit worker-b.service (ja funcionou ontem em caso parecido).

Verificacao: apos restart, checar /health e tamanho da fila. Se fila continuar subindo abrir SEV2 com print do painel.

Escalonamento: supervisor solicitou mitigacao SEV2 se nao normalizar em 10 min. Nao reiniciar broker sem autorizacao.