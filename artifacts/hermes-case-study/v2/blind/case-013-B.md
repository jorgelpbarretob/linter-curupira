# CI docs

1. No pipeline liste os `.md` do diff contra `origin/main`.
2. Rode `curupira lint` nesses arquivos com a regra `CURUPIRA-PT-PONT-001`.
3. Se o exit code for diferente de 0 falhe o job.
4. Publique o JSON como artifact.
5. Bloqueie o merge até limpar as falhas.
6. Não rode semantic-review no CI.
7. Mantenha cache da toolchain entre jobs se possível.
