# Acceptance tests case-014

```bash
curupira lint ARTIFACT --enable-rule CURUPIRA-PT-PONT-001 --format json
test $? -eq 0
grep -ciE 'o mesmo|deste' ARTIFACT   # esperado: 0
```
