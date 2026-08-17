# Insumos técnicos (sintéticos)

- Serviço: `curupira-api`
- Healthcheck: `GET http://127.0.0.1:8080/health` deve retornar 200
- Unidade systemd: `curupira-api.service`
- Log: `journalctl -u curupira-api.service -n 100`
- Ação de restart permitida: `systemctl restart curupira-api.service`
- Se healthcheck falhar 3 vezes após restart, escalar para plantão (sem inventar contato)
