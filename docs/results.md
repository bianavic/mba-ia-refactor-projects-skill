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

Rodadas registradas em [`audit-project-2.md`](../reports/audit-project-2.md) (12 findings: 4
CRITICAL, 2 HIGH, 2 MEDIUM, 4 LOW) e [`audit-project-2-part2.md`](../reports/audit-project-2-part2.md)
(8 findings: 1 CRITICAL, 2 HIGH, 2 MEDIUM, 3 LOW). Narrativa rodada a rodada (o que a Fase 3 mudou
de fato, o que ficou aberto entre as duas) ainda não foi escrita neste documento — não foi
verificada nesta sessão. Ver os relatórios diretamente enquanto isso não é preenchido.

### task-manager-api

Rodadas registradas em [`audit-project-3.md`](../reports/audit-project-3.md) (14 findings: 4
CRITICAL, 2 HIGH, 4 MEDIUM, 4 LOW) e [`audit-project-3-part2.md`](../reports/audit-project-3-part2.md)
(7 findings: 0 CRITICAL, 2 HIGH, 2 MEDIUM, 3 LOW). Mesma situação do projeto 2: narrativa ainda não
escrita neste documento, não verificada nesta sessão. Ver os relatórios diretamente.

## Checklist de Validação Preenchido

Notas de rodapé referenciadas pela tabela da [§3.3 do README](../README.md#33-checklist-de-validação-preenchido):

¹ — nota de `ecommerce-api-legacy` (célula "Relatório segue o template"). **Pendente** — não
verificada nesta sessão; preencher ao revisar o relatório desse projeto diretamente.

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

Galeria de screenshots e logs em [`evidence/`](../evidence/), citada em
[§3.4 do README](../README.md#34-evidências-de-execução). O inventário completo (o que cada
arquivo mostra, de qual projeto/rodada) ainda não foi escrito neste documento — pendente,
não verificado nesta sessão.

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
- A skill rodando as 3 fases interativamente (prompt real, não reconstruído) e o gate de
  confirmação da Fase 2 continuam sem evidência gravada, conforme já apontado no README.
- Narrativa de evidências para `ecommerce-api-legacy` e `task-manager-api` (rodada a rodada)
  ainda não foi escrita — ver [Resultados por Projeto](#resultados-por-projeto).

## Comportamento entre Diferentes Stacks

A comparação entre Python/Flask monolítico (`code-smells-project`), Node.js/Express monolítico
(`ecommerce-api-legacy`) e Python/Flask parcialmente em camadas (`task-manager-api`) — ver
[§3.5 do README](../README.md#35-comportamento-entre-diferentes-stacks) — ainda não tem a
narrativa completa registrada aqui — pendente, não verificado nesta sessão.
