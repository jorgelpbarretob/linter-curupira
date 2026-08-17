# Cases — estudo Hermes × Curupira

| ID | Tipo | Título | Proveniência | Status |
|---|---|---|---|---|
| case-001 | regressao | Remover ponto e vírgula em procedimento de bomba | synthetic | frozen-draft |
| case-002 | criacao | Criar procedimento de recuperação de serviço a partir de insumos | synthetic | frozen-draft |
| case-003 | revisao | Corrigir ambiguidade sem mudar fatos | synthetic | frozen-draft |
| case-004 | atualizacao | Atualizar runbook após mudança de CLI | synthetic | frozen-draft |
| case-005 | transformacao | Converter notas em procedimento | synthetic | frozen-draft |
| case-006 | incidente | Instrução de mitigação a partir de log sanitizado | synthetic | frozen-draft |

Alvo do protocolo: 12–20 casos. Banco atual: 16 casos.

## Lote difícil 1 (tokens + legibilidade)

| ID | Residual input | Chars input | Foco |
|---|---:|---:|---|
| case-007 | 8 | 787 | tokens + legibilidade |
| case-008 | 8 | 453 | tokens + legibilidade |
| case-009 | 9 | 364 | tokens + legibilidade |
| case-010 | 8 | 592 | tokens + legibilidade |

## Lote difícil 2 (tokens + legibilidade)

Gerado por `tools/curupira/make_case_hard.py` (2026-08-17).
Cases 011–014 reautorados para o estudo v2 (bateria `run-v2-01`); definições
anteriores constam no histórico git.

| ID | Tipo | Residual input | Chars input | Foco |
|---|---|---:|---:|---|
| case-011 | revisao-dificil | 5 | 308 | partida de bomba com intertravamentos |
| case-012 | incidente-dificil | 6 | 262 | alarme denso → ação curta |
| case-013 | atualizacao-dificil | 5 | 300 | checklist CI → curupira lint |
| case-014 | transformacao-dificil | 7 | 330 | rascunho calibração → POP |
| case-015 | atualizacao-dificil | 6 | 678 | troca de tag + enxugar |
| case-016 | incidente-dificil | 12 | 908 | timeline densa → mitigação curta |

## Composição do banco vs pré-registro v1

- Sem residual no input: 5/16 (case-002 a case-006). Alvo do pré-registro:
  pelo menos um terço sem ponto e vírgula no insumo. Cumprido (31%).
- Com residual no input: 11/16 (residual esperado no controle).
- Desfecho primário aprovado: achados residuais das regras habilitadas.
  Secundários com correção de Holm. Ver
  `docs/hermes-case-study/power-analysis-v1.md`.
