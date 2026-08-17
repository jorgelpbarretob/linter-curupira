# Migração de banco — db-synth-01

1. Faça backup do banco no host `db-synth-01` antes de qualquer alteração.
2. Execute `migrate` no host `db-synth-01`.
3. Verifique com `SELECT COUNT(*)` na tabela `jobs`.
4. Se o count for menor que o valor anterior, pare e chame o DBA.
