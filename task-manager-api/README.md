# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Refatorada para MVC: `routes/` → `controllers/` → `services/` (casos de uso com mais de um model) → `models/`, com `config/`, `database/`, `errors/`, `middleware/` e `utils/`.

## Como rodar

```bash
python -m venv .venv && source .venv/bin/activate   # Python 3.11.18 (.python-version)
pip install -r requirements.txt
cp .env.example .env          # preencha SECRET_KEY, SEED_ADMIN_PASSWORD e SEED_USER_PASSWORD
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000` (`APP_PORT`). O `seed.py` popula o banco SQLite (`DATABASE_URL`, padrão `sqlite:///tasks.db`) com usuários, categorias e tasks de exemplo; uma conta cuja senha não está no ambiente não é criada.

Autenticação: `POST /login` devolve `token`; envie `Authorization: Bearer <token>`. Acesso por rota: `/health`, `/`, `POST /login`, `POST /users` públicos; `GET /users`, `/reports/summary` e escrita em `/categories` só admin; `/users/<id>`, `/users/<id>/tasks`, `/reports/user/<id>` e `PUT/DELETE /tasks/<id>` dono ou admin; demais rotas exigem login. Listas aceitam `?page=&per_page=` (opcional, máx. 100).

## Testes de contrato

```bash
T=$(mktemp -d); export DATABASE_URL="sqlite:///$T/tasks.db" SEED_ADMIN_PASSWORD=<senha> SEED_USER_PASSWORD=<senha> APP_LOG_FILE=$T/app.log
python seed.py && python app.py > "$APP_LOG_FILE" 2>&1 &
BASE_URL=http://localhost:5000 ./api-test.sh
```

## Future improvements

- Retention limit for users' personal data (names and emails are kept indefinitely, also for deactivated accounts) — left open in the plan — the retention period is a policy decision; needs a deactivation timestamp and a de-link/anonymize job.
- Rotate the previously hardcoded `SECRET_KEY` (`super-secret-key-123`), the SMTP password (`senha123`) and the seeded passwords (`1234`, `abcd`, `pass`) of any existing deployment — outside the code — they remain in git history; removing them from the code does not un-leak them.
- Purge application logs already written with user names, emails and password hashes (old `print` of `str(e)`) — outside the code — logs cannot be fixed by a code change.
- A stolen token stays valid until `TOKEN_TTL_SECONDS` (no revocation list; deleted or deactivated users are refused) — accepted by the user — residual of "Signed expiring token".
- Accounts that never log in again keep their legacy MD5 hash until reset or re-seeded — accepted by the user — residual of "Rehash on next login".
- Clients that never send `page`/`per_page` still receive whole tables — accepted by the user — residual of "Opt-in page/per_page".
- Any logged-in user sees every task and its assignee's name — accepted by the user — residual of "Confirm as proposed".
- Tasks, users and categories already stored with invalid values (empty names, non-boolean `active`, invalid colors) are left as they are — accepted by the user — residual of "Validate, answer 400".
- `POST /login` has no rate limiting or lockout — noticed during Phase 3 — outside the approved plan, kept as in the original.
- CORS allows every origin on every route (`CORS(app)`) — noticed during Phase 3 — outside the approved plan, kept as in the original.
- The owner of a task can reassign it to any user (`user_id` in `PUT /tasks/<id>`) and then loses access to it — noticed during Phase 3 — outside the approved plan, kept as in the original.
- `datetime.utcnow()` is deprecated from Python 3.12 on (not in 3.11, the version in use) — noticed during Phase 3 — outside the approved plan; replace with timezone-aware datetimes when the runtime moves past 3.11.
- The `.venv` created by Python 3.11.18 bundles setuptools 79.0.1 (PYSEC-2026-3447, GHSA-xmj3-9gf7-h52w; not a project dependency) — outside the code — run `pip install -U setuptools` in the venv.
- The app runs on the Werkzeug development server — noticed during Phase 3 — outside the approved plan; use a production WSGI server (gunicorn/waitress) to deploy.
