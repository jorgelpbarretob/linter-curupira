# Acceptance tests case-006

```bash
curupira lint ARTIFACT --enable-rule CURUPIRA-PT-PONT-001 --format json
test $? -eq 0
rg -n "worker-queue|SEV3|15" ARTIFACT
```
