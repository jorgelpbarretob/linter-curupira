# Recuperacao do servico curupira-api

Use este procedimento apos falha de healthcheck.

1. Confirme a unidade systemd `curupira-api.service`.
2. Leia as ultimas 100 linhas do log com `journalctl -u curupira-api.service -n 100`.
3. Reinicie o servico com `systemctl restart curupira-api.service`.
4. Execute o healthcheck: `GET http://127.0.0.1:8080/health`.
5. Aceite sucesso somente se a resposta for 200.
6. Se o healthcheck falhar, volte ao passo 3.
7. Se o healthcheck falhar 3 vezes apos o restart, pare o ciclo.
8. Escale para o plantao. Nao invente contato.
9. Verificacao final: `GET http://127.0.0.1:8080/health` deve retornar 200.
