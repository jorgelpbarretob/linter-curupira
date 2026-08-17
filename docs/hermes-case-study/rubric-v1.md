# Rubrica de aceite — estudo Hermes × Curupira v1

## Princípios

- Critérios binários para risco. Escala curta para qualidade.
- Erro técnico crítico **bloqueia** aceite mesmo com nota editorial alta.
- Mesmos testes no controle e no tratamento.
- Só o tratamento pode usar Curupira **durante** a execução.

## Critérios

| Critério | Método | Regra de aceite |
|---|---|---|
| Correção técnica | Conferência contra fontes fornecidas | Zero erro crítico |
| Cobertura da solicitação | Checklist da tarefa | 100% dos itens obrigatórios |
| Executabilidade | Revisor tenta seguir o procedimento | Passos acionáveis, ordenados e completos |
| Clareza | Escala 1–5 | Nota mínima 4 |
| Achados Curupira | `curupira lint` final com regras do aceite | Zero diagnóstico remanescente dessas regras |
| Integridade editorial | Diff e fontes | Sem fatos inventados. Sem remoção indevida |
| Formatação e integração | Checks do repositório | Todos os checks obrigatórios OK |

## Escala de clareza (1–5)

1. Incompreensível ou contraditório
2. Ambíguo em pontos críticos
3. Usável com esforço e perguntas
4. Claro para operador experiente
5. Claro e direto, mínimo de interpretação

## Classes de aceite da rodada

| Classe | Definição |
|---|---|
| aceito | Passa todos os critérios binários e clareza ≥4 |
| aceito_retrabalho_menor | Falha só cosmético/formatação leve, sem risco operacional |
| rejeitado_retrabalho_maior | Falha de cobertura, clareza <4 ou residual Curupira |
| bloqueado | Erro técnico crítico ou requisito obrigatório faltante |

## Avaliação cega

1. Artefatos renomeados sem rótulo de condição
2. Dois revisores independentes
3. Divergência de classe ou de erro crítico → terceiro revisor
4. Registrar IDs de revisor, timestamps e notas brutas em `artifacts/.../evaluation/`

## Rubrica semântica contável

Para medir sentido operacional além de PONT-001, use:

`docs/hermes-case-study/semantic-rubric-v1.md`

- 4 categorias C1–C4, escala 0–2, S=0..8
- preferência A/B determinística
- helper: `tools/curupira/semantic_rubric_score.py`
