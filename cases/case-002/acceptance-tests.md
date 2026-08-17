# Acceptance tests case-002

```bash
curupira lint ARTIFACT --enable-rule CURUPIRA-PT-PONT-001 --format json
test $? -eq 0
rg -n "curupira-api.service|8080/health|restart" ARTIFACT
```
