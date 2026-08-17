# Acceptance tests case-004

```bash
curupira lint ARTIFACT --enable-rule CURUPIRA-PT-PONT-001 --format json
test $? -eq 0
! rg -n "hermes-lint|HERMES-PT-PONT-001" ARTIFACT
rg -n "curupira|CURUPIRA-PT-PONT-001" ARTIFACT
```
