# CI docs
no pipeline rode hermes-lint $(git diff --name-only origin/main...HEAD | grep -E '\.md$') --enable-rule HERMES-PT-PONT-001; se exit!=0 falhe o job; publique o JSON como artifact; bloqueie merge até limpar; não rode semantic-review no CI; mantenha cache da toolchain entre jobs se possível.
