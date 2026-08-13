# ADR-015: contrato do fixer seguro

Status: Accepted
Data: 2026-08-13

## Contexto

A Fase 7 prevê edições estruturadas e `ste fix --check|--apply` somente para
correções unívocas. O domínio já reserva `RuleMetadata.safe_autofix` e rejeita
esse valor para regras que não sejam `stable`. As sete regras atuais são
`preview`, estão desabilitadas por padrão e não têm correção inequívoca aprovada.

O fixer toca o arquivo do usuário e cruza contratos difíceis de reverter:
offsets, associação entre regra e edição, compatibilidade de `Diagnostic`,
tratamento de overlaps e metadata divergente, backup, atomicidade e exit codes. Esses pontos precisam
ser decididos antes de TDD ou exposição da CLI.

## Opções consideradas

1. **Adicionar edições opcionais a `Diagnostic`:** associação direta e fácil de
   serializar, ao custo de alterar o contrato público e o schema JSON para todo
   diagnóstico, inclusive quando nenhum consumidor precisa de autofix.
2. **Provider separado por `rule_id`:** preserva `Diagnostic` e JSON `1.0`; o
   provider puro converte somente um diagnóstico elegível em substituição
   exata. Custa um registry adicional e testes contra divergência entre regra e
   provider.
3. **Heurísticas na CLI por mensagem ou texto:** menor número de tipos, mas
   acopla correção a strings editoriais instáveis e contorna o catálogo.
4. **Engine genérico de transformações/DSL:** flexível para edições futuras,
   porém congela uma abstração grande antes do primeiro consumidor seguro.

## Decisão proposta

Escolher a opção 2 e criar uma fronteira `ste_lint.fixer` sem I/O no domínio.
Não alterar `Diagnostic`, `Rule`, o JSON `1.0` nem os exit codes de `ste lint`.

### Identidade e elegibilidade

Não haverá fixer ID separado. `rule_id` é a identidade estável da correção. Um
provider só pode ser registrado quando, simultaneamente:

- a regra existe no catálogo e está implementada;
- `implementation_status == "stable"`;
- `safe_autofix is True`;
- a regra é `deterministic`;
- mantenedor aprovou a precondição e a substituição exata daquele provider.

Registry ausente significa abstenção. Registry duplicado, metadata divergente
ou provider para regra inelegível falha no startup; não degrada para aplicação
parcial. NLP, semantic e human-review não produzem autofix nesta fase.

### Edição estruturada

O contrato Python mínimo é uma estrutura imutável `FixEdit` com:

- `rule_id`;
- `uri`;
- `start_offset` e `end_offset`, intervalo Unicode semiaberto;
- `expected_text`, cópia exata do span diagnosticado;
- `replacement`, texto substituto exato.

O provider recebe `Document` e um `Diagnostic` validado e retorna no máximo uma
edição ou abstém-se. Ele não abre arquivos, não acessa rede e não altera o
documento. A edição precisa ter o mesmo `rule_id`, URI e span do diagnóstico;
`expected_text` precisa coincidir com `Document.text[start:end]`; `replacement`
precisa ser não vazio e diferente do texto esperado. O primeiro incremento não
aceita deleção, inserção fora do span, edição de múltiplos spans por diagnóstico
nem schema serializado.

Um `FixPlan` associa as edições ordenadas ao URI e ao SHA-256 dos bytes UTF-8
originais. Os bytes são lidos diretamente do arquivo e submetidos a SHA-256
antes do decode; o hash nunca é reconstruído a partir de texto. O decode usa
UTF-8 estrito e preserva newlines, como `ste lint`. Antes de planejar, o fixer
exige que reencodar o `Document.text` em UTF-8 produza exatamente os bytes
originais. Assim, BOM UTF-8 presente é preservado como U+FEFF e volta aos mesmos
bytes; entrada não UTF-8 ou sem round-trip byte-exato falha operacionalmente.

O planner ordena por offset inicial, offset final e `rule_id` e rejeita qualquer
interseção entre dois intervalos, inclusive spans idênticos. Spans adjacentes
não se sobrepõem e são permitidos. Não existe uma segunda categoria implícita de
"conflito": metadata divergente, `expected_text` incorreto e overlaps já falham
pelos invariantes próprios. Somente depois dessas validações o planner constrói
o texto candidato. As substituições são aplicadas do último span para o primeiro
para não deslocar offsets ainda pendentes.

