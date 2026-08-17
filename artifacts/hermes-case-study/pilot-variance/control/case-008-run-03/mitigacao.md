# Mitigação SEV2: worker-b e fila jobs-hot

Fonte: notas de turno de 16/08, após 21h.

## Sintoma
- Fila jobs-hot voltou a crescer após 21h.
- Worker-b parece preso em batch antigo, segundo o turno. Causa raiz não confirmada.
- Latência subiu e o health flipou.
- Drain executado, mas a fila não esvaziou.

## Mitigação imediata
- Executar restart da unit `worker-b.service`. O mesmo procedimento resolveu caso semelhante ontem.
- Não reiniciar o broker sem autorização.

## Verificação
- Consultar `/health` após o restart.
- Medir o tamanho da fila jobs-hot.

## Escalonamento
- Se não normalizar em 10 min, abrir SEV2 com print do painel, conforme diretriz do supervisor.
- Se a fila continuar subindo após o restart, abrir SEV2 com o mesmo print.
