# Procedimento de migracao do banco

Host: db-synth-01.

1. Faca backup do banco no host db-synth-01.
2. Registre o count da tabela jobs.
3. Rode migrate no host db-synth-01.
4. Verifique o count com select count na tabela jobs.
5. Se o count for menor que o valor anterior, pare e chame o DBA.
