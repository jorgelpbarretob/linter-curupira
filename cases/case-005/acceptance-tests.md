# Acceptance tests case-005

```bash
curupira lint ARTIFACT --enable-rule CURUPIRA-PT-PONT-001 --format json
test $? -eq 0
rg -ni "backup|migrate|jobs|db-synth-01" ARTIFACT
```
