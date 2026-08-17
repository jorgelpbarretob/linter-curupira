# Mitigação — fila jobs-hot (worker-b)

## Sintoma
- Fila jobs-hot cresce desde as 21h.
- Worker-b preso em batch antigo.
- Latência subiu e o health flipou.
- Drain tentado. A fila não esvaziou.

## Mitigação imediata
1. Reinicie a unit `worker-b.service`.
2. O restart já resolveu caso parecido ontem.
3. Não reinicie o broker sem autorização.

## Verificação
1. Cheque `/health` após o restart.
2. Meça o tamanho da fila jobs-hot.

## Escalonamento
- Janela: 10 min para normalizar.
- Sem normalizar: abra SEV2 com print do painel.
- Se a fila seguir subindo após o restart: abra SEV2.
- Causa raiz: não diagnosticada até o momento.
