# CI docs

1. Liste os Markdown alterados com `git diff --name-only origin/main...HEAD` e filtre `\.md$`.
2. Rode `curupira lint` nesses arquivos com `--enable-rule CURUPIRA-PT-PONT-001` e `--format json`.
3. Se o exit code for diferente de zero falhe o job.
4. Publique o JSON como artifact do pipeline.
5. Bloqueie o merge até limpar os achados.
6. Não rode semantic-review no CI.
7. Mantenha cache da toolchain entre jobs se possível.
