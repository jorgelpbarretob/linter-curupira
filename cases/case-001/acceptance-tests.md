# Acceptance tests case-001

```bash
curupira lint ARTIFACT --enable-rule CURUPIRA-PT-PONT-001 --format json
test $? -eq 0
rg -n "V-12|P-01|PI-01" ARTIFACT
```
