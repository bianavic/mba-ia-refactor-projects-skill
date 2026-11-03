# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
ADMIN_TOKEN=<token-admin> SEED_USER_PASSWORD=<senha-do-seed> npm start
```

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
| `PAYMENT_GATEWAY_KEY`, `DB_USER`, `DB_PASSWORD`, `SMTP_USER` | Credenciais de integrações, apenas pelo ambiente |

Acesso por rota:

| Endpoint | Acesso |
|---|---|
| `POST /api/checkout` | Público para e-mail novo; para e-mail já cadastrado, `pwd` precisa ser a senha da conta (senão `401`) |
| `GET /api/admin/financial-report` | Admin (`X-Admin-Token`); `?limit=1..100&offset=N` opcionais |
| `DELETE /api/users/:id` | Admin (`X-Admin-Token`) |
| `GET /api/users/:id/export` | Admin (`X-Admin-Token`) |

Exemplos de requisições estão em `api.http` (defina `@adminToken` com o mesmo valor de `ADMIN_TOKEN`).

Testes de contrato (com a aplicação rodando):

```bash
ADMIN_TOKEN=<token-admin> SEED_USER_PASSWORD=<senha-do-seed> ./api-test.sh
```

Para as verificações no banco (`check_db`), suba e rode com o mesmo `DB_FILE` apontando para um arquivo
em um diretório temporário (`mktemp -d`); `APP_LOG=<arquivo de log do app>` habilita as checagens de log.

## Future improvements

- Limite de retenção de dados pessoais (AP-19) — left open in the plan — você escolheu adicionar apenas o endpoint de exportação; dados pessoais continuam guardados até a exclusão.
- Rotacionar a senha do banco e a chave `pk_live_` que estavam no código, e expurgar logs antigos com números de cartão completos — outside the code — remover do código não desfaz o vazamento.
- Sem bloqueio nem rate limit contra tentativa de senha no checkout de conta existente — accepted by the user — resíduo declarado da opção "401 unless pwd matches".
- Rotas admin protegidas por um único token compartilhado (`ADMIN_TOKEN`), sem identidade por administrador — accepted by the user — resíduo declarado da opção "Env admin token".
- Relatório financeiro ainda mostra nomes de alunos a administradores — accepted by the user — resíduo declarado da opção "Keep name, admin-only".
- `sqlite3` 6.x está marcado como não mantido; advisories futuros podem ficar sem correção — accepted by the user — resíduo declarado da opção "Upgrade to 6.0.1".
- `arch-check.sh` não detecta uma função de controller escrita em uma única linha que chama 2 models — noticed during Phase 3 — limitação do verificador (a forma multilinha é detectada), confirmada na anti-tautologia.
- Rajadas de checkout com senha errada saturam o threadpool do libuv (scrypt e sqlite3 dividem as mesmas 4 threads) e atrasam todas as consultas em ~0,5 s por rajada de 20 — noticed during Phase 3 — a fila de transações já não amplifica o efeito; mitigar com rate limit (ver item acima) ou `UV_THREADPOOL_SIZE` maior.
