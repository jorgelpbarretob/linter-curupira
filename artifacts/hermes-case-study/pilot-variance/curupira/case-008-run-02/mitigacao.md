# Mitigação — worker-b e fila jobs-hot

## Sintoma
- Fila jobs-hot voltou a crescer depois das 21h.
- Worker-b parece preso em batch antigo.
- Latência subiu e o health flipou.
- Drain tentado. A fila não esvaziou.

## Mitigação imediata
1. Reinicie a unit `worker-b.service`.
2. O mesmo restart resolveu caso parecido ontem.
3. Não reinicie o broker sem autorização.

## Verificação
1. Verifique `/health` do worker-b.
2. Meça o tamanho da fila jobs-hot.

## Escalonamento
- Janela: 10 min para normalizar.
- Se a fila continuar subindo, abra SEV2 com print do painel.
- Supervisor pediu mitigação SEV2 nesse cenário.
