# Mitigação case-008

## Sintoma
- fila jobs-hot cresce após 21h
- worker-b parece preso em batch antigo
- latência subiu
- health flipou
- drain não esvaziou

## Mitigação imediata
- restart unit worker-b.service
- janela de normalização 10 min

## Verificação
- checar /health
- verificar tamanho da fila jobs-hot
- confirmar processamento de novos jobs

## Escalonamento
- SEV2 se não normalizar em 10 min
- abrir SEV2 com print do painel se fila continuar subindo
- não reiniciar broker sem autorização
