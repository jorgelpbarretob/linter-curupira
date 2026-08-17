# Mitigação — incidente fila jobs-hot e worker-b

## Sintoma
- Fila jobs-hot voltou a crescer após as 21h.
- Worker-b aparentemente preso em batch antigo.
- Latência subiu e o health flipou.
- Drain tentado, mas a fila não esvaziou.

## Mitigação imediata
1. Reiniciar a unit `worker-b.service`.
2. Base: este restart funcionou ontem em caso parecido.
3. Não reiniciar o broker sem autorização.

## Verificação
1. Verificar `/health` após o restart.
2. Verificar o tamanho da fila jobs-hot.

## Escalonamento
- Janela: normalizar em 10 min.
- Se não normalizar: abrir SEV2.
- Se a fila continuar a crescer: abrir SEV2 com print do painel.

## Pendência
- Causa raiz não confirmada. Tratar após estabilizar.
