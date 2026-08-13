# Spec: fixer seguro da Fase 7

Status: Approved
Autor: Codex, sob autorização do mantenedor
Última atualização: 2026-08-13
Approved by: project maintainer, 2026-08-13
Plano relacionado: [`PLANS.md`](../PLANS.md)

## Resumo

O `ste-lint` continuará somente leitura para diagnósticos sem correção única. A
Fase 7 acrescentará preview determinístico e aplicação transacional apenas para
uma regra `stable` que declare `safe_autofix` e tenha um provider aprovado para
substituir exatamente o span diagnosticado. `ste fix` não será implementado até
o ADR-015 e o primeiro provider serem aprovados explicitamente.

## Problema

Hoje o autor precisa interpretar cada diagnóstico e editar o documento à mão.
Isso é correto para os sete detectores atuais, pois todos permanecem `preview`
e suas avaliações não sustentam promoção ou correção automática. Porém, quando
uma futura correção for comprovadamente única, repetir essa edição manualmente
adicionará risco de atingir o span errado e impedirá uso verificável em CI.

## Tese da feature

Um fixer é seguro somente quando transforma um diagnóstico estável em uma
substituição exata, revisável e transacional; ausência de certeza deve produzir
zero edição, não uma tentativa heurística.

## Comportamento atual e delta observável

Atualmente `ste lint` lê um arquivo e nunca altera seu conteúdo. A Fase 7 não
muda esse comportamento. Ela acrescenta um comando separado para um único
arquivo TXT ou Markdown:

```text
ste fix PATH
ste fix PATH --check
ste fix PATH --apply
```

Sem opção de modo, `ste fix PATH` equivale a `--check`. `--check` e `--apply`
são mutuamente exclusivos.

O comando aceita `--config`, `--vocabulary`, `--text-type`, `--enable-rule` e
`--disable-rule` com a mesma precedência de `ste lint`, mas executa somente a
interseção da seleção resolvida com providers elegíveis. Ele não carrega NLP ou
outra capacidade necessária exclusivamente a uma regra sem autofix. Baseline
nunca seleciona nem oculta uma edição. Somente diagnósticos de regras `stable`,
marcadas `safe_autofix` e com provider registrado podem produzir uma edição.

### Preview e check

- não escreve, cria backup ou modifica metadados do arquivo;
- imprime um diff unificado determinístico quando existem edições elegíveis:
  três linhas de contexto, labels `--- a/<basename>` e `+++ b/<basename>`,
  nenhum timestamp ou path absoluto e line endings LF na apresentação;
- representa a ausência de newline final com a linha ASCII exata
  `\ No newline at end of file`, sem alterar os bytes do arquivo;
- o diff contém os trechos alterados do documento e pode ser capturado por logs
  do shell ou da CI; o comando não envia esse conteúdo a serviço externo;
- retorna `0` quando não há edição, `1` quando o diff contém edição e `2` para
  falha operacional ou de segurança;
- diagnósticos sem provider seguro permanecem fora do diff.

### Apply

- calcula e valida o mesmo plano mostrado por `--check`;
- recusa symlink, arquivo não regular, alteração concorrente detectada, spans
  sobrepostos ou qualquer edição que não corresponda ao texto original;
- cria antes da troca um backup adjacente, verificável e sem sobrescrita;
- parseia e executa novamente o mesmo lint em memória sobre o documento
  resultante e então os mesmos providers; cada diagnóstico alvo precisa
  desaparecer e, se ainda houver edição elegível, nenhuma troca é feita;
- troca o arquivo atomicamente somente depois de todas as verificações;
- após a troca, imprime a quantidade aplicada e o path do backup;
- retorna `0` em sucesso ou quando não há edição e `2` se a transação for
  recusada. No-op não cria backup nem temporário. Diagnósticos não corrigíveis
  não transformam sucesso em exit `1`.

Não existe aplicação parcial: um plano inválido impede todas as edições daquele
arquivo.

## Critérios de aceite

- [ ] AC1: `ste fix PATH` e `--check` produzem os mesmos bytes em stdout, não
  alteram o arquivo e retornam `1` exatamente quando há edição elegível.
- [ ] AC2: a mesma entrada, configuração e versão do catálogo produzem o mesmo
  conjunto ordenado de edições e o mesmo diff no perfil declarado, sem variação
  por TTY, plataforma ou localização absoluta do arquivo.
- [ ] AC3: cada edição pertence ao mesmo `rule_id`, URI e intervalo semiaberto
  do diagnóstico de origem; o texto esperado coincide exatamente com os code
  points do `Document` e a substituição é não vazia e diferente dele.
- [ ] AC4: regra `preview`, `nlp`, `semantic`, `human-review`, sem
  `safe_autofix` ou sem provider aprovado produz zero edição.
