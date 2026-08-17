# Mitigacao worker-queue

## Erro observado

Em 2026-08-16T10:01:02Z o log registra WARN: worker-queue timeout on job batch-77.

Em 2026-08-16T10:01:10Z o log registra ERROR: worker-queue stalled.

O supervisor reiniciou a unit worker-queue.service.

O log nao indica causa raiz alem do stall e do timeout.

## Acao de mitigacao

Reinicie a unit worker-queue.service, como o supervisor fez no log.

## Verificacao pos-mitigacao

Confirme o INFO do log: worker-queue healthy after restart (2026-08-16T10:01:40Z).

Se o stall repetir em 15 min, abra incidente SEV3 com o trecho do log.
