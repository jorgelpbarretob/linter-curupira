# Rubrica semântica contável — estudo Hermes × Curupira v2

Status: ativo para o lote v2 (cases 001–014, pacote cego em `artifacts/hermes-case-study/v2/blind/`)

## Propósito

O gate operacional (`curupira lint`, residual 0 de `CURUPIRA-PT-PONT-001`) é binário e já
empata com frequência: modelos limpos passam sozinhos. Ele não mede legibilidade.
Esta rubrica transforma o **residual semântico** em métrica contínua e contável,
aplicável cega aos dois braços (control e cli).

Ela é o desfecho primário de qualidade do estudo. O gate de lint permanece separado,
como gate operacional.

## Categorias (4, fixas)

1. `ambiguous-reference` — pronome ou referência com mais de um antecedente possível
   no contexto ("o painel", "deste", "ele" sem antecedente único).
2. `implicit-agent` — ação imperativa sem agente definido quando o agente importa
   para a execução ("desligar a bomba" sem dizer quem: operador, sistema, automático).
3. `multiple-actions` — sentença ou passo único que empilha 2 ou mais ações obrigatórias
   (risco de executar pela metade).
4. `terminology` — jargão técnico sem qualificador necessário para executar
   (válvula/registro/bomba/sensor/tolerância sem tipo, faixa ou fonte).

## Escala

- Contagem por categoria e total. Cada ocorrência distinta conta uma vez.
- `severity`: `major` = pode causar erro operacional ou decisão errada;
  `minor` = incômodo de leitura.
- Zero achados em uma categoria é um resultado válido.
- Preferência de estilo não conta. Não conta o que o próprio texto resolve no contexto.

## Validação (anti-alucinação)

Cada achado deve citar `excerpt` literal do artefato. O script verifica o trecho por
substring (whitespace normalizado). Achado sem trecho verificável é rejeitado e
registrado em `invalid_rejected`. Achados duplicados (mesma categoria + trecho) são
deduplicados.

## Aplicação cega

1. Mesmos artefatos A/B sem rótulo de condição.
2. Painel fixo: Kimi `kimi-k2.7` (temp=1, exigência da API) e Maritaca `sabia-4-thinking` (temp=0).
3. Nenhum revisor recebe informação de braço, prompt de tratamento ou resultado de lint.
4. Unblind só após todos os scores salvos, via `KEY-DO-NOT-SHARE-until-scores.json`.

## Métricas reportadas

- Por artefato: `findings_total`, `findings_major`, `findings_minor`, `by_category`.
- Por braço (após unblind): média de achados por artefato, delta cli − control, por revisor.
- Preferência por caso: braço com menos achados (desempate por `major`); empate declarado.
- Concordância entre revisores: Spearman dos totais por artefato + concordância de sinal
  (achados > 0 vs 0).
- Tokens do painel sempre logados (política fixada v2).

## Ferramenta

`tools/curupira/semantic_rubric.py` — saída em
`artifacts/hermes-case-study/v2/blind/semantic-rubric-scores.json`.

## Limitações declaradas

- Revisores LLM têm variância própria; dois revisores independentes mitigam, não eliminam.
- A categoria `terminology` depende do domínio do caso; casos fora de chão de fábrica
  tendem a zero nela.
- Contagem é por artefato, não por sentença; tamanho do artefato influencia o total.
- O que derruba a métrica: se os dois revisores discordarem sistematicamente
  (Spearman < 0,3), a contagem não serve como desfecho primário e volta para revisão.
