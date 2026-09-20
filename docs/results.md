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

Nenhuma screenshot nova foi capturada nesta rodada — as imagens em `evidence/` continuam sendo das
rodadas anteriores; ver [Lacunas de Evidência](#lacunas-de-evidência).

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

### task-manager-api

Rodadas registradas em [`audit-project-3.md`](../reports/audit-project-3.md) (14 findings: 4
CRITICAL, 2 HIGH, 4 MEDIUM, 4 LOW) e [`audit-project-3-part2.md`](../reports/audit-project-3-part2.md)
(7 findings: 0 CRITICAL, 2 HIGH, 2 MEDIUM, 3 LOW). Mesma situação do projeto 2: narrativa ainda não
escrita neste documento, não verificada nesta sessão. Ver os relatórios diretamente.

## Checklist de Validação Preenchido

Notas de rodapé referenciadas pela tabela da [§3.3 do README](../README.md#33-checklist-de-validação-preenchido):

¹ — nota de `ecommerce-api-legacy` (célula "Relatório segue o template"). Verificada na
rodada 3 (2026-09-20), lendo os três relatórios do projeto: os três seguem
`references/audit-report-template.md` — cabeçalho em caixa, linha `Stack:`/`Files:`, bloco
`## Summary` com a contagem por severidade, um bloco por finding com `File:`/`Description:`/
`Impact:`/`Recommendation:` citando AP-xx/RP-xx, ordenação CRITICAL → LOW, total e a pergunta
final literal do gate. As partes 2 e 3 acrescentam, como o template manda para re-execução, a
seção `## Resolved since ...` no topo, com o delta em relação à parte anterior.

², ³, ⁴ — notas de `task-manager-api` (células "Estrutura de diretórios segue MVC", "Controllers
concentram o fluxo" e "Error handling centralizado", respectivamente). **Pendentes** — não
verificadas nesta sessão; preencher ao revisar esse projeto diretamente.

⁵ — **O achado de `admin_controller.py` que motivou a re-auditoria de `code-smells-project`.**
Entre a rodada 1 e a rodada 2, a Fase 3 corrigiu o vazamento de segredo e a injeção de SQL nas
rotas de negócio, mas manteve `POST /admin/query` executando SQL vindo do cliente. A rodada 2
achou isso de novo (agora autenticado, mas ainda cru) e recomendou removê-lo. A rodada 3 (2026-09-19)
finalmente fechou: `models/admin_model.py` não aceita mais SQL do cliente — só uma tabela de uma
allow-list fixa (`produtos`, `usuarios`, `pedidos`, `itens_pedido`), cada uma resolvendo para uma
query parametrizada hardcoded. Ver [rodada 3 de `code-smells-project`](#code-smells-project) acima.

## Evidências de Execução

Galeria em [`evidence/`](../evidence/), citada em
[§3.4 do README](../README.md#34-evidências-de-execução). Inventário conferido arquivo a
arquivo em 2026-09-20 — cada linha descreve o que a imagem ou o log realmente mostra.

### Screenshots (10)

| Arquivo | Projeto | O que mostra |
|---|---|---|
| `project1-boot.png` | 1 | Terminal: `INFO __main__: Servidor iniciado em http://0.0.0.0:5000` com `Debug mode: off`. Prova as duas correções da rodada 1 de uma vez — `logging` estruturado no lugar de `print`, e `DEBUG` vindo do config em vez de `True` fixo. |
| `project1-admin-bloqueado.png` | 1 | Postman: `POST /admin/query` com `{"sql": "SELECT 1"}` → **403 FORBIDDEN**, `{"erro": "Endpoints administrativos desabilitados"}`. |
| `project1-usuarios-sem-senha.png` | 1 | Postman: `GET /usuarios` → 200, objetos com `criado_em`/`email`/`id`/`nome`/`tipo` — **sem o campo `senha`**, que a versão legada devolvia. |
| `project2-boot.png` | 2 | Terminal: log JSON de boot na porta 3000. ⚠️ Anterior à rodada 3 — mostra `desafio-arquitetura-ia-boilerplate@1.0.0`, `node src/app.js` e o nome "Frankenstein LMS", os três substituídos depois (`ecommerce-api-legacy@1.0.0`, `node src/server.js`, nome vindo do config). |
| `project2-checkout-sem-cartao.png` | 2 | Postman: `POST /api/checkout` com `card` no request → 200 `{"msg":"Sucesso","enrollment_id":2}`. O ponto é a resposta **não** ecoar o cartão. |
| `project2-checkout-sem-cartao-log.png` | 2 | Terminal do mesmo checkout: `"card":"4111*******1111"` — mascarado no log. ⚠️ Mesma ressalva de rodada do `project2-boot.png`. |
| `project3-boot.png` | 3 | Terminal: Flask subindo com `Debug mode: off`. |
| `project3-login-token.png` | 3 | Postman: `POST /login` → 200 com `token` assinado e objeto `user` **sem campo de senha/hash**. |
| `project3-tasks-paginacao.png` | 3 | Postman: `GET /tasks?page=1&per_page=2` → exatamente 2 tarefas. Prova a paginação que o legado não tinha. |
| `project3-users-sem-senha.png` | 3 | Postman: `GET /users/1` → 200 com `tasks` aninhadas e **sem campo de senha**. |

### Logs de terminal (11)

| Arquivo | Projeto | O que mostra |
|---|---|---|
| `code-smells-project-round3-validation.txt` | 1 | Validação completa da rodada 3: boot, `arch-check.sh`, correções específicas da rodada e `manual-tests.sh` inteiro. |
| `ecommerce-api-legacy-round3-validation.txt` | 2 | Validação completa da rodada 3: boot, `arch-check.sh` (com o detector validado antes contra uma violação plantada), `manual-tests.sh`, log do servidor, um `curl` por finding corrigido e a saída de `npm run test:internal`. |
| `item1-2-skill-phase1-phase2-gate-code-smells-project.txt` | 1 | A skill rodando de verdade em modo headless (`claude -p`, só leitura, worktree isolado no commit pré-Fase 3): Fase 1, Fase 2 completa e a **pergunta** do gate. Interrompido ali de propósito — a Fase 3 não roda nesta captura. |
| `item1-2-skill-3-fases-gate-respondido-ecommerce-api-legacy.txt` | 2 | O que faltava no anterior: execução **interativa**, com o gate **respondido** (`y` digitado pelo desenvolvedor, com timestamp) e a Fase 3 executando até o resumo de conclusão. Extraído do transcript da própria sessão. |
| `item3-arch-check-project-specific.txt` | 1 | `arch-check.sh` da raiz do projeto: PASS, 2 arquivos de rota, exit 0. |
| `item4-arch-check-bundled-generic.txt` | 1 | A versão genérica empacotada na skill no mesmo projeto: mesmo PASS, com `Detected sources: py` — prova que as duas formas checam a mesma regra. |
| `item5-manual-tests-project1.txt` | 1 | Suíte `manual-tests.sh` completa. |
| `item5-manual-tests-project2.txt` | 2 | Suíte `manual-tests.sh` completa. ⚠️ Anterior à rodada 3 — o caso `DELETE /api/users/9999` ainda aparece respondendo 200; hoje responde 404. |
| `item5-manual-tests-project3.txt` | 3 | Suíte `manual-tests.sh` completa. É a evidência que sustenta "aplicação funciona" do Projeto 3 nos Critérios de Aceite. |
| `item7a-drop-table-blocked-project1.txt` | 1 | `POST /admin/query` com token válido tentando `DROP TABLE produtos` → recusado ("Somente instruções SELECT são permitidas"), seguido de um `SELECT COUNT(*)` com o mesmo token que funciona — a proteção é seletiva, não bloqueio geral. |
| `item9-project2-checkout-server-log.txt` | 2 | Log do servidor durante os checkouts, com os três cartões mascarados. ⚠️ Anterior à rodada 3 (mesma ressalva de nome/entry point). |

Os itens marcados com ⚠️ continuam válidos para o que provam, mas foram capturados antes da
rodada 3 do Projeto 2 — ver [Lacunas de Evidência](#lacunas-de-evidência).

## Lacunas de Evidência

- A rodada 3 de `code-smells-project` (2026-09-19) tem log de validação completo em
  `evidence/logs/code-smells-project-round3-validation.txt`, mas **não** tem screenshot nova —
  as imagens `evidence/project1-*` ainda são das rodadas anteriores. A primeira tentativa desta
  rodada terminou sem nenhuma evidência: a captura era uma linha passiva numa tabela de referência
  do `CLAUDE.md`, lida só no rollup de documentação, quando a aplicação já havia sido derrubada.
  Corrigido em duas frentes — a captura virou gate obrigatório na seção "Antes de dar uma
  refatoração por concluída" do `CLAUDE.md` (executada com o app de pé, não depois), e
  `scripts/sync-docs.sh --check` agora falha com exit 1 quando um relatório em `reports/` é mais
  novo que a evidência do mesmo projeto.
- ~~A skill rodando as 3 fases interativamente e o gate de confirmação da Fase 2 sem evidência
  gravada.~~ **Fechado em 2026-09-20** por
  `evidence/logs/item1-2-skill-3-fases-gate-respondido-ecommerce-api-legacy.txt`: execução
  interativa no Projeto 2 com o `y` do desenvolvedor registrado com timestamp e a Fase 3
  rodando em seguida. O `item1-2-...-code-smells-project.txt` continua cobrindo o outro ângulo
  — modo headless, somente leitura, parando na pergunta do gate.
- A rodada 3 de `ecommerce-api-legacy` (2026-09-20) tem log de validação completo em
  `evidence/logs/ecommerce-api-legacy-round3-validation.txt`, mas **não** tem screenshot nova —
  `evidence/project2-*.png` continuam sendo das rodadas anteriores. O log cobre boot, os dois
  validadores e um `curl` por finding, capturados com a aplicação de pé; a screenshot é a única
  peça faltando.
- Narrativa rodada a rodada de `task-manager-api` ainda não escrita — ver
  [Resultados por Projeto](#resultados-por-projeto). A de `ecommerce-api-legacy` foi escrita na
  rodada 3. Será preenchida quando esse projeto tiver a próxima rodada.
- Três capturas do Projeto 2 (`project2-boot.png`, `project2-checkout-sem-cartao-log.png`,
  `item9-project2-checkout-server-log.txt`) são anteriores à rodada 3 e ainda mostram o nome
  antigo do pacote, `node src/app.js` e "Frankenstein LMS". Continuam válidas para o que provam
  (cartão mascarado, boot com log estruturado), mas não refletem o entry point atual.

## Comportamento entre Diferentes Stacks

A comparação entre Python/Flask monolítico (`code-smells-project`), Node.js/Express monolítico
(`ecommerce-api-legacy`) e Python/Flask parcialmente em camadas (`task-manager-api`) — ver
[§3.5 do README](../README.md#35-comportamento-entre-diferentes-stacks) — ainda não tem a
narrativa completa registrada aqui — pendente, não verificado nesta sessão.
