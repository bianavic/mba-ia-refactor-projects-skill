# Resultados — Deep Dive

[← README](../README.md) · [Análise Manual](manual-analysis.md) · [Design da Skill](skill-design.md) · [Estrutura Final](project-structure.md) · [Evolução do Uso de IA](ai-evolution.md) · [Enunciado Original](challenge-original.md)

Narrativa rodada a rodada por trás da tabela de [§3.1](../README.md#31-resumo-das-auditorias)
e do checklist de [§3.3](../README.md#33-checklist-de-validação-preenchido) do README.
Uma seção por projeto; dentro de cada uma, uma subseção por rodada, mais antiga primeiro —
nunca removida quando uma rodada nova é adicionada, porque é a evidência do estado "antes".

## Resultados por Projeto

### code-smells-project

**Rodada 1 — [`audit-project-1.md`](../reports/audit-project-1.md).**
13 findings (4 CRITICAL, 3 HIGH, 2 MEDIUM, 4 LOW) sobre o boilerplate original de 4 arquivos
(`app.py`, `controllers.py`, `database.py`, `models.py`, ~780 linhas). A Fase 3 reestruturou o
projeto em `config/`, `controllers/`, `models/`, `routes/`, `middlewares/`, `utils/`; parametrizou
todas as queries; moveu `SECRET_KEY`/`DEBUG`/`DB_PATH`/host/porta para `config/settings.py`; parou
de vazar `senha` e passou a hashear com `werkzeug.security`; e substituiu `print` por `logging`.

**Rodada 2 — [`audit-project-1-part2.md`](../reports/audit-project-1-part2.md).** Re-auditoria
pós-Fase 3: todos os CRITICAL menos um foram confirmados resolvidos. Ficaram abertos, reaparecendo
parcialmente corrigidos:
- `POST /admin/query` ganhou autenticação (`requer_admin`), mas continuava executando SQL cru
  vindo do cliente sem parametrização — rebaixado de "não autenticado" para "autenticado mas ainda
  cru", carregado como o novo CRITICAL desta rodada.
- `admin_controller.py` chamava `models.db.get_db()` e cursor diretamente, quebrando a convenção
  Controller→Model que todo o resto do projeto já seguia (novo HIGH).
- Parsing de paginação duplicado em três controllers (novo HIGH).
- N+1 ao criar pedido e busca de produtos sem paginação (2 novos MEDIUM).
- Faixas de desconto do relatório de vendas hardcoded (novo LOW).

Total: 7 findings (1 CRITICAL, 2 HIGH, 2 MEDIUM, 2 LOW). Fase 3 não foi reexecutada
imediatamente após esta rodada — os achados ficaram pendentes até a rodada 3.

**Rodada 3 — [`audit-project-1-part3.md`](../reports/audit-project-1-part3.md), 2026-09-19.**
Antes de auditar de novo, confirmamos que os HIGH e MEDIUM da rodada 2 já haviam sido corrigidos
entre as duas rodadas: `models/admin_model.py` passou a existir e `admin_controller.py` já só o
chamava (fechando o HIGH de bypass de camada); `utils/pagination.py` com `parse_pagination()` já
existia e já era usado pelos três controllers (fechando a duplicação); `order_model.criar()` já
buscava os produtos em um único `WHERE id IN (...)` antes do loop (fechando o N+1); `product_model.buscar()`
já paginava (fechando a paginação ausente); e os descontos já estavam em
`FAIXAS_DESCONTO_FATURAMENTO` em `config/settings.py` (fechando o LOW). A auditoria desta rodada
buscou o que sobrava e o que apareceu de novo:
- **[CRITICAL] admin ainda executava SQL sem parametrização.** `executar_query()` já filtrava para
  aceitar só instruções `SELECT`, mas ainda executava a string do cliente direto em
  `cursor.execute(query)` — um token de admin válido ainda conseguia rodar `SELECT senha FROM usuarios`
  ou ler `sqlite_master`. Achado carregado da rodada 2, nunca de fato resolvido até aqui.
- **[LOW] `id` sombreando builtin do Python** — corrigido em `product_controller`/rotas de produto,
  mas ainda presente em `user_controller.buscar_por_id(id)` e na rota `/usuarios/<int:id>`, um local
  que a rodada 2 não tinha coberto.
- **[MEDIUM] `GET /pedidos/usuario/<id>` sem paginação** — histórico de pedidos por usuário nunca
  tinha sido citado nas rodadas anteriores; `/pedidos` (listagem geral) já paginava, este não.
- **[MEDIUM] validação de campos obrigatórios duplicada** entre `criar` e `atualizar` em
  `product_controller.py` — mesmo bloco copiado duas vezes no mesmo arquivo.
- **[LOW] limites de tamanho do nome do produto hardcoded** em `product_model._validar_campos`
  (`2`/`200`), mesmo padrão já resolvido para categorias e faixas de desconto no mesmo arquivo/projeto.

Total: 5 findings (1 CRITICAL, 0 HIGH, 2 MEDIUM, 2 LOW) — usuário confirmou Fase 3.

**Fase 3 desta rodada** (resumo; ver histórico de commits para o diff completo):
- `models/admin_model.py`: SQL cru trocado por `CONTAGENS_POR_TABELA`, um dict de queries
  parametrizadas fixas indexado pelo nome da tabela — nenhuma string vinda do cliente chega a
  `cursor.execute` nunca mais. `admin_controller.py` e `manual-tests.sh` atualizados para o novo
  contrato (`{"tabela": "..."}` em vez de `{"sql": "..."}`).
- `models/order_model.get_por_usuario` + `controllers/order_controller.listar_por_usuario`: agora
  aceitam `page`/`per_page` via `parse_pagination()` e aplicam `LIMIT ? OFFSET ?`.
- `controllers/product_controller.py`: `_validar_campos_obrigatorios()` extraído e chamado por
  `criar` e `atualizar`.
- `controllers/user_controller.py` + `routes/routes.py`: `buscar_por_id(id)` → `buscar_por_id(usuario_id)`,
  rota `/usuarios/<int:id>` → `/usuarios/<int:usuario_id>`.
- `config/settings.py` + `models/product_model.py`: `NOME_PRODUTO_MIN_LEN`/`NOME_PRODUTO_MAX_LEN`
  centralizados.

**Validação real desta rodada:** log completo em
[`evidence/logs/code-smells-project-round3-validation.txt`](../evidence/logs/code-smells-project-round3-validation.txt)
(646 linhas) — boot da aplicação, `arch-check.sh` (`PASS`, 2 arquivos de rota, 0 chamadas inline),
um `curl` por finding corrigido e a suíte `manual-tests.sh` completa. Destaques registrados ali:
`/admin/query` responde à allow-list e rejeita com 400 tanto `sqlite_master` quanto a tentativa de
injeção `usuarios; DROP TABLE usuarios;--`; `/pedidos/usuario/2` devolve pedidos diferentes em
`page=1` e `page=2` com `per_page=1` (paginação real, não truncamento); `criar` e `atualizar`
devolvem a mesma mensagem de campo obrigatório (helper compartilhado); e o nome de 1 caractere é
barrado pelos limites agora vindos de `config/settings.py`.

**Rodada 4 — [`audit-project-1-part4.md`](../reports/audit-project-1-part4.md), 2026-09-20.**
Re-auditoria manual e pontual, não uma passada completa Fase 1-3 — disparada ao escrever
`code-smells-project/api-tests.http` (cobertura manual de todos os endpoints) e cair em dois bugs
de comportamento que as seções de edge case/sad path desse arquivo foram desenhadas pra pegar.
Nenhum dos dois estava em `manual-tests.sh` nem em nenhum relatório anterior; não questiona nem
contradiz a rodada 3 (commit `83bfaa3`) ou sua validação — são achados novos em código que a
rodada 3 não tocou:

- **[HIGH] `PUT /pedidos/<id>/status` reporta sucesso para pedido inexistente.**
  `models/order_model.atualizar_status` roda o `UPDATE` e sempre retorna `True`, sem checar
  `cursor.rowcount`; o controller sempre responde 200 `"sucesso": true`, mesmo quando nenhuma
  linha foi afetada. Mesma classe de bug do HIGH "Cascade delete swallows errors" da rodada 3 de
  `ecommerce-api-legacy` — mutação que nunca confere se mutou algo de fato.
- **[MEDIUM] parâmetro não numérico em paginação/filtro derruba pra 500 em vez de 400.**
  `utils/pagination.parse_pagination()` (`int(...)` sem `try/except`) e o `float(preco_min)`/
  `float(preco_max)` de `product_controller.buscar` deixam `?page=abc` ou `?preco_min=abc`
  virarem `ValueError`, capturado pelo `except Exception` genérico de cada handler e devolvido
  como 500 com a mensagem crua da exceção Python no corpo — afeta os 5 endpoints paginados/
  filtráveis do projeto (produtos, produtos/busca, pedidos, pedidos/usuário, usuários).

Total: 2 findings (1 HIGH, 1 MEDIUM) — abaixo do mínimo de 5, mesma justificativa da rodada 4 de
`ecommerce-api-legacy`: é re-auditoria pontual sobre dois bugs específicos, não uma passada
completa, e o template proíbe inventar finding pra preencher vaga.

Nenhum AP-xx do catálogo atual cobre exatamente nenhum dos dois (mutação sem checar linha
afetada; coerção de tipo sem guard virando 500) — o relatório propõe candidatos a AP-18/AP-19,
mas não os adiciona ao catálogo nesta rodada, mesma decisão tomada para o AP-17 antes de ele ser
formalizado.

**Fase 3 desta rodada:** `models/order_model.atualizar_status` agora retorna
`cursor.rowcount > 0`; `order_controller.atualizar_status` responde 404 quando nada foi afetado
(fecha o HIGH). `utils/pagination.parse_pagination()` ganhou `try/except (TypeError, ValueError)`
em torno dos dois `int()`, levantando um `ValueError` com mensagem clara; `product_controller.buscar`
guarda os dois `float()` (`preco_min`/`preco_max`) da mesma forma. Os 5 call sites de
`parse_pagination()` (`product_controller.listar`/`buscar`, `order_controller.listar_todos`/
`listar_por_usuario`, `user_controller.listar`) ganharam `except ValueError as e: ..., 400` antes
do `except Exception` genérico que antes convertia o `ValueError` em 500 (fecha o MEDIUM).

**Validação real desta rodada:** log completo em
[`evidence/logs/code-smells-project-round4-validation.txt`](../evidence/logs/code-smells-project-round4-validation.txt) —
boot, `arch-check.sh` (exit 0), `manual-tests.sh` inteiro sem regressão, e verificação dirigida
dos dois achados: `PUT /pedidos/99999/status` agora 404 (era 200 falso) com controle positivo em
`PUT /pedidos/1/status` (continua 200); `GET /produtos?page=abc` e
`GET /produtos/busca?preco_min=abc` agora 400 (eram 500) com dois controles negativos em outros
controllers (`/usuarios?page=abc`, `/pedidos/usuario/2?per_page=abc`, mesma raiz do bug) e um
controle positivo (`/produtos?page=1&per_page=5` continua 200).

### ecommerce-api-legacy

**Rodada 1 — [`audit-project-2.md`](../reports/audit-project-2.md).**
12 findings (4 CRITICAL, 2 HIGH, 2 MEDIUM, 4 LOW) sobre o boilerplate de 3 arquivos
(`app.js`, `AppManager.js`, `utils.js`, ~180 linhas). Os 4 CRITICAL eram a classe-Deus
`AppManager` (schema, rotas e regra de negócio no mesmo arquivo), segredos literais em
`utils.js` — incluindo uma chave `pk_live_` de gateway de pagamento —, um "hash" de senha
que era base64 repetido e truncado em 10 caracteres, e o número do cartão escrito em log
em texto plano junto da chave do gateway. A Fase 3 quebrou o `AppManager` em `controllers/`,
`models/`, `services/`, `routes/`, `middlewares/` e `utils/`; moveu os segredos para
`config/index.js` lendo `process.env`; trocou o base64 por `crypto.scryptSync` com salt por
usuário; passou a mascarar o cartão antes de logar; deu cascade ao delete de usuário; e
trocou o N+1 do relatório financeiro por uma query batched com `WHERE course_id IN (...)`.

**Rodada 2 — [`audit-project-2-part2.md`](../reports/audit-project-2-part2.md).**
Re-auditoria pós-Fase 3: 8 findings (1 CRITICAL, 2 HIGH, 2 MEDIUM, 3 LOW). Confirmou
resolvidos os 4 CRITICAL, o delete sem cascade, o N+1 e o log via `console.log`. O CRITICAL
desta rodada foi uma reclassificação: a senha fallback `'123456'` (antes LOW/AP-13) passou a
AP-02, por ser credencial hardcoded que provisiona conta real.
**Esta rodada parou no gate da Fase 2 — não houve Fase 3.** O relatório termina na pergunta
de confirmação sem resposta registrada, e `git log -- ecommerce-api-legacy` não tem commit de
refatoração depois dele (o último é `f5c6fca`, a Fase 3 da rodada 1). Os 8 findings ficaram
abertos por inteiro.

**Rodada 3 — [`audit-project-2-part3.md`](../reports/audit-project-2-part3.md) (2026-09-20).**
16 findings (1 CRITICAL, 5 HIGH, 5 MEDIUM, 5 LOW): os 8 herdados da rodada 2, re-verificados
linha a linha e todos ainda abertos, mais 8 novos que as duas passagens anteriores não tinham
alcançado. Os novos vieram de quatro frentes que só aparecem depois que a estrutura já existe:

- **Integridade transacional** — o checkout cobrava o cartão e só então gravava matrícula e
  pagamento, em três escritas sequenciais sem transação nem compensação. Uma falha no meio
  deixava cliente cobrado sem matrícula, sem linha em `payments` para reconciliar.
- **Fronteira controller/service** — a Fase 3 da rodada 1 criou `controllers/` e `models/`, mas
  nenhum service de domínio: o `checkoutController` orquestrava cinco models e o
  `reportController` calculava a regra de receita ("só soma pagamento `PAID`") dentro do handler.
- **Erro engolido no model** — `deleteCascade` passava callback de erro só na última das três
  statements; falha parcial resolvia como sucesso. E, sem checar `this.changes`, apagar um id
  inexistente respondia 200 afirmando ter removido registros.
- **Bootstrap e validação** — `app.js` chamava `listen()` no import (impossível importar a app
  num teste sem abrir porta) e nenhuma rota validava entrada (`card` numérico chegava a
  `cardNumber.slice()` e estourava TypeError dentro de handler async sem guarda).

A Fase 3 resolveu 13 dos 16. Criou `services/checkoutService.js` (com `withTransaction` e
registro de `ESTORNO PENDENTE` em `audit_log` quando a escrita falha depois da cobrança),
`services/reportService.js`, `services/userService.js`, `errors/AppError.js` com o adaptador
`failWith()` que substitui os nove try/catch dos controllers, `middlewares/validators.js`,
`middlewares/asyncHandler.js` (o Express 4 não encaminha promise rejeitada de handler async —
era isso que travava a requisição no `await auditLogModel.create(...)` desguardado),
`middlewares/notFoundHandler.js` e `src/server.js` separado do `src/app.js`. Removeu o
`cacheService` (write-only: `get` não era chamado em lugar nenhum) e os campos mortos
`dbUser`/`dbPass`/`smtpUser` do config.

Ficaram abertos de propósito, por limite de escopo do RP-15 (são contrato da API, não código
interno): os dois LOW de convenção — nomes abreviados no corpo do request (`usr`, `eml`, `pwd`,
`c_id`, `card`), mensagens de erro em português, corpos ora texto ora JSON, e `enrollment_id`
em snake_case. Documentados, não renomeados.

Um terceiro foi resolvido por remoção em vez de integração: `verifyPassword` estava
inalcançável (não existe rota de autenticação no projeto) e criar uma seria mudança de feature.
Seguindo o RP-10, a função foi apagada — o histórico do git a preserva.

**Uma mudança de comportamento intencional**, que era o defeito relatado e não regressão:
`DELETE /api/users/<id inexistente>` agora responde 404 em vez de 200 afirmando ter apagado.
O rótulo desse caso no `manual-tests.sh` foi atualizado para "esperado 404".

Validação completa da rodada em
[`evidence/logs/ecommerce-api-legacy-round3-validation.txt`](../evidence/logs/ecommerce-api-legacy-round3-validation.txt):
boot, `arch-check.sh` (exit 0) com o detector validado antes contra uma violação plantada de
propósito, `manual-tests.sh` inteiro, log do servidor mostrando o cartão mascarado, e um `curl`
por finding corrigido. Os probes de caixa-branca da rodada foram consolidados em
`ecommerce-api-legacy/internal-tests.js` (`npm run test:internal`) e ficam no repositório —
cobrem o rollback da transação com controle negativo, a app importável sem abrir porta e o teto
de `per_page`, que são propriedades que nenhuma resposta HTTP revela. A porta 3000 estava
ocupada pelo Docker na máquina, então a validação rodou em `PORT=3100`; `manual-tests.sh` passou
a aceitar `BASE` do ambiente por causa disso.

**Rodada 4 — [`audit-project-2-part4.md`](../reports/audit-project-2-part4.md), 2026-09-20.**
Re-auditoria manual e pontual, não uma passada completa Fase 1-3 — disparada ao escrever
`ecommerce-api-legacy/api-tests.http` (testes manuais de endpoint/DB) e notar que o projeto não
tem nenhuma camada de autenticação, uma lacuna que nenhuma das três rodadas anteriores tinha
levantado. Antes de registrar o achado, os 16 findings de `-part3.md` foram reverificados um a
um contra o código atual, porque `git log -- ecommerce-api-legacy` mostra um commit de refatoração
(`4ddb14e refactor(ecommerce-api-legacy): resolve round-3 findings and add internal checks`)
depois de `-part3.md` sem nenhum relatório de auditoria confirmando o que ele corrigiu.

14 dos 16 achados da rodada 3 estão resolvidos (fallback de senha removido, checkout em
transação, lógica de negócio em `services/`, tratamento de erro centralizado em `asyncHandler`/
`AppError`, cascade delete transacional, cache write-only removido, camada de validação,
paginação com teto, `verifyPassword` morto removido, `app.js` sem side effect de boot, config
morta limpa, default de paginação centralizado, contrato 404 para rota desconhecida, metadata do
`package.json` atualizada). Os 2 LOW de convenção (nomes abreviados de campo, formato de
resposta ora texto ora JSON) seguem abertos de propósito, quarta rodada consecutiva, por limite
de escopo do RP-15 (contrato de API, não código interno).

O achado novo: **[CRITICAL] nenhum endpoint tem autenticação ou autorização.**
`GET /api/admin/financial-report` expõe a receita completa por aluno para qualquer chamador não
autenticado; `DELETE /api/users/:id` apaga qualquer usuário (cascade para matrículas/pagamentos)
para quem conseguir adivinhar ou enumerar um id inteiro pequeno — nenhuma sessão, API key ou
token é checado em lugar nenhum (`grep -rni "auth\|token\|role\|permission\|credential" src/` não
acha nada). Nenhum AP-xx/RP-xx existente cobre exatamente "endpoint sem checagem de identidade do
chamador" — o relatório não força um encaixe em AP-02/AP-06 e propõe um AP-17 novo.

Total: 3 findings (1 CRITICAL novo, 2 LOW herdados) — abaixo do mínimo de 5 do enunciado para uma
primeira passada de Fase 2, mas o próprio template proíbe inventar finding para preencher vaga;
um projeto que já resolveu 14 dos 16 achados anteriores legitimamente sobra pouco a reportar além
do gap novo que motivou a rodada. Ver nota ⁶ em
[Checklist de Validação Preenchido](#checklist-de-validação-preenchido).

**Fase 3 desta rodada:** adicionado `src/middlewares/requireAdminToken.js` — guarda mínima por
API key (`X-Admin-Token`), não um sistema de contas completo (o projeto nunca teve login/sessão,
então inventar um seria decisão de produto, fora do escopo mecânico do RP-16). Sem `ADMIN_TOKEN`
configurado no servidor, as duas rotas ficam **desabilitadas** (403) em vez de abertas por
padrão — mesma convenção já usada e validada em `code-smells-project` (`middlewares/auth.py`).
Aplicada em `GET /api/admin/financial-report` e `DELETE /api/users/:id` via `src/routes/index.js`.
`manual-tests.sh` ganhou uma seção AUTH (sem token / token forjado -> 401) e passou a exigir
`ADMIN_TOKEN` no ambiente para exercitar o resto do fluxo com token válido; `api-tests.http`
ganhou `@adminToken` e o header nas ~15 chamadas às duas rotas, e sua seção "Limites de
permissão" foi reescrita para demonstrar a checagem em vez de documentar a ausência dela.

**Validação real desta rodada:** log completo em
[`evidence/logs/ecommerce-api-legacy-round4-validation.txt`](../evidence/logs/ecommerce-api-legacy-round4-validation.txt) —
boot com e sem `ADMIN_TOKEN` (confirma "desabilitado" vs. "autenticado", nunca "aberto"),
`arch-check.sh` (exit 0), `manual-tests.sh` inteiro sem regressão, `npm run test:internal` (4/4),
e verificação dirigida do CRITICAL: `Authorization: Bearer` forjado e ausência total de header
agora respondem 401 em ambas as rotas (antes respondiam 200 igual a uma chamada legítima), com
controle positivo (`X-Admin-Token` correto continua 200).

Achado colateral, registrado no relatório mas fora do formato da Fase 2: nem
`references/anti-patterns-catalog.md` nem `references/refactoring-playbook.md` (nas 3 cópias)
tem entrada para "ausência de autenticação/autorização" — é o motivo mecânico do gap ter
atravessado três rodadas sem ser pego. Próximo id livre: AP-17. `code-smells-project` e
`task-manager-api` nunca foram auditados especificamente para esse gap, então o mesmo pode
existir neles sem ter sido reportado ainda.

### task-manager-api

**Rodada 1 — [`audit-project-3.md`](../reports/audit-project-3.md).**
14 findings (4 CRITICAL, 2 HIGH, 4 MEDIUM, 4 LOW) sobre o projeto original de 15 arquivos
(~1158 linhas), que já tinha `models/`, `routes/`, `services/`, `utils/` mas ainda concentrava
lógica e persistência nas rotas. Os CRITICAL: `User.to_dict()` devolvia o hash da senha em
toda resposta; senha hasheada com MD5 sem sal; `SECRET_KEY` hardcoded + `debug=True` em
`0.0.0.0` + credenciais SMTP hardcoded em `services/notification_service.py`; e `POST /login`
devolvia `'fake-jwt-token-' + str(user.id)`, um token forjável por qualquer um. A Fase 3
corrigiu os 4 CRITICAL, extraiu `config/settings.py`, passou a usar `werkzeug.security` e
`itsdangerous`, e centralizou agregação/serialização no model.

**Rodada 2 — [`audit-project-3-part2.md`](../reports/audit-project-3-part2.md).** Re-auditoria
pós-Fase 3: os 4 CRITICAL confirmados resolvidos. Reapareceram, em locais novos:
- Rotas ainda chamando o ORM diretamente (`Task.query`, `User.query`, `Category.query`,
  `db.session.add/commit/delete`) em vez de delegar a um Controller/Service — novo HIGH.
- Validação de título/status/prioridade/due_date/tags duplicada entre `create_task` e
  `update_task`, e `update_category` sem o guard de corpo vazio que os demais endpoints já
  tinham — novo HIGH.
- N+1 em `get_users` (uma query por usuário) e em `delete_user` (um delete por task) — novo
  MEDIUM.
- `GET /categories` sem paginação (nota: a correção de 2026-09-19 no próprio relatório
  esclareceu que `GET /users` já paginava desde essa rodada — o achado original estava errado
  nesse ponto).
- `log_action` morto usando `print()`; defaults `'#000000'`/`3` duplicados em vez de reusar
  `DEFAULT_COLOR`/`DEFAULT_PRIORITY`; strings de usuário em português dentro de um código em
  inglês (deixado aberto de propósito, ver RP-15).

Total: 7 findings (0 CRITICAL, 2 HIGH, 2 MEDIUM, 3 LOW) — usuário confirmou Fase 3.

**Rodada 3 — [`audit-project-3-part3.md`](../reports/audit-project-3-part3.md), 2026-09-20.**
Antes de auditar de novo, confirmamos que os 2 HIGH e os 2 MEDIUM da rodada 2 já estavam
resolvidos: AP-16 fechado (nenhuma rota toca persistência, confirmado por `arch-check.sh`);
validação de task centralizada em `controllers/task_controller.py`
(`_validate_title/_validate_status/_validate_priority/_resolve_user/_resolve_category/_apply_due_date`);
`update_category` ganhou o guard de corpo vazio; N+1 de `get_users`/`delete_user` viraram
query agrupada / bulk delete; `GET /categories` pagina; `log_action` foi deletado; os defaults
passaram a vir de `DEFAULT_COLOR`/`DEFAULT_PRIORITY`. A auditoria desta rodada achou 3 HIGH, 4
MEDIUM e 4 LOW novos:
- **[HIGH] Sem application factory** — `app.py` era um módulo que criava o app, configurava
  CORS/DB e chamava `db.create_all()` em tempo de import; `tests/conftest.py` tinha um segundo
  Flask app duplicado só para não importar `app.py`.
- **[HIGH] Agregação de status implementada 3 vezes** — `Task.get_statistics`,
  `build_summary_report` e `build_user_report` cada um recontava os mesmos status por conta
  própria, já divergentes entre si e nenhum deles derivado de `VALID_STATUSES`.
- **[HIGH] Login emite um token que nada verifica** — `POST /login` assinava um token com
  `itsdangerous`, mas não existia nenhum `loads`/decorator/`before_request` que o lesse; toda
  escrita (`PUT`/`DELETE /users`, `POST`/`PUT`/`DELETE /tasks`, escrita em `/categories`) era
  anônima. Relatado, mas **não resolvido nesta Fase 3** — mudar isso significa novos 401s ou
  mudar o payload de login, o que a Fase 3 não tem autorização para decidir sozinha.
- MEDIUM: carregamento de tabela inteira em `is_overdue()`/loops Python para relatórios;
  `?priority=`/`?user_id=` sem coerção de tipo virando 500 em vez de 400; coleções aninhadas
  (`tasks` de um usuário, `overdue.tasks` do resumo) sem paginação; `CORS(app)` liberado para
  qualquer origem e a única config não vinda de `config/settings.py`.
- LOW: 4 helpers mortos + `User.is_admin` mal escrito; literais de status espalhados em vez de
  `VALID_STATUSES`; `requirements.txt` desalinhado com os imports reais; `get_user_tasks`
  montando a resposta apagando chaves de outro serializer.

Total: 11 findings (0 CRITICAL, 3 HIGH, 4 MEDIUM, 4 LOW) — usuário confirmou Fase 3.

**Fase 3 desta rodada** resolveu os 2 HIGH estruturais e todos os MEDIUM/LOW exceto o de
linguagem inconsistente (mantido de propósito, RP-15) e o de token — inicialmente também
deixado em aberto, pela mesma regra de "Fase 3 não muda comportamento observável sem decisão
explícita". O usuário determinou explicitamente que o finding do token fosse resolvido
nesta rodada, com o escopo: leituras (`GET`) continuam públicas; toda escrita exige
`Authorization: Bearer <token>`; `PUT`/`DELETE /users/<id>` exigem ser o próprio usuário ou
admin; `PUT`/`DELETE /tasks/<id>` exigem ser o dono da task ou admin; escrita em `/categories`
exige role `admin`/`manager`; cadastro anônimo só pode criar role `user`. Implementação:
`services/token_service.py` (emissão/leitura do token, dono único — nem controller nem
middleware o reimplementam), `services/authorization.py` (regras de dono/role, sem nenhum
acoplamento a Flask/HTTP) e `middlewares/auth.py` (o guard, que recarrega o usuário do banco
a cada request — uma conta apagada devolve 401 e uma inativa devolve 403, sem esperar o token
expirar). `SECRET_KEY` deixou de ter qualquer default: o boot aborta fora de
`FLASK_ENV=development`, que gera uma chave efêmera em memória (perdida a cada restart,
portanto inútil para forjar uma sessão persistente). Ver o adendo datado no corpo do
[relatório desta rodada](../reports/audit-project-3-part3.md) para o registro formal da
decisão.

**Validação real desta rodada:** dois logs —
[`evidence/logs/task-manager-api-round3-validation.txt`](../evidence/logs/task-manager-api-round3-validation.txt)
(649 linhas, estrutura MVC/AP-16 e os achados estruturais da rodada 3) e
[`evidence/logs/task-manager-api-round4-validation.txt`](../evidence/logs/task-manager-api-round4-validation.txt)
(auth/autorização). Destaques do segundo: boot aborta com `RuntimeError` claro quando
`SECRET_KEY` está ausente fora de dev; `FLASK_ENV=development` sobe com chave efêmera de 64
caracteres + warning; `manual-tests.sh` com casos negativos retornando 401/401/401/403/403/403
exatamente como desenhado; um token forjado com a string antiga `'dev-secret-change-in-production'`
recebe 401; token de usuário desativado recebe 403; token de usuário apagado recebe 401;
`arch-check.sh` (do projeto e o genérico da skill) sai 0; `python -m pytest` 67/67 passando
(40 originais + 27 novos de token/autorização/rotas).

## Bug Encontrado Após a Entrega

Referenciado em [§2 do README](../README.md#2-construção-da-skill) como o motivo de AP-16
("Persistência/ORM Chamada Direto na Rota") ter entrado no catálogo depois dos outros 15.

**O que aconteceu:** [`audit-project-3.md`](../reports/audit-project-3.md) (rodada 1) auditou
`task-manager-api` contra um catálogo de 15 anti-patterns — nenhum deles cobria "a rota chama
o ORM/persistência diretamente em vez de delegar a um Controller/Service". O projeto já tinha
`routes/`/`services/` como pastas, então a violação (rotas chamando `Task.query`,
`db.session.add/commit/delete` etc. diretamente) passou pela Fase 2 sem ser sinalizada, e a
Fase 3 da rodada 1 não a corrigiu — não porque fosse difícil, mas porque não havia regra no
catálogo que a nomeasse.

**Como foi descoberto:** a rodada 2 ([`audit-project-3-part2.md`](../reports/audit-project-3-part2.md))
reauditou o projeto já refatorado e achou o padrão de novo, agora como o novo finding [HIGH]
"Routes call the ORM directly instead of delegating to a Controller/Service" —
`routes/task_routes.py`, `routes/user_routes.py` e `routes/report_routes.py` inteiros
reimplementavam a chamada de persistência em vez de delegar. Ficou claro que o problema não era
específico dessa rodada: tinha atravessado a entrega original porque não estava catalogado, e
nenhum teste de endpoint (`manual-tests.sh`) o pega — um `curl` não distingue uma rota que
delega de uma que consulta o ORM direto, só o código-fonte revela isso.

**Correção:** o commit `c4d523d` (2026-09-18) adicionou o **AP-16** ao catálogo (16 entradas
no total), com sinal explícito de detecção mesmo quando a chamada aparece uma única vez ou
quando o projeto já tem pastas `services/`/`controllers/` usadas por outras rotas. O commit
`a6527c1` (2026-09-19) foi além: tornou a verificação **mecânica e agnóstica de stack** —
`scripts/arch-check.sh`, empacotado pela skill, detecta a linguagem, seleciona os arquivos de
rota e aplica os sinais de persistência corretos por stack (Python, JS/TS, Go, Java/Kotlin,
Ruby, PHP, C#), documentados em `references/verification-recipes.md`. Um Go real expôs mais um
ajuste necessário: lá persistência é função de pacote, não método de receiver, então o padrão
inicial (baseado em `Model.find(...)`) dava falso PASS numa rota cheia de violações — corrigido
no mesmo commit. Desde então, a Fase 3 do `SKILL.md` trata esse check como **obrigatório e
nunca substituível** por teste de endpoint (passo 6, "Static AP-16 audit").

**Confirmação em `task-manager-api`:** a rodada 3 ([`audit-project-3-part3.md`](../reports/audit-project-3-part3.md))
fechou o finding — nenhuma rota toca persistência, confirmado por `./arch-check.sh` (exit 0) —
ver [nota ² acima](#task-manager-api) e
[`evidence/logs/task-manager-api-round3-validation.txt`](../evidence/logs/task-manager-api-round3-validation.txt).

## Checklist de Validação Preenchido

Notas de rodapé referenciadas pela tabela da [§3.3 do README](../README.md#33-checklist-de-validação-preenchido):

¹ — nota de `ecommerce-api-legacy` (célula "Relatório segue o template"). Verificada na
rodada 3 (2026-09-20), lendo os três relatórios do projeto: os três seguem
`references/audit-report-template.md` — cabeçalho em caixa, linha `Stack:`/`Files:`, bloco
`## Summary` com a contagem por severidade, um bloco por finding com `File:`/`Description:`/
`Impact:`/`Recommendation:` citando AP-xx/RP-xx, ordenação CRITICAL → LOW, total e a pergunta
final literal do gate. As partes 2 e 3 acrescentam, como o template manda para re-execução, a
seção `## Resolved since ...` no topo, com o delta em relação à parte anterior.

² — nota de `task-manager-api` (célula "Estrutura de diretórios segue MVC"). O projeto já tinha
`models/`/`routes/`/`services/`/`utils/` desde o boilerplate original, mas as rotas chamavam o
ORM diretamente (finding [HIGH] AP-16 da [rodada 3](#task-manager-api)). Fechado nessa mesma
rodada: `routes/*.py` passaram a só parsear → chamar `controllers/`/`services/` → serializar,
confirmado mecanicamente por `arch-check.sh` (exit 0, tanto o específico do projeto quanto o
genérico da skill) — ver
[`evidence/logs/task-manager-api-round3-validation.txt`](../evidence/logs/task-manager-api-round3-validation.txt).

³ — nota de `task-manager-api` (célula "Controllers concentram o fluxo"). `controllers/task_controller.py`
e `controllers/user_controller.py` concentram parsing/validação/autorização e delegam
persistência ao model; recebem `actor` explícito (`SYSTEM` por padrão, `None` para chamador
HTTP anônimo) em vez de ler estado global, o que manteve os 40 testes de controller originais
passando sem alteração ao acrescentar autorização na rodada 4.

⁴ — nota de `task-manager-api` (célula "Error handling centralizado"). `middlewares/error_handler.py`
registra dois handlers globais via `register_error_handlers(app)`: um para `HTTPException`
(preserva código e mensagem) e um catch-all para exceção não tratada (loga e devolve 500
genérico) — nenhuma rota trata exceção por conta própria.

⁵ — **O achado de `admin_controller.py` que motivou a re-auditoria de `code-smells-project`.**
Entre a rodada 1 e a rodada 2, a Fase 3 corrigiu o vazamento de segredo e a injeção de SQL nas
rotas de negócio, mas manteve `POST /admin/query` executando SQL vindo do cliente. A rodada 2
achou isso de novo (agora autenticado, mas ainda cru) e recomendou removê-lo. A rodada 3 (2026-09-19)
finalmente fechou: `models/admin_model.py` não aceita mais SQL do cliente — só uma tabela de uma
allow-list fixa (`produtos`, `usuarios`, `pedidos`, `itens_pedido`), cada uma resolvendo para uma
query parametrizada hardcoded. Ver [rodada 3 de `code-smells-project`](#code-smells-project) acima.

⁶ — nota de `ecommerce-api-legacy` (célula "Mínimo de 5 findings" em §3.3). A rodada 4
([`audit-project-2-part4.md`](../reports/audit-project-2-part4.md), 2026-09-20) achou só 3
findings (1 CRITICAL novo + 2 LOW herdados) — abaixo do mínimo de 5. É uma re-auditoria manual e
pontual, não uma passada completa Fase 1-3, e o próprio template proíbe inventar finding para
preencher vaga: um projeto que já resolveu 14 dos 16 achados da rodada 3 legitimamente sobra
pouco a reportar além do gap novo. O mínimo de 5 continua demonstrado pela rodada 3 (16
findings, as 3 fases completas). **A Fase 3 desta rodada já rodou**: o CRITICAL (ausência de
autenticação/autorização) foi corrigido com `requireAdminToken` e validado com a aplicação de pé
em
[`evidence/logs/ecommerce-api-legacy-round4-validation.txt`](../evidence/logs/ecommerce-api-legacy-round4-validation.txt) —
ver [Rodada 4](#ecommerce-api-legacy) acima. A nota existe só para explicar a contagem de
findings, não para sinalizar pendência.

⁷ — nota de `code-smells-project` (célula "Mínimo de 5 findings" em §3.3). A rodada 4
([`audit-project-1-part4.md`](../reports/audit-project-1-part4.md), 2026-09-20) achou só 2
findings (1 HIGH + 1 MEDIUM) — abaixo do mínimo de 5, mesma justificativa da nota ⁶: re-auditoria
pontual sobre dois bugs específicos encontrados escrevendo `api-tests.http`, não uma passada
completa. O mínimo de 5 continua demonstrado pela rodada 3 (5 findings, as 3 fases completas).
**Diferente da rodada 4 de `ecommerce-api-legacy` (nota ⁶), esta já teve Fase 3**: os dois
achados foram corrigidos e validados com a aplicação de pé em
[`evidence/logs/code-smells-project-round4-validation.txt`](../evidence/logs/code-smells-project-round4-validation.txt) —
ver [Rodada 4](#code-smells-project) acima.

## Evidências de Execução

Logs de terminal em [`evidence/logs/`](../evidence/logs/), citados em
[§3.4 do README](../README.md#34-evidências-de-execução). O enunciado aceita screenshots
**ou** logs como evidência ([9.4, item C](challenge-original.md#94-requisitos)) — esta entrega
usa só logs de terminal reais, capturados com a aplicação de pé, como evidência única.
Inventário conferido arquivo a arquivo em 2026-09-20 — cada linha descreve o que o log
realmente mostra.

### Logs de terminal (15)

Nomeados `<projeto>-<o-que-prova>.txt`, agrupados por projeto e ordenados por rodada; os que não
citam rodada são anteriores à convenção `-round<N>-validation` e cobrem uma prova pontual, não a
suíte completa de uma rodada.

| Arquivo | Projeto | O que mostra |
|---|---|---|
| `code-smells-project-admin-query-drop-table-blocked.txt` | 1 | `POST /admin/query` com token válido tentando `DROP TABLE produtos` → recusado ("Somente instruções SELECT são permitidas"), seguido de um `SELECT COUNT(*)` com o mesmo token que funciona — a proteção é seletiva, não bloqueio geral. |
| `code-smells-project-arch-check-specific.txt` | 1 | `arch-check.sh` da raiz do projeto: PASS, 2 arquivos de rota, exit 0. |
| `code-smells-project-arch-check-generic.txt` | 1 | A versão genérica empacotada na skill no mesmo projeto: mesmo PASS, com `Detected sources: py` — prova que as duas formas checam a mesma regra. |
| `code-smells-project-manual-tests.txt` | 1 | Suíte `manual-tests.sh` completa. |
| `code-smells-project-round3-validation.txt` | 1 | Validação completa da rodada 3: boot, `arch-check.sh`, correções específicas da rodada e `manual-tests.sh` inteiro. |
| `code-smells-project-round4-validation.txt` | 1 | Validação da rodada 4: boot, `arch-check.sh`, `manual-tests.sh` inteiro sem regressão, e um `curl` por finding corrigido (rowcount check + guard de tipo na paginação). |
| `code-smells-project-skill-run-phase1-2-gate.txt` | 1 | A skill rodando de verdade em modo headless (`claude -p`, só leitura, worktree isolado no commit pré-Fase 3): Fase 1, Fase 2 completa e a **pergunta** do gate. Interrompido ali de propósito — a Fase 3 não roda nesta captura. |
| `ecommerce-api-legacy-checkout-server-log.txt` | 2 | Log do servidor durante os checkouts, com os três cartões mascarados. ⚠️ Anterior à rodada 3 (mesma ressalva de nome/entry point). |
| `ecommerce-api-legacy-manual-tests.txt` | 2 | Suíte `manual-tests.sh` completa. ⚠️ Anterior à rodada 3 — o caso `DELETE /api/users/9999` ainda aparece respondendo 200; hoje responde 404. |
| `ecommerce-api-legacy-round3-validation.txt` | 2 | Validação completa da rodada 3: boot, `arch-check.sh` (com o detector validado antes contra uma violação plantada), `manual-tests.sh`, log do servidor, um `curl` por finding corrigido e a saída de `npm run test:internal`. |
| `ecommerce-api-legacy-round4-validation.txt` | 2 | Validação da rodada 4: boot com/sem `ADMIN_TOKEN` (desabilitado vs. autenticado, nunca aberto), `arch-check.sh`, `manual-tests.sh` sem regressão, `npm run test:internal` (4/4), e o CRITICAL de auth fechado (header forjado/ausente agora 401 nas duas rotas, antes 200). |
| `ecommerce-api-legacy-skill-run-gate-answered.txt` | 2 | O que faltava no anterior: execução **interativa**, com o gate **respondido** (`y` digitado pelo desenvolvedor, com timestamp) e a Fase 3 executando até o resumo de conclusão. Extraído do transcript da própria sessão. |
| `task-manager-api-manual-tests.txt` | 3 | Suíte `manual-tests.sh` completa. É a evidência que sustenta "aplicação funciona" do Projeto 3 nos Critérios de Aceite. |
| `task-manager-api-round3-validation.txt` | 3 | Validação completa da rodada 3: estrutura MVC/AP-16 e os achados estruturais da rodada. |
| `task-manager-api-round4-validation.txt` | 3 | Validação da rodada 4 (auth/autorização): boot com/sem `SECRET_KEY`, tokens forjados/expirados/de contas apagadas ou inativas rejeitados, `pytest` 67/67. |

Os itens marcados com ⚠️ continuam válidos para o que provam, mas foram capturados antes da
rodada 3 do Projeto 2 — ver [Lacunas de Evidência](#lacunas-de-evidência).

## Lacunas de Evidência

- ~~`ecommerce-api-legacy` rodada 4 sem Fase 3/evidência.~~ **Fechado em 2026-09-20**: Fase 3
  rodou (`middlewares/requireAdminToken.js`, guarda por API key nas duas rotas do CRITICAL),
  validada com a aplicação de pé em
  [`evidence/logs/ecommerce-api-legacy-round4-validation.txt`](../evidence/logs/ecommerce-api-legacy-round4-validation.txt) —
  ver [Rodada 4](#ecommerce-api-legacy) acima.
- ~~`code-smells-project` rodada 4 sem Fase 3/evidência.~~ **Fechado em 2026-09-20**: Fase 3 rodou
  (rowcount check em `atualizar_status`, guard de tipo em `parse_pagination`/`buscar`), validada
  com a aplicação de pé em
  [`evidence/logs/code-smells-project-round4-validation.txt`](../evidence/logs/code-smells-project-round4-validation.txt) —
  ver [Rodada 4](#code-smells-project) acima.
- A captura de evidência via screenshot foi descontinuada nesta rodada (2026-09-20): as 10
  imagens em `evidence/` foram removidas porque o enunciado aceita screenshots **ou** logs
  ([9.4, item C](challenge-original.md#94-requisitos)), e os logs de terminal já cobriam o
  mesmo resultado com mais detalhe verificável (não só o estado final, o comando e a saída
  completa). Nenhuma lacuna de evidência resulta disso: cada rodada citada nos itens abaixo já
  tem log completo com a aplicação de pé.
- ~~A skill rodando as 3 fases interativamente e o gate de confirmação da Fase 2 sem evidência
  gravada.~~ **Fechado em 2026-09-20** por
  `evidence/logs/ecommerce-api-legacy-skill-run-gate-answered.txt`: execução
  interativa no Projeto 2 com o `y` do desenvolvedor registrado com timestamp e a Fase 3
  rodando em seguida. O `code-smells-project-skill-run-phase1-2-gate.txt` continua cobrindo o
  outro ângulo — modo headless, somente leitura, parando na pergunta do gate.
- Narrativa de evidências para `ecommerce-api-legacy` e `task-manager-api` (rodada a rodada)
  foram escritas nesta rodada de merge (2026-09-20) — ver
  [Resultados por Projeto](#resultados-por-projeto). Nenhuma pendência de narrativa restante
  para os 3 projetos no estado atual.
- `ecommerce-api-legacy-checkout-server-log.txt` é anterior à rodada 3 e ainda mostra o nome
  antigo do pacote, `node src/app.js` e "Frankenstein LMS". Continua válido para o que prova
  (cartão mascarado no log), mas não reflete o entry point atual.

## Comportamento entre Diferentes Stacks

A mesma skill (`SKILL.md` + `references/` + `scripts/`, sem nenhuma edição entre execuções)
produziu relatórios e refatorações corretos em três arquiteturas de partida bem diferentes —
ver [§3.5 do README](../README.md#35-comportamento-entre-diferentes-stacks):

- **`code-smells-project`** (Python/Flask 3.1.1, SQLite cru) — monolito de 4 arquivos sem
  nenhuma separação de camadas. A Fase 3 construiu `config/`, `controllers/`, `models/`,
  `routes/`, `middlewares/`, `utils/` do zero.
- **`ecommerce-api-legacy`** (Node.js/Express 4.18.2, `sqlite3`) — monolito de 3 arquivos, mesma
  falta de camadas, stack e linguagem totalmente diferentes. A Fase 1 detectou
  `package.json`/`express`/`sqlite3` sem qualquer heurística específica de Python, e a Fase 3
  construiu o equivalente MVC em `src/config/`, `src/controllers/`, `src/models/`,
  `src/routes/`, `src/middlewares/`.
- **`task-manager-api`** (Python/Flask 3.0.0 + SQLAlchemy) — já chegava com `models/`,
  `routes/`, `services/`, `utils/` parcialmente separados. Aqui a Fase 3 não reconstruiu nada:
  ajustou as camadas existentes (rotas que ainda chamavam o ORM direto viraram
  parse→controller/service→serializa) em vez de forçar um layout genérico por cima do que já
  fazia sentido — a mesma instrução do `SKILL.md` ("adapte ao que já existe, não force um
  template") produziu um resultado estruturalmente diferente dos outros dois projetos.

O único ponto onde o processo teve que evoluir entre projetos foi o catálogo em si, não a
skill: o anti-pattern AP-16 (persistência chamada direto da rota) só entrou no catálogo depois
de aparecer em `task-manager-api` e atravessar a auditoria original sem ser pego — ver o
achado ⁵ acima e o postmortem em [README](../README.md#2-construção-da-skill). Depois de
catalogado, o mesmo `arch-check.sh` (versão genérica da skill) e as versões específicas de
cada projeto passaram a detectar AP-16 nos 3 projetos sem qualquer lógica por stack além da
detecção de rota já prevista em `references/verification-recipes.md`.

Comparação numérica completa (findings por severidade e por rodada) está em
[§3.1 do README](../README.md#31-resumo-das-auditorias) e nas seções de
[Resultados por Projeto](#resultados-por-projeto) acima.
