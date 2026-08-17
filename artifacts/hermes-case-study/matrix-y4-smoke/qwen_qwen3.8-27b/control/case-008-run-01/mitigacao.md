# Mitigação — fila jobs-hot / worker-b

## Sintoma
- Fila `jobs-hot` cresce desde 21h.
- Worker `worker-b` preso em batch antigo.
- Latência subiu e health flipou.
- Tentativa de drain não esvaziou a fila.

## Mitigação imediata
- Executar restart da unit `worker-b.service`.
- Ação conhecida: funcionou ontem em caso parecido.

## Verificação
- Checar `/health` após o restart.
- Acompanhar o tamanho da fila `jobs-hot` por 10 min.

## Escalonamento
- Abrir SEV2 se a fila continuar subindo após 10 min.
- Incluir print do painel no SEV2.
- Não reiniciar o broker sem autorização.