### CLI e exit codes

O comando será:

```text
ste fix PATH [--check | --apply]
```

Ausência de modo equivale a `--check`. `--check` e `--apply` são mutuamente
exclusivos. O comando compartilha com `lint` `--config`, `--vocabulary`,
`--text-type`, `--enable-rule` e `--disable-rule`, com a precedência do ADR-009,
mas intersecta a seleção resolvida com o registry de providers elegíveis.
Capacidades exigidas somente por regras sem provider não são carregadas. Ele não
aceita baseline, output JSON ou múltiplos arquivos no primeiro incremento.

`--check` imprime diff unificado determinístico com três linhas de contexto,
labels `--- a/<basename>` e `+++ b/<basename>`, sem timestamps ou paths
absolutos. O output usa LF independentemente dos newlines do documento e marca
original ou candidato sem newline final com a linha ASCII exata
`\ No newline at end of file`. Não há cor, paginação ou variação por TTY. Essa
normalização é somente apresentação; o candidato preserva os newlines reais
fora dos spans editados.

`--check` retorna `0` sem edições, `1` com edições e `2` para falha
operacional/de segurança. `--apply` imprime a quantidade aplicada e o path do
backup somente após a troca, retorna `0` após no-op ou troca validada e `2` se
recusar a transação. No-op não cria backup nem temporário. Erros seguem o prefixo
existente `ste: operational error:` em stderr. O exit code de apply descreve a
operação de fix, não diagnósticos não corrigíveis.

O diff contém os trechos alterados do documento e pode entrar nos logs do shell
ou da CI. O fixer não envia documento, diff ou backup a serviço externo.

### Validação e idempotência

Antes de qualquer escrita, o fixer:

1. valida todos os diagnósticos e providers;
2. valida o plano completo e constrói o texto candidato em memória;
3. parseia e executa novamente o mesmo lint sobre o candidato;
4. exige que não exista diagnóstico do mesmo `rule_id` sobreposto ao span
   transformado de cada alvo;
5. executa novamente os providers e exige zero edição elegível restante.

Falha em qualquer etapa aborta o plano inteiro. Como a substituição é não vazia,
o planner mapeia cada intervalo original para o intervalo transformado e pode
verificar overlap sem coordenadas mágicas. A segunda passagem prova o no-op da
próxima execução e a remoção dos diagnósticos alvo. Regressões de diagnósticos
não corrigíveis são controladas por fixtures e pela suíte completa, pois
comparar achados deslocados em runtime exigiria introduzir outra identidade
pública além da baseline existente. Portanto, a garantia runtime é remoção dos
alvos e zero nova edição elegível; a ausência de regressões conhecidas de outras
regras é gate do corpus e da suíte completa.

Para múltiplas edições não sobrepostas, o intervalo transformado de uma edição é
seu offset original mais a soma dos deltas de replacements anteriores. Exemplo:
se `[2,3)` vira dois code points e `[6,7)` vira um, o primeiro span transformado
é `[2,4)` e o segundo começa em `7`, pois recebe delta `+1` da edição anterior.

### Transação de arquivo e backup

`--apply` aceita somente arquivo regular local e recusa symlink. O backup fica
ao lado do documento e usa o nome:

```text
<nome>.ste-lint-backup.sha256-<64-hex-do-original>
```

O backup contém os bytes crus exatos do original, é criado de forma exclusiva e
nunca é sobrescrito. Se já existir, seus bytes precisam corresponder ao hash e
ao original; caso contrário, a operação falha. Antes da troca, o fixer relê o
arquivo e compara o SHA-256 com o plano para detectar mudança concorrente.

O candidato é codificado em UTF-8 e precisa preservar byte a byte tudo fora dos
spans editados, inclusive BOM e newlines. Ele é gravado em arquivo temporário no
mesmo diretório, com os mode bits POSIX do original quando a plataforma os
expõe, flush e sincronização suportada pela plataforma. O fixer relê o
temporário e confere seu SHA-256 contra os bytes candidatos esperados antes da
troca, que usa `os.replace`. Ownership, ACLs, extended attributes
e metadata específica de plataforma ficam fora do primeiro incremento e são
documentados como limitação. Temporários são removidos em falhas anteriores à
troca. O backup é intencionalmente preservado e pode conter conteúdo técnico
confidencial; ele continua local e nunca entra automaticamente em Git ou pacote.

