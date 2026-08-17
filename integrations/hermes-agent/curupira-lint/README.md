# Plugin Curupira para Hermes Agent

Este plugin opt-in registra a tool local `curupira_lint` e um gate de saída
`pre_verify`. A tool recebe uma lista de caminhos, classifica `.md`,
`.markdown` e `.txt`, executa somente
`curupira lint --format json` e retorna um evento estruturado
`preflight_completed`.

O wrapper não chama `analyze`, `semantic-review`, rede ou modelo remoto. O
conteúdo dos documentos não entra no evento. Ficam registrados caminho,
SHA-256, tamanho, diagnósticos, regra, versão, duração e falhas operacionais.

## Instalação local

Com o repositório já clonado:

```bash
mkdir -p ~/.hermes/plugins
ln -s "$PWD/integrations/hermes-agent/curupira-lint" \
  ~/.hermes/plugins/curupira-preflight
hermes plugins enable curupira-preflight --no-allow-tool-override
hermes plugins doctor ~/.hermes/plugins/curupira-preflight --ci
```

Reinicie processos Hermes que já estavam em execução. O binário `curupira`
precisa estar no `PATH` do processo do agente.

O gate executa a tool automaticamente sobre os arquivos alterados quando o
Hermes tenta concluir a tarefa. `passed` e `not_applicable` liberam a conclusão.
`needs_review` concede uma rodada para corrigir os diagnósticos e executa o
preflight novamente. Diagnóstico residual, falha operacional ou evento inválido
retorna `block_completion`, portanto o resultado do turno não recebe
`completed=true`.

No prompt-base, use somente esta frase e não faça preload da skill:

> Antes de concluir alterações em documentação, execute o preflight Curupira.

## Interface

Entrada:

```json
{
  "paths": ["docs/procedimento.md", "notas.txt"],
  "config_path": "curupira.toml"
}
```

`config_path` é opcional. O wrapper não aceita argumentos livres de CLI.

Estados de saída:

| status | exit_code | significado |
|---|---:|---|
| `passed` | 0 | todos os documentos suportados passaram |
| `needs_review` | 1 | há diagnósticos para corrigir |
| `blocked` | 2 | houve falha operacional ou evidência inválida |
| `not_applicable` | 0 | nenhum caminho tem extensão suportada |

O schema inicial é `curupira-hermes-preflight/v1`. A tool limita cada execução
do Curupira a 30 segundos e falha fechada se não puder confirmar a versão ou
interpretar o JSON retornado.