- [ ] AC5: qualquer interseção entre spans, inclusive spans idênticos, span fora
  do documento, texto esperado divergente ou mudança concorrente resultam em
  exit `2` e deixam o original intacto; spans adjacentes não se sobrepõem.
- [ ] AC6: antes de `--apply`, existe um backup adjacente com os bytes exatos do
  original; backup existente nunca é sobrescrito silenciosamente.
- [ ] AC7: `--apply` calcula a identidade sobre bytes crus, preserva BOM quando
  presente, conteúdo não editado, newlines e mode bits POSIX quando disponíveis,
  e usa uma troca atômica no mesmo filesystem.
- [ ] AC8: em runtime, cada diagnóstico alvo desaparece e o replanejamento do
  resultado produz zero edição elegível; uma segunda execução é no-op. Ausência
  de regressões de outras regras é provada no corpus e na suíte, não inferida por
  identidade de diagnóstico em runtime.
- [ ] AC9: cada provider tem fixtures autorais positivas, negativas, de borda,
  overlap e idempotência, além da suíte completa offline.
- [ ] AC10: nenhuma dependência, rede, recurso normativo ou conteúdo de backup
  entra no wheel, sdist ou repositório.
- [ ] AC11: `--check` e `--apply` juntos falham com exit `2` e prefixo
  `ste: operational error:`; `--apply` no-op retorna `0`, não escreve e não cria
  backup; apply bem-sucedido só anuncia count e backup depois da troca.

## Non-goals

- corrigir qualquer uma das sete regras enquanto ela permanecer `preview`;
- reescrever sentenças, escolher palavras, interpretar significado ou usar NLP,
  semantic reviewer ou LLM para produzir edições;
- expor JSON/SARIF de edições no primeiro incremento;
- aceitar stdin, diretórios, múltiplos arquivos, PDF, DOCX ou HTML;
- aplicar somente parte de um plano conflitante;
- usar baseline como autorização para editar;
- preservar ownership, ACLs, extended attributes ou metadata específica de
  plataforma no primeiro incremento;
- adicionar fixer IDs independentes de `rule_id` ou uma DSL genérica de
  transformações.

## Métricas e guardrails

- 100% das fixtures de provider devem ser idempotentes;
- zero escrita parcial nas falhas injetadas antes da troca atômica;
- zero novo diagnóstico conhecido no corpus de regressão de cada provider;
- guardrail: nenhum provider é registrado sem regra `stable`, correção única e
  aprovação humana específica.

## Dependências e premissas

- ADR-002 continua definindo offsets Unicode semiabertos no `Document`;
- ADR-004 continua mantendo `Diagnostic` imutável e sem I/O;
- ADR-011 permanece em JSON `1.0`, pois o primeiro fixer não serializa edições;
- o contrato técnico proposto está em
  [`ADR-015`](adr/0015-safe-fixer-contract.md);
- os providers são código do projeto, offline e testados com conteúdo
  sintético/autoral.

## Candidata ao primeiro provider

Nenhuma regra atual satisfaz o gate. A única candidata mecânica plausível é
`STE-I9-LIST-001`: nos casos já cobertos, o diagnóstico aponta para o ponto final
de um lead-in diretamente associado à lista, e o provider proposto substituiria
exatamente `.` por `:`. Isto é uma recomendação para avaliação, não promoção:

- a regra ainda é `preview/info`, com limite inferior Wilson de precisão 0,566;
- `docs/f4-evaluation.md` e `docs/rule-candidates.md` registram que nenhuma
  correção atual foi aprovada como inequívoca;
- sem falsos positivos, são necessárias pelo menos 73 emissões corretas no total
  para o limite inferior Wilson bilateral de 95% alcançar 0,95; o seed atual tem
  5, portanto o piso aritmético seria mais 68, além de diversidade e revisão
  independente suficientes;
- a revisão normativa precisa confirmar que a troca de pontuação, sem reescrita
  do lead-in, é uma correção válida para toda a subclasse detectada.

`STE-I9-PUNCT-001`, as regras de comprimento e as duas regras NLP exigem
reescrita ou julgamento e ficam excluídas. A implementação permanece bloqueada
até o mantenedor aprovar a candidata, sua evidência, a promoção e a substituição
exata.

## Estado da revisão

A revisão local de consistência foi executada em 2026-08-13. Após autorização
do mantenedor, a primeira revisão externa somente leitura com `cursor-agent` e
`composer-2.5-fast` aprovou a direção, mas pediu mudanças em conflito de edits,
identidade de bytes, perfil do diff e escopo da validação runtime. A segunda
rodada confirmou os quatro bloqueios resolvidos, não encontrou bloqueio material
remanescente e recomendou aprovação documental. O mantenedor aprovou a spec em
2026-08-13. Implementação continua fechada até o DoR completo.