Não se promete lock contra todo escritor concorrente. Mudança detectada aborta;
processos que ignoram coordenação de arquivos permanecem risco documentado.

## Alternativas rejeitadas

- permitir fixer em regra `preview`, porque transforma evidência insuficiente
  em mutação automática;
- usar `suggestion` como replacement, porque sugestão humana não é contrato de
  edição nem carrega precondição de span;
- escolher uma correção quando spans se sobrepõem, porque prioridade implícita
  pode alterar significado;
- aplicar edições válidas e pular inválidas, porque deixa estado parcialmente
  previsto;
- sobrescrever um backup fixo, porque destrói a recuperação anterior;
- escrever o arquivo in-place, porque crash pode truncar o original;
- implementar a infraestrutura sem provider real aprovado, porque isso congela
  abstrações sem validar o consumidor.

## Estratégia de testes e rollout

- unitários: invariantes de `FixEdit`, elegibilidade, ordenação, overlap,
  metadata divergente, expected text e composição de spans;
- integração: check sem escrita, perfil byte a byte do diff, exit codes, apply
  stdout, no-op sem backup, backup, permissões, BOM, CRLF/LF, Unicode, symlink,
  mudança concorrente e falhas injetadas;
- por provider: ao menos 3 correções, 3 abstenções, 3 edge cases, idempotência e
  lint pós-fix;
- regressão: suíte base offline, corpus rotulado e scan de recursos protegidos;
- rollout: primeiro provider único, somente determinístico e `stable`; novos
  providers passam por aprovação e evidência próprias.

O rollback é remover o provider e manter `safe_autofix = False`; `ste lint`
permanece inalterado. O comando não deve ser publicado sem ao menos um provider
real aprovado.

## Riscos e mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| span ou texto stale | média | alto | `expected_text`, hash e releitura antes da troca |
| providers sobrepostos | média | alto | rejeição do plano completo |
| crash durante escrita | baixa | alto | backup, temporário no mesmo diretório e `os.replace` |
| falso positivo promovido cedo | média | alto | `stable` + `safe_autofix` + aprovação específica |
| backup expõe conteúdo local | média | médio | nome explícito, nenhuma coleta ou inclusão em pacote |
| metadata não portável muda | baixa | médio | preservar mode bits e documentar ownership/ACL/xattrs |
| abstração não serve ao primeiro caso | média | médio | implementação bloqueada até provider real aprovado |

## Consequências

- o contrato de lint e JSON permanece compatível;
- providers duplicam uma pequena parte da associação regra/correção, compensada
  por validação de registry e testes pós-fix;
- o primeiro incremento suporta somente substituição de um span existente;
- correções multi-span, inserções, JSON de edits e múltiplos arquivos exigem
  nova decisão compatível;
- todas as regras atuais continuam sem autofix até promoção e aprovação
  separadas.

## Aprovação e gates remanescentes

O mantenedor aceitou este ADR e a spec da Fase 7 em 2026-08-13. Esse aceite
congela o contrato documental, mas não autoriza implementação. Nenhum tipo,
provider, comando ou teste de implementação pode ser criado antes de:

1. uma regra determinística ser promovida a `stable` com evidência suficiente;
2. o mantenedor aprovar a precondição e a substituição exata do primeiro
   provider;
3. o mantenedor autorizar explicitamente o início do TDD.

## Revisão independente

A revisão local de consistência foi executada em 2026-08-13. Após autorização
do mantenedor, a primeira revisão externa somente leitura com `cursor-agent` e
`composer-2.5-fast` aprovou a direção e pediu quatro correções antes do aceite:
definir conflito, fechar identidade de bytes, especificar o perfil do diff e
alinhar AC8 à validação runtime. Esta versão remove a categoria indefinida,
define round-trip/hash cru, congela o diff mínimo e separa garantia runtime do
gate de regressão. Também incorpora os gaps não bloqueantes de CLI, apply,
no-op, mapeamento de spans e inventário arquitetural.

A segunda rodada somente leitura confirmou todos os quatro bloqueios resolvidos,
não encontrou bloqueio material remanescente e recomendou aprovação da spec e
deste ADR. A revisão não autoriza implementação: o DoR e as quatro aprovações da
seção anterior continuavam obrigatórios naquele parecer. O mantenedor aceitou o
contrato em 2026-08-13; os três gates de implementação acima permanecem.
