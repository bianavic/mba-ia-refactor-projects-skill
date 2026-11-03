# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

Python 3.11.18 (`.python-version`).

```bash
pip install -r requirements.txt
cp .env.example .env   # preencha e exporte as variáveis (SECRET_KEY, ADMIN_PASSWORD, SEED_CUSTOMER_PASSWORD...)
python app.py
```

A aplicação sobe em `http://localhost:5000` (`APP_PORT`). O banco SQLite (`DB_PATH`, padrão `loja.db`) é criado no primeiro boot com os produtos de exemplo; a conta admin e os clientes de exemplo só são semeados quando `ADMIN_PASSWORD` / `SEED_CUSTOMER_PASSWORD` estão definidos. Senhas em texto puro de um banco antigo são convertidas em hash no boot.

Autenticação: `POST /login` devolve `token`; envie `Authorization: Bearer <token>` nas rotas protegidas.

## Testes de contrato

```bash
export DB_PATH="$(mktemp -d)/loja-test.db" ADMIN_PASSWORD=<senha> SEED_CUSTOMER_PASSWORD=<senha>
python app.py > "$(dirname "$DB_PATH")/app.log" 2>&1 &
APP_LOG_FILE="$(dirname "$DB_PATH")/app.log" ./api-test.sh
```

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
