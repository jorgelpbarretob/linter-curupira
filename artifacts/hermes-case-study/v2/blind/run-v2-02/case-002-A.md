# Procedimento de recuperação — curupira-api

Restaurar `curupira-api` após falha de healthcheck.

1. Confirme a falha: `GET http://127.0.0.1:8080/health` não retorna 200.
2. Leia os últimos 100 eventos: `journalctl -u curupira-api.service -n 100`.
3. Reinicie a unidade: `systemctl restart curupira-api.service`.
4. Verifique o healthcheck: `GET http://127.0.0.1:8080/health` deve retornar 200.
5. Se o healthcheck falhar, repita os passos 3 e 4. No máximo 3 falhas após restart.
6. Se o healthcheck falhar 3 vezes após restart, escale para o plantão. Não invente contato.
7. Verificação final: `GET http://127.0.0.1:8080/health` retorna 200. Só então o serviço está restaurado.
