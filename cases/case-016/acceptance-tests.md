# Acceptance tests case-016

```bash
curupira lint ARTIFACT --enable-rule CURUPIRA-PT-PONT-001 --format json
test $? -eq 0
```
