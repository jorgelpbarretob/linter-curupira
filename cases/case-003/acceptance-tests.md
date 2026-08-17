# Acceptance tests case-003

```bash
curupira lint ARTIFACT --enable-rule CURUPIRA-PT-PONT-001 --format json
test $? -eq 0
rg -n "V-90|R-02|S-11" ARTIFACT
```
