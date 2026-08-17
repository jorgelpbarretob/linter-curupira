# Acceptance tests case-008

```bash
curupira lint ARTIFACT --enable-rule CURUPIRA-PT-PONT-001 --format json
test $? -eq 0
```
