# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

Python 3.11.18 (`.python-version`).

```bash
pip install -r requirements.txt
[ -f .env ] || cp .env.example .env    # só na primeira vez; preencha SECRET_KEY, ADMIN_PASSWORD e SEED_CUSTOMER_PASSWORD
set -a; source .env; set +a            # carrega o .env neste terminal (o app não lê o arquivo sozinho)
python app.py
```

A aplicação sobe em `http://localhost:5000` (`APP_PORT`). O banco SQLite (`DB_PATH`, padrão `loja.db`) é criado no primeiro boot com os produtos de exemplo; a conta admin e os clientes de exemplo só são semeados quando `ADMIN_PASSWORD` / `SEED_CUSTOMER_PASSWORD` estão definidos. Senhas em texto puro de um banco antigo são convertidas em hash no boot.

Autenticação: `POST /login` devolve `token`; envie `Authorization: Bearer <token>` nas rotas protegidas.

## Testar com SQLite (passo a passo)

Usa um arquivo SQLite temporário. Assim o `api-test.sh` consegue fazer as checagens no banco (`sqlite3`) e no log (`APP_LOG_FILE`).

```bash
cd code-smells-project

[ -f .env ] || cp .env.example .env              # só na primeira vez; preencha SECRET_KEY, ADMIN_PASSWORD e SEED_CUSTOMER_PASSWORD
set -a; source .env; set +a                      # carrega o .env neste terminal
export DB_PATH="$(mktemp -d)/loja-test.db"       # banco temporário (sobrescreve DB_PATH=loja.db do .env)
export APP_LOG_FILE="$(dirname "$DB_PATH")/app.log"

python app.py > "$APP_LOG_FILE" 2>&1 &          # sobe a app gravando o log (porta 5000)
sleep 3
grep "SERVIDOR INICIADO" "$APP_LOG_FILE"        # confirma a subida

sqlite3 "$DB_PATH" "SELECT id, nome, preco, estoque FROM produtos LIMIT 3;"   # produtos de exemplo do boot
sqlite3 "$DB_PATH" "SELECT id, nome, email, tipo FROM usuarios;"              # admin e clientes de exemplo

./api-test.sh                                    # testes de contrato
```

Resultado esperado no fim:

```
TOTAL: 173 checks | failures: 0 | skipped: 0
Coverage: 21 endpoints inventoried / 21 exercised
```

Encerrar a aplicação e apagar o banco temporário:

```bash
kill $(lsof -t -iTCP:5000 -sTCP:LISTEN)
rm -rf "$(dirname "$DB_PATH")"
```

> **Atenção à ordem:** a app e o terminal só enxergam as variáveis do momento em que foram iniciados. Se
> você já tinha a app rodando na porta 5000, ou exportou variáveis antes de editar o `.env`, pare a app
> (`kill $(lsof -t -iTCP:5000 -sTCP:LISTEN)`) e repita o bloco inteiro, na ordem acima. Se outra app
> responder na 5000, o `api-test.sh` para com "not isolated — o app não usa o DB_PATH informado".

Pontos de atenção:

- `DB_PATH` precisa estar numa pasta temporária (`/var/folders`, `/tmp` ou `/private/tmp`). Fora dela, o `api-test.sh` recusa com "not isolated".
- O `api-test.sh` apaga o admin no T8 (reset). Para rodar `code-smells-project-api-curls.http` depois dele, pare a app e suba de novo com um `DB_PATH` novo (`mktemp -d`). No mesmo servidor, o login do item 3 responde `401` e os itens seguintes falham em cascata.
- O teste T8 faz um reset que apaga tudo. Para rodar de novo, reinicie a app com um `mktemp -d` novo.
- Se a app estiver em outra porta (`APP_PORT`), passe `BASE_URL=http://localhost:<porta> ./api-test.sh`.
- Sem `.env`, exporte antes: `export ADMIN_PASSWORD=... SEED_CUSTOMER_PASSWORD=...`.

## Conclusão da Fase 3

Saída do `completion-box.sh` da skill, que só emite a caixa quando `arch-check.sh` e o
log de validação passam. Log: [`evidence/logs/code-smells-project-validation.txt`](../evidence/logs/code-smells-project-validation.txt).

<!-- BEGIN:completion-box -->
```text
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
code-smells-project/
├── .arch-check.conf
├── .env.example
├── .python-version
├── README.md
├── api-test.sh
├── app.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── controllers/
│   ├── __init__.py
│   ├── admin_controller.py
│   ├── pedido_controller.py
│   ├── produto_controller.py
│   ├── relatorio_controller.py
│   ├── sistema_controller.py
│   └── usuario_controller.py
├── database/
│   ├── __init__.py
│   └── connection.py
├── errors/
│   ├── __init__.py
│   ├── exceptions.py
│   └── handlers.py
├── middleware/
│   ├── __init__.py
│   └── auth.py
├── models/
│   ├── __init__.py
│   ├── pedido_model.py
│   ├── produto_model.py
│   └── usuario_model.py
├── requirements.txt
├── routes/
│   ├── __init__.py
│   ├── admin_routes.py
│   ├── pedido_routes.py
│   ├── produto_routes.py
│   ├── relatorio_routes.py
│   ├── sistema_routes.py
│   └── usuario_routes.py
├── services/
│   ├── __init__.py
│   ├── admin_service.py
│   ├── notificacao_service.py
│   ├── pedido_service.py
│   └── usuario_service.py
└── utils/
    ├── __init__.py
    ├── mascaramento.py
    ├── paginacao.py
    └── seguranca.py

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
```
<!-- END:completion-box -->

## Future improvements

- Retention limit for user personal data — left open in the plan — needs a retention policy (age after which personal fields are de-linked).
- Rotate the previously hardcoded `SECRET_KEY` and the seeded passwords of any existing `loja.db` or deployment — outside the code — they are in git history; removing them from the code does not un-leak them.
- Bearer tokens cannot be revoked before expiry (a deleted or demoted user's token stays valid until `TOKEN_TTL_SECONDS`) — accepted by the user — residual of "Signed bearer token".
- Accounts already in an existing `loja.db` keep their current passwords (now hashed) until rotated or the DB is recreated — accepted by the user — residual of "Passwords from env".
- With `ADMIN_QUERY_ENABLED=true` an admin still has full control of the database — accepted by the user — residual of "Env flag, off by default".
- Clients that never send `page`/`per_page` still receive whole tables — accepted by the user — residual of "Opt-in".
- Products, orders and users already stored with invalid values (short names, invalid categories, negative quantities, unknown users) are left as they are — accepted by the user — residual of "Validate → 400" / "Update uses create's rules".
- `PUT /pedidos/<id>/status` on a nonexistent order answers 200 — noticed during Phase 3 — outside the approved plan, kept as in the original.
- Cancelling an order does not restore stock, although the notification says "Devolver estoque" — noticed during Phase 3 — outside the approved plan, kept as in the original.
- `usuarios.email` has no unique constraint; signup accepts duplicate emails — noticed during Phase 3 — outside the approved plan, kept as in the original.
- `POST /login` has no rate limiting or lockout — noticed during Phase 3 — outside the approved plan, kept as in the original.
- CORS allows every origin on every route (`CORS(app)`) — noticed during Phase 3 — outside the approved plan, kept as in the original.
- An invalid statement in `POST /admin/query` (when enabled) answers a generic 500 instead of 400 — noticed during Phase 3 — outside the approved plan.
- The app runs on the Werkzeug development server — noticed during Phase 3 — outside the approved plan; use a production WSGI server (gunicorn/waitress) to deploy.
