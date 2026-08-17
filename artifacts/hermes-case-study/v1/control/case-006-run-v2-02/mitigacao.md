# Mitigação — worker-queue (batch-77)

## Erro observado

Em 2026-08-16T10:01:02Z o worker-queue registrou timeout no job batch-77.
Em 2026-08-16T10:01:10Z o worker-queue ficou stalled.

O log não informa causa raiz.

## Mitigação

O supervisor reiniciou a unit `worker-queue.service`.

## Verificação

Após o restart, o log em 2026-08-16T10:01:40Z indica worker-queue healthy.

Confirme o estado da unit e a ausência de novo timeout ou stall.

## Se repetir

Se o stall repetir em 15 min, abra incidente SEV3 com o trecho do log.
