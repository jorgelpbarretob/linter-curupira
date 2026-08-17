# Mitigação case-008

Sintoma:
- fila jobs-hot cresceu após as 21h
- worker-b preso em batch antigo
- latência subiu e health check flipou

Mitigação imediata:
- restart da unit worker-b.service (já resolveu caso similar ontem)

Verificação:
- após restart, checar health e tamanho da fila jobs-hot
- se fila continuar subindo após 10 min, abrir SEV2 com print do painel

Escalonamento:
- não reiniciar broker sem autorização