# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install                                  # Node.js e npm (testado com Node 26.13.0)
[ -f .env ] || cp .env.example .env          # só na primeira vez; preencha ADMIN_TOKEN e SEED_USER_PASSWORD
set -a; source .env; set +a                  # carrega o .env no terminal (o app não lê o arquivo sozinho)
npm start                                    # sobe em http://localhost:3000
```

Gere um `ADMIN_TOKEN` forte com: `node -e "console.log(require('crypto').randomBytes(24).toString('hex'))"`

A aplicação sobe em `http://localhost:3000` (ou na porta de `PORT`). Por padrão o banco SQLite é em memória
(`DB_FILE=:memory:`) e é semeado automaticamente no boot; com `DB_FILE=<arquivo>` ele usa um arquivo e só
semeia se estiver vazio.

Variáveis de ambiente (todas listadas, sem valores reais, em `.env.example`):

| Variável | Uso |
|---|---|
| `PORT` | Porta HTTP (padrão `3000`) |
| `LOG_LEVEL` | `debug`, `info`, `warn` ou `error` (padrão `info`) |
| `DB_FILE` | `:memory:` (padrão) ou caminho de um arquivo SQLite |
| `ADMIN_TOKEN` | Token exigido no header `X-Admin-Token` das rotas administrativas; vazio = elas respondem `401` |
| `SEED_USER_PASSWORD` | Senha do usuário semente `leonan@fullcycle.com.br`; vazio = senha aleatória, nunca exibida |
| `PAYMENT_GATEWAY_KEY` | Chave do gateway de pagamento; vazia = o log de pagamento indica "gateway sem chave configurada" |

Acesso por rota:

| Endpoint | Acesso |
|---|---|
| `POST /api/checkout` | Público para e-mail novo; para e-mail já cadastrado, `pwd` precisa ser a senha da conta (senão `401`) |
| `GET /api/admin/financial-report` | Admin (`X-Admin-Token`); `?limit=1..100&offset=N` opcionais |
| `DELETE /api/users/:id` | Admin (`X-Admin-Token`) |
| `GET /api/users/:id/export` | Admin (`X-Admin-Token`) |

Exemplos de requisições estão em `ecommerce-api-legacy-api-curls.http` (preencha `@admin_token` e `@seed_user_password`
com os mesmos valores de `ADMIN_TOKEN` e `SEED_USER_PASSWORD`).

### Testar com SQLite (passo a passo)

Usa um arquivo SQLite temporário. Assim o `api-test.sh` consegue fazer as checagens no banco (`check_db`) e no log (`APP_LOG`).

```bash
cd ecommerce-api-legacy

[ -f .env ] || cp .env.example .env                  # só na primeira vez; preencha ADMIN_TOKEN e SEED_USER_PASSWORD
set -a; source .env; set +a                          # carrega o .env neste terminal
export DB_FILE="$(mktemp -d)/loja.sqlite"            # banco temporário (sobrescreve DB_FILE=:memory: do .env)
export TMP_DIR="$(dirname "$DB_FILE")"

npm start > "$TMP_DIR/app.log" 2>&1 &                # sobe a app gravando o log
sleep 3
grep "rodando na porta" "$TMP_DIR/app.log"           # Frankenstein LMS rodando na porta 3000...

APP_LOG="$TMP_DIR/app.log" ./api-test.sh             # testes de contrato
```

> **Atenção à ordem:** a app e o terminal só enxergam as variáveis do momento em que foram iniciados. Se
> você já tinha a app rodando, ou exportou variáveis antes de editar o `.env`, pare a app
> (`kill $(lsof -t -iTCP:3000 -sTCP:LISTEN)`) e repita o bloco inteiro, na ordem acima. Sem o `source .env`,
> a app sobe sem `ADMIN_TOKEN` e o `api-test.sh` mostra "ADMIN_TOKEN não informado".

Resultado esperado no fim: `TOTAL: 100 checks | failures: 0 | skipped: 0`.

Conferir o banco:

```bash
sqlite3 "$DB_FILE" "SELECT id, name, email FROM users;"        # Leonan (usuário semente)
sqlite3 "$DB_FILE" "SELECT id, title, price FROM courses;"     # Clean Architecture e Docker
```

Encerrar a aplicação e apagar o banco temporário:

```bash
kill $(lsof -t -iTCP:3000 -sTCP:LISTEN)
rm -rf "$TMP_DIR"
```

Pontos de atenção:

- `DB_FILE` precisa estar numa pasta temporária (`/var/folders`, `/tmp` ou `/private/tmp`). Fora dela, o `api-test.sh` recusa com "not isolated".
- Para começar do zero, use um `mktemp -d` novo. O seed só roda em banco vazio.
- Com `DB_FILE=:memory:`, as checagens de banco são puladas.
- Sem `.env`, exporte as variáveis antes: `export ADMIN_TOKEN=... SEED_USER_PASSWORD=...`.

## Conclusão da Fase 3

Saída do `completion-box.sh` da skill, que só emite a caixa quando `arch-check.sh` e o
log de validação passam. Log: [`evidence/logs/ecommerce-api-legacy-validation.txt`](../evidence/logs/ecommerce-api-legacy-validation.txt).

<!-- BEGIN:completion-box -->
```text
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
ecommerce-api-legacy/
├── .env.example
├── README.md
├── api-test.sh
├── api.http
├── package-lock.json
├── package.json
└── src/
    ├── app.js
    ├── config/
    │   └── index.js
    ├── controllers/
    │   ├── checkoutController.js
    │   ├── reportController.js
    │   └── userController.js
    ├── database/
    │   ├── connection.js
    │   └── schema.js
    ├── errors/
    │   ├── AppError.js
    │   └── errorHandler.js
    ├── middleware/
    │   └── requireAdmin.js
    ├── models/
    │   ├── auditLogModel.js
    │   ├── courseModel.js
    │   ├── enrollmentModel.js
    │   ├── paymentModel.js
    │   └── userModel.js
    ├── routes/
    │   ├── adminRoutes.js
    │   ├── checkoutRoutes.js
    │   └── userRoutes.js
    ├── services/
    │   ├── checkoutService.js
    │   ├── paymentGatewayService.js
    │   ├── reportService.js
    │   └── userService.js
    └── utils/
        ├── asyncHandler.js
        ├── logger.js
        └── password.js

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
```
<!-- END:completion-box -->

## Future improvements

- Limite de retenção de dados pessoais (AP-19) — left open in the plan — você escolheu adicionar apenas o endpoint de exportação; dados pessoais continuam guardados até a exclusão.
- Rotacionar a senha do banco e a chave `pk_live_` que estavam no código, e expurgar logs antigos com números de cartão completos — outside the code — remover do código não desfaz o vazamento.
- Sem bloqueio nem rate limit contra tentativa de senha no checkout de conta existente — accepted by the user — resíduo declarado da opção "401 unless pwd matches".
- Rotas admin protegidas por um único token compartilhado (`ADMIN_TOKEN`), sem identidade por administrador — accepted by the user — resíduo declarado da opção "Env admin token".
- Relatório financeiro ainda mostra nomes de alunos a administradores — accepted by the user — resíduo declarado da opção "Keep name, admin-only".
- `sqlite3` 6.x está marcado como não mantido; advisories futuros podem ficar sem correção — accepted by the user — resíduo declarado da opção "Upgrade to 6.0.1".
- `arch-check.sh` não detecta uma função de controller escrita em uma única linha que chama 2 models — noticed during Phase 3 — limitação do verificador (a forma multilinha é detectada), confirmada na anti-tautologia.
- Rajadas de checkout com senha errada saturam o threadpool do libuv (scrypt e sqlite3 dividem as mesmas 4 threads) e atrasam todas as consultas em ~0,5 s por rajada de 20 — noticed during Phase 3 — a fila de transações já não amplifica o efeito; mitigar com rate limit (ver item acima) ou `UV_THREADPOOL_SIZE` maior.
