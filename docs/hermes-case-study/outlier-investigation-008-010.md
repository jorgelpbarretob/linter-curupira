# Investigação outliers case-008/009/010

Battery: `run-cli-default` (control × CLI-min).
Outliers permanecem no agregado.

JSON completo: `artifacts/hermes-case-study/v1/outlier-investigation-008-010.json`

## case-008

- Δ tokens total: **6233**
- Δ input: **6184** · Δ output: **49**
- tokens control/cli: 23624 / 29857

### Braço control
- session `20260816_232907_4d8d77`
- model grok-4.5 · msgs 10 · tools 5 · api 4
- tokens in/out 23049/575
- system_prompt_len 36420
- msg content bytes 3845 · tool bytes 2186
- errorish/retryish 2/0
- artifact chars 513
- tools: read_file x3 (1731 B), terminal x1 (167 B), write_file x1 (288 B)
- maiores mensagens:
  - user/- len=1285: Você é o braço CONTROLE do estudo case-008 (sem Curupira).  Leia a tarefa completa abaixo e o arquivo de traba
  - tool/read_file len=834: {"content": "1|# Tarefa case-008 — incidente denso → mitigação legível\n2|\n3|## Objetivo de produto\n4|Menos 
  - tool/read_file len=574: {"content": "1|# Notas de turno — 16/08\n2|\n3|fila jobs-hot voltou a crescer depois das 21h, worker-b parece 
  - tool/read_file len=323: {"content": "", "total_lines": 0, "file_size": 0, "truncated": false, "is_binary": false, "is_image": false, "
  - tool/write_file len=288: {"bytes_written": 530, "dirs_created": true, "verified": true, "lint": {"status": "skipped", "message": "No li
  - assistant/- len=226: path: /tmp/cs-ab/case-008-run-cli-default-control/mitigacao.md chars: 513 (530 bytes) resumo: Mitigação SEV2 e

### Braço cli
- session `20260816_232928_b2314e`
- model grok-4.5 · msgs 10 · tools 5 · api 4
- tokens in/out 29233/624
- system_prompt_len 36420
- msg content bytes 4260 · tool bytes 2349
- errorish/retryish 0/0
- artifact chars 551
- tools: read_file x2 (1408 B), terminal x2 (661 B), write_file x1 (280 B)
- maiores mensagens:
  - user/- len=1579: Você é o braço CLI do estudo case-008. NÃO carregue skill. Use só o binário local curupira.  Arquivos: - taref
  - tool/read_file len=834: {"content": "1|# Tarefa case-008 — incidente denso → mitigação legível\n2|\n3|## Objetivo de produto\n4|Menos 
  - tool/read_file len=574: {"content": "1|# Notas de turno — 16/08\n2|\n3|fila jobs-hot voltou a crescer depois das 21h, worker-b parece 
  - tool/terminal len=491: {"output": "total 16\ndrwx------  2 jorge jorge 120 ago 16 23:29 .\ndrwx------ 40 jorge jorge 800 ago 16 23:29
  - tool/write_file len=280: {"bytes_written": 568, "dirs_created": true, "verified": true, "lint": {"status": "skipped", "message": "No li
  - assistant/- len=195: path: /tmp/cs-ab/case-008-run-cli-default-cli/mitigacao.md lint exit: 0 chars: 568 resumo: Mitigação SEV2 em 4

### Diff artefato: 26 linhas unificadas

### Drivers
- inspect_timeline_for_extra_reads_or_search
- razão input cli/control: 1.268

## case-009

- Δ tokens total: **-15424**
- Δ input: **-15566** · Δ output: **142**
- tokens control/cli: 29457 / 14033

### Braço control
- session `20260816_232951_87aa78`
- model grok-4.5 · msgs 10 · tools 5 · api 4
- tokens in/out 28853/604
- system_prompt_len 36420
- msg content bytes 2944 · tool bytes 1554
- errorish/retryish 1/0
- artifact chars 512
- tools: read_file x2 (1105 B), search_files x1 (18 B), terminal x1 (155 B), write_file x1 (276 B)
- maiores mensagens:
  - user/- len=1079: Você é o braço CONTROLE do estudo case-009 (sem Curupira).  Leia a tarefa completa abaixo e o arquivo de traba
  - tool/read_file len=620: {"content": "1|# Tarefa case-009 — lab notes → POP legível\n2|\n3|## Objetivo de produto\n4|Reduzir ruído text
  - tool/read_file len=485: {"content": "1|# Notas — amostragem mosto\n2|\n3|pegar amostra no ponto A-14 com frasco F90 limpo, descartar p
  - tool/write_file len=276: {"bytes_written": 533, "dirs_created": true, "verified": true, "lint": {"status": "skipped", "message": "No li
  - assistant/- len=161: path: /tmp/cs-ab/case-009-run-cli-default-control/pop.md chars: 512 (bytes: 533) resumo: POP numerado com A-14
  - tool/terminal len=155: {"output": "533 /tmp/cs-ab/case-009-run-cli-default-control/pop.md\n512 /tmp/cs-ab/case-009-run-cli-default-co

### Braço cli
- session `20260816_233014_12c478`
- model grok-4.5 · msgs 10 · tools 5 · api 4
- tokens in/out 13287/746
- system_prompt_len 36420
- msg content bytes 3673 · tool bytes 2016
- errorish/retryish 1/0
- artifact chars 749
- tools: read_file x2 (1105 B), terminal x2 (643 B), write_file x1 (268 B)
- maiores mensagens:
  - user/- len=1361: Você é o braço CLI do estudo case-009. NÃO carregue skill. Use só o binário local curupira.  Arquivos: - taref
  - tool/read_file len=620: {"content": "1|# Tarefa case-009 — lab notes → POP legível\n2|\n3|## Objetivo de produto\n4|Reduzir ruído text
  - tool/read_file len=485: {"content": "1|# Notas — amostragem mosto\n2|\n3|pegar amostra no ponto A-14 com frasco F90 limpo, descartar p
  - tool/terminal len=479: {"output": "total 16\ndrwx------  2 jorge jorge 120 ago 16 23:30 .\ndrwx------ 42 jorge jorge 840 ago 16 23:30
  - tool/write_file len=268: {"bytes_written": 778, "dirs_created": true, "verified": true, "lint": {"status": "skipped", "message": "No li
  - assistant/- len=168: path: /tmp/cs-ab/case-009-run-cli-default-cli/pop.md lint exit: 0 chars: 778 resumo: POP em passos numerados c

### Diff artefato: 46 linhas unificadas

### Drivers
- artifact_size_diff_material
- razão input cli/control: 0.461

## case-010

- Δ tokens total: **22445**
- Δ input: **22405** · Δ output: **40**
- tokens control/cli: 29789 / 52234

### Braço control
- session `20260816_233037_4d9878`
- model grok-4.5 · msgs 9 · tools 4 · api 4
- tokens in/out 29103/686
- system_prompt_len 36420
- msg content bytes 3574 · tool bytes 1940
- errorish/retryish 1/0
- artifact chars 812
- tools: read_file x2 (1536 B), terminal x1 (120 B), write_file x1 (284 B)
- maiores mensagens:
  - user/- len=1282: Você é o braço CONTROLE do estudo case-010 (sem Curupira).  Leia a tarefa completa abaixo e o arquivo de traba
  - tool/read_file len=823: {"content": "1|# Tarefa case-010 — modernizar runbook denso\n2|\n3|## Objetivo de produto\n4|Legibilidade para
  - tool/read_file len=713: {"content": "1|# Runbook legado — preflight docs\n2|\n3|O revisor deve garantir o ambiente com a toolchain do 
  - tool/write_file len=284: {"bytes_written": 830, "dirs_created": true, "verified": true, "lint": {"status": "skipped", "message": "No li
  - assistant/- len=202: path: /tmp/cs-ab/case-010-run-cli-default-control/runbook.md chars: 830 resumo: Runbook em 5 passos (instalar→
  - tool/terminal len=120: {"output": "830 /tmp/cs-ab/case-010-run-cli-default-control/runbook.md\nOK: zero legado", "exit_code": 0, "err

### Braço cli
- session `20260816_233059_de7bcd`
- model grok-4.5 · msgs 9 · tools 4 · api 4
- tokens in/out 51508/726
- system_prompt_len 36420
- msg content bytes 3911 · tool bytes 1993
- errorish/retryish 0/0
- artifact chars 765
- tools: read_file x2 (1536 B), terminal x1 (181 B), write_file x1 (276 B)
- maiores mensagens:
  - user/- len=1572: Você é o braço CLI do estudo case-010. NÃO carregue skill. Use só o binário local curupira.  Arquivos: - taref
  - tool/read_file len=823: {"content": "1|# Tarefa case-010 — modernizar runbook denso\n2|\n3|## Objetivo de produto\n4|Legibilidade para
  - tool/read_file len=713: {"content": "1|# Runbook legado — preflight docs\n2|\n3|O revisor deve garantir o ambiente com a toolchain do 
  - tool/write_file len=276: {"bytes_written": 784, "dirs_created": true, "verified": true, "lint": {"status": "skipped", "message": "No li
  - assistant/- len=214: Pronto.  path: /tmp/cs-ab/case-010-run-cli-default-cli/runbook.md lint exit: 0 chars: 784 resumo: Runbook em p
  - tool/terminal len=181: {"output": "{\n  \"schema_version\": \"1.0\",\n  \"diagnostics\": []\n}\nEXIT:0\n784 /tmp/cs-ab/case-010-run-c

### Diff artefato: 57 linhas unificadas

### Drivers
- input_tokens_cli_much_higher
- razão input cli/control: 1.77

## Conclusões pontuais

### case-008 (CLI +6233 tok)
- Mesma ordem de magnitude de tools (5) e tool bytes parecidos.
- Input tokens CLI bem maior (29233 vs 23049) com system_prompt_len a checar no JSON.
- CLI fez 2 terminais (inclui lint). Control 1 terminal.
- Não há cascata de erro. Custo parece vir de **contexto/prompt de sessão**, não de tool dump enorme.

### case-009 (CLI -15424 tok) — outlier barato
- Control fez `search_files` extra. CLI não.
- Input CLI 13287 vs control 28853. Ferramentas semelhantes no restante.
- Artefato CLI maior em chars (749 vs 512), então o ganho não é “texto final menor”.
- Hipótese: control pagou exploração/busca desnecessária. CLI foi mais direto.

### case-010 (CLI +22445 tok)
- Tools 4=4 e tool bytes quase iguais.
- Input CLI 51508 vs control 29103 (~1.77x) com pouca diferença de tool output.
- Hipótese principal: **inchaco de contexto de input do modelo** (prompt/system/history accounting), não retries de lint.
- Artefato até um pouco menor no CLI (765 vs 812).

### Implicação
- Outliers de tokens nesta bateria **não se explicam só por residual ou por bytes de tool**.
- Manter no agregado. Na v2, logar `system_prompt_len`, tamanho do user prompt e tokens por API call quando disponível.

