# Acceptance tests case-015

```bash
curupira lint ARTIFACT --enable-rule CURUPIRA-PT-PONT-001 --format json
test $? -eq 0
grep -c 'XV-201' ARTIFACT   # esperado: 0
grep -c 'XV-205' ARTIFACT   # esperado: >= 1
```
