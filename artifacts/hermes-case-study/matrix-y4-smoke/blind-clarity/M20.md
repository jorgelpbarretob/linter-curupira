Sintoma: worker-b saturado; fila jobs-hot acumulada; SEV2; janela 10 min.
Mitigação: reiniciar unit worker-b.service; drenar fila jobs-hot.
Verificar: fila esvaziada; service ativo.
Escalonamento: se persistir após 10 min, elevar para plantão.
