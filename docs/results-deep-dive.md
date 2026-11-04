# Resultados — Rodada final

[← README](../README.md)

Uma seção por projeto com a rodada final: findings por severidade, o que a Fase 3 mudou e o que
ficou em aberto.

A skill foi construída em rodadas. Cada rodada anterior usou uma versão ainda incompleta da skill e
revelou falhas que viraram regras, anti-patterns ou checagens
([Desafios](skill-construction.md#desafios-e-como-a-skill-os-trata)). Os resultados dessas rodadas
não fazem parte desta entrega: relatórios e logs vêm da rodada final, executada uma vez em cada
projeto, com a skill já pronta.

| Projeto | Stack | CRITICAL | HIGH | MEDIUM | LOW | Total | Checks (`api-test.sh`) | Endpoints |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `code-smells-project` | Python 3.11.15 + Flask 3.1.1 | 8 | 3 | 7 | 4 | 22 | 173, 0 falhas | 21/21 |
| `ecommerce-api-legacy` | Node.js 26.13.0 + Express 4.22.1 | 7 | 3 | 5 | 4 | 19 | 100, 0 falhas | 4/4 |
| `task-manager-api` | Python 3.11.15 + Flask 3.0.0 | 7 | 3 | 8 | 4 | 22 | 217, 0 falhas | 22/22 |

Achados vêm dos relatórios; checks e endpoints, dos logs de validação.

## `code-smells-project`

### Resultados

**Findings** ([`reports/audit-project-1.md`](../reports/audit-project-1.md)) — Python 3.11.15 + Flask 3.1.1,
4 arquivos, ~780 linhas: **8 CRITICAL · 3 HIGH · 7 MEDIUM · 4 LOW = 22**.

Os CRITICAL: SQL injection em todas as funções de acesso a dados, o endpoint `POST /admin/query` que
executa SQL do cliente, segredos hardcoded com debug ligado e ecoados no `/health`, senhas em texto
plano, o campo de senha serializado nas respostas, dados pessoais de outros usuários para anônimos,
nenhuma autenticação em rota alguma e SQL cru no código de roteamento.

**O que a Fase 3 mudou**
- `app.py`/`controllers.py`/`models.py`/`database.py` divididos em `routes/`, `controllers/`,
  `services/`, `models/`, `database/`, `config/`, `errors/`, `middleware/` e `utils/`; `app.py`
  ficou só como raiz de composição.
- Todas as consultas parametrizadas; uma conexão SQLite por requisição no lugar da conexão global.
- Segredos, debug e senhas do seed lidos do ambiente (`.env.example`); o `/health` não expõe mais a
  configuração.
- Senhas com hash (Werkzeug), linhas em texto plano migradas no boot; senha nunca serializada;
  e-mail de outros usuários mascarado.
- Token bearer assinado no login e regra de acesso por rota (público / dono-ou-admin / admin);
  `/admin/query` desligado atrás de `ADMIN_QUERY_ENABLED`.
- Validação na borda com 400/404 tipados e tratador central de erros com 500 genérico; um único
  validador de produto para criação e atualização.
- Caso de uso do pedido num Service, em uma transação e com baixa de estoque atômica; N+1 removido;
  paginação opcional.
- Endpoints de exclusão (desvincula pedidos) e de exportação dos dados do usuário.
- Flask 3.1.3, flask-cors 6.0.5, werkzeug e itsdangerous fixados; `.python-version` 3.11.18.

**Validação** ([log](../evidence/logs/code-smells-project-validation.txt)): 173 checks, 0 falhas,
0 pulados, 21/21 endpoints, `api-test.sh` exit 0; `arch-check.sh` PASS; caixa de conclusão da Fase 3 gerada
([README do projeto](../code-smells-project/README.md#conclusão-da-fase-3)).

**Em aberto**: limite de retenção de dados pessoais (decisão deixada em aberto na Fase 2), rotação dos
segredos e senhas que estavam no código (fora do código), resíduos aceitos (tokens sem revogação,
`/admin/query` ainda total quando habilitado, listas sem `page` devolvendo a tabela inteira, dados
inválidos já gravados) e itens notados na Fase 3 fora do plano (status de pedido inexistente
responde 200, cancelamento não devolve estoque, e-mail sem `UNIQUE`, login sem rate limit, CORS
aberto, servidor de desenvolvimento). Lista completa, com a origem de cada item:
[`code-smells-project/README.md`](../code-smells-project/README.md#future-improvements).

## `ecommerce-api-legacy`

### Resultados

**Findings** ([`reports/audit-project-2.md`](../reports/audit-project-2.md)) —
JavaScript (Node.js 26.13.0) + Express 4.22.1, 3 arquivos, ~180 linhas:
**7 CRITICAL · 3 HIGH · 5 MEDIUM · 4 LOW = 19**.

Os CRITICAL: credenciais e chave de pagamento `pk_live_` no código, "hash" de senha em base64
truncado, número completo do cartão e chave do gateway no log, rotas admin e de exclusão sem
autenticação, nomes de alunos no relatório financeiro para anônimos, a God Class `AppManager` e o
`express@4.22.1` com um advisory de queda do processo sem autenticação.

**O que a Fase 3 mudou**
- `AppManager` e `utils.js` divididos em `src/routes/`, `controllers/`, `services/`, `models/`,
  `database/`, `config/`, `errors/`, `middleware/` e `utils/`; `src/app.js` ficou só como raiz de
  composição.
- Segredos, porta e senha do seed lidos do ambiente (`.env.example`); nenhuma credencial ou chave
  literal no código.
- `crypto.scrypt` com salt no lugar do `badCrypto`.
- Rotas admin protegidas por `X-Admin-Token` (`ADMIN_TOKEN`, fecha por padrão); checkout em e-mail
  já cadastrado exige a senha da conta.
- Cartão e chave do gateway fora do log (só os 4 últimos dígitos, mascarados); logger com níveis no
  lugar do `console.log`.
- Validação estrita do checkout (400) e tratador central de erros; um cartão numérico não derruba
  mais o processo.
- Checkout num Service com uma transação; relatório com `JOIN` (sem N+1) e `limit`/`offset` opcionais.
- Exclusão de usuário desvincula matrículas, mantém pagamentos, anonimiza o audit log e responde 404
  para id desconhecido; novo `GET /api/users/:id/export` (admin).
- Cache global e contador de receita morto removidos.
- express 4.22.1 → 4.22.3 e sqlite3 5.1.7 → 6.0.1 (`npm audit` limpo).

**Correções da revisão de segurança pós-Fase 3** (mesma rodada):
- Checkouts simultâneos com o mesmo e-mail novo podiam criar duas contas: a busca da conta, a
  checagem de senha, a decisão de pagamento e os inserts passaram a rodar numa transação
  serializada, e `users.email` ganhou índice `UNIQUE`.
- Essa transação serializada passou a segurar o `scrypt`, e uma rajada de checkouts com senha
  errada travava a fila: a senha agora é verificada/derivada antes da transação, que só relê a conta
  e tenta de novo (até 3 vezes) se ela mudou. O `api-test.sh` cobre os dois casos.

**Validação** ([log](../evidence/logs/ecommerce-api-legacy-validation.txt)): 100 checks, 0 falhas,
0 pulados, 4/4 endpoints, `api-test.sh` exit 0; `arch-check.sh` PASS; caixa de conclusão da Fase 3 gerada
([README do projeto](../ecommerce-api-legacy/README.md#conclusão-da-fase-3)).

**Em aberto**: limite de retenção de dados pessoais, rotação da senha do banco e da chave `pk_live_`, expurgo dos logs antigos com cartão (fora do código) e resíduos aceitos (sem rate limit no checkout de conta existente, um único token admin compartilhado, nomes de alunos no relatório para admins, `sqlite3` 6.x sem manutenção). Lista completa:
[`ecommerce-api-legacy/README.md`](../ecommerce-api-legacy/README.md#future-improvements).

## `task-manager-api`

### Resultados

**Findings** ([`reports/audit-project-3.md`](../reports/audit-project-3.md)) — Python 3.11.15 + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1, SQLite), 15 arquivos, ~1160 linhas:
**7 CRITICAL · 3 HIGH · 8 MEDIUM · 4 LOW = 22**.

Os CRITICAL: `SECRET_KEY`, senha SMTP e senhas do seed literais com debug em `0.0.0.0`, MD5 sem salt,
hash de senha em toda resposta de usuário (inclusive no login), nenhuma autenticação em rota alguma (o
login emitia um token forjável que nada conferia), nomes e e-mails de outros para anônimos,
`flask-cors` 4.0.0 enviando `Access-Control-Allow-Private-Network: true` e exceções com hash e e-mail
escritas no log.
Os HIGH são o padrão deste projeto: pastas `models/routes/services` já existiam, mas a persistência
e a regra de negócio estavam nas rotas, sem camada de controller, e a regra de atraso, a
serialização e as estatísticas estavam copiadas entre handlers.

**O que a Fase 3 mudou**
- Camadas `controllers/`, `services/`, `config/`, `database/`, `errors/` e `middleware/`; as rotas só
  ligam caminhos a controllers.
- Token bearer assinado e com expiração, com regra de acesso por rota; `role`/`active` graváveis só
  por admin.
- Hash de senha com salt (Werkzeug), com o MD5 legado convertido no próximo login; hash fora das
  respostas; e-mail de outros usuários mascarado.
- Segredos, debug e senhas do seed lidos do ambiente.
- Flask 3.1.3 e flask-cors 6.0.5; pins sem uso removidos (marshmallow, requests); Python 3.11.18
  fixado; `Query.get()` deprecated trocado por `db.session.get` (16 → 0).
- Validação de entrada respondendo 400, tratamento central de erros, log sem dado pessoal,
  paginação opcional e N+1 removido.

**Correções da revisão de segurança pós-Fase 3** (mesma rodada):
- O token passou a carregar uma impressão digital da conta (id, criação, hash da senha): ele é
  recusado depois que a conta é excluída e o id reaproveitado, ou depois de uma troca de senha.
- Só admin cria task para outro usuário ou troca o responsável; usuário comum recebe 403. O
  `api-test.sh` cobre os dois casos.

**Validação** ([log](../evidence/logs/task-manager-api-validation.txt)): 217 checks, 0 falhas,
0 pulados, 22/22 endpoints, `api-test.sh` exit 0; `arch-check.sh` PASS; caixa de conclusão da Fase 3 gerada
([README do projeto](../task-manager-api/README.md#conclusão-da-fase-3)).

**Em aberto**: limite de retenção de dados pessoais (decisão deixada em aberto na Fase 2), rotação dos
segredos e expurgo dos logs antigos com hash e e-mail (fora do código), resíduos aceitos (token
roubado válido até expirar, MD5 legado em contas que não voltam a logar, listas sem `page`
devolvendo a tabela inteira, qualquer usuário logado vê todas as tasks e o nome do responsável,
dados inválidos já gravados) e itens notados na Fase 3 (login sem rate limit, CORS aberto,
`datetime.utcnow()` deprecated a partir do Python 3.12, setuptools do `.venv` com advisory,
servidor de desenvolvimento). Lista completa:
[`task-manager-api/README.md`](../task-manager-api/README.md#future-improvements).
