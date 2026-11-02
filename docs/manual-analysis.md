## 1. Análise Manual

[← README §1](../README.md#1-análise-manual)

Leitura manual dos 3 projetos **antes** de escrever a skill — o insumo que definiu quais
padrões o catálogo precisava detectar. Foram 8 achados no primeiro projeto e 9 em cada um dos
outros, acima do mínimo do enunciado (5, com ≥1 CRITICAL/HIGH, ≥2 MEDIUM, ≥2 LOW). As linhas se
referem ao código original do boilerplate, antes da Fase 3.

| # | Projeto | Stack | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---:|---:|---:|---:|---:|
| 1 | `code-smells-project` | Flask 3.1.1 + SQLite cru | 3 | 1 | 2 | 2 | 8 |
| 2 | `ecommerce-api-legacy` | Express 4.22.1 + sqlite3 5.1.7 | 4 | 1 | 2 | 2 | 9 |
| 3 | `task-manager-api` | Flask + SQLAlchemy | 3 | 1 | 3 | 2 | 9 |

#### Projeto 1 — `code-smells-project` (Flask 3.1.1 + SQLite cru)

| Severidade | Achado | Localização | Por que é relevante |
|---|---|---|---|
| CRITICAL | SQL Injection generalizada | `models.py:47-50,57-61,109-111,126-129,140,148-151,155-161,163-166,289-299` | As queries são montadas por concatenação, sem parâmetro preparado, e campos vindos do cliente chegam ao SQL sem tratamento: `nome` e `descricao` (`POST`/`PUT /produtos`), `categoria` (`PUT /produtos/<id>` e busca), `email` e `senha` (`POST /login`, `POST /usuarios`), `usuario_id` e `produto_id` do corpo de `POST /pedidos` e `q` da busca. Sem autenticação, qualquer cliente entra sem senha (`senha = ' OR '1'='1` loga como o primeiro usuário, o admin), lê qualquer tabela via `UNION` na busca, altera todos os produtos de uma vez e cria uma conta `admin` pelo `POST /usuarios` |
| CRITICAL | Segredo de aplicação hardcoded e vazado na resposta | `app.py:7-8,88`, `controllers.py:285-289` | `SECRET_KEY` fixa no código-fonte, `DEBUG=True`, e o `/health` devolve `secret_key` e `debug` no corpo. O segredo que assina sessão fica público no repositório **e** na própria API — invalida qualquer garantia de integridade de sessão |
| CRITICAL | Senha em texto plano, devolvida nas respostas | `database.py:31,75-83`, `models.py:83,99,105-111,122-128` | A coluna `senha` guarda o valor como digitado (o seed grava `admin123`, `123456`, `senha123`), o login compara em claro no SQL e a serialização de usuário inclui `senha`: uma chamada a `GET /usuarios` entrega a credencial de todas as contas |
| HIGH | God Class / sem separação MVC | `models.py` (4 domínios), `controllers.py:208-210,268-274`, `app.py:51-54,69` | Os 4 domínios vivem em `models.py`, os controllers misturam parsing, validação e notificação simulada de e-mail/SMS (`controllers.py:208-210`) e há SQL também fora de `models.py` (`app.py:51-54,69`, `controllers.py:268-274`): nenhuma regra é testável isoladamente e qualquer alteração em um domínio arrisca os outros três. É HIGH, não CRITICAL, porque rotas, controllers e SQL já estão em arquivos separados |
| MEDIUM | Queries N+1 no histórico de pedidos | `models.py:171-233` | Um cursor por pedido e outro por item, em laços aninhados: uma única listagem dispara dezenas de queries e degrada junto com a base |
| MEDIUM | Ausência de paginação nas listagens | `controllers.py:5-12,128-134,229-235` | `/produtos`, `/usuarios` e `/pedidos` devolvem a tabela inteira, sem `limit`/`offset` — gargalo de payload que piora sozinho com o crescimento |
| LOW | `print()` como mecanismo de log | `controllers.py:8,11,57,61,106,161,179,182,208-210,219,248,250`, `app.py:56,83-86` | Sem níveis, sem estrutura, sem rotação — inviável de operar em produção |
| LOW | Categorias válidas hardcoded inline | `controllers.py:52` | Incluir uma categoria exige alterar código-fonte; deveria vir de configuração ou tabela |

#### Projeto 2 — `ecommerce-api-legacy` (Express 4.22.1 + sqlite3 5.1.7)

| Severidade | Achado | Localização | Por que é relevante |
|---|---|---|---|
| CRITICAL | Segredos de produção hardcoded | `src/utils.js:2-5` | `dbPass`, `smtpUser` e uma chave de gateway no formato `pk_live_...` fixos no código — e a chave é impressa no log a cada checkout (`src/AppManager.js:45`). Chave "live" vazada é incidente imediato, não hipotético |
| CRITICAL | Hashing de senha falso/quebrado | `src/utils.js:17-23` (`badCrypto`), usado em `src/AppManager.js:68` | O "hash" são os 2 primeiros caracteres do base64 da senha, repetidos e truncados: senhas que começam igual têm o mesmo "hash", e quem lê a tabela recupera o começo da senha decodificando o base64. Equivale a guardar a senha em claro com verniz cosmético |
| CRITICAL | Número completo do cartão no log | `src/AppManager.js:33,45` | O cartão lido do corpo (`:33`) é impresso inteiro, sem máscara, junto com a chave do gateway (`:45`) a cada checkout: dado PCI-DSS em todo destino de log, retido por mais tempo e com menos controle de acesso que o banco |
| CRITICAL | God Class | `src/AppManager.js:4-139` | Uma única classe cria o schema, faz seed, define todas as rotas e executa a lógica de pagamento, sem camada intermediária. É exatamente o exemplo de CRITICAL do enunciado — impossível testar em isolamento |
| HIGH | Estado mutável global no módulo `utils` | `src/utils.js:9-10,14`, `src/AppManager.js:2` | `globalCache` e `totalRevenue` são variáveis de módulo. `globalCache` é gravado a cada checkout (`:14`) e acumula uma entrada por usuário, compartilhada por todas as requisições, sem limite de tamanho nem expiração; `totalRevenue` é exportado por valor (o `AppManager.js:2` recebe uma cópia) e nunca é atualizado. É o exemplo de HIGH do enunciado ("estado global mutável em toda a aplicação") |
| MEDIUM | N+1 em cascata de callbacks no relatório financeiro | `src/AppManager.js:80-129` | Uma query por curso e, por matrícula, uma de usuário e outra de pagamento, aninhadas: o tempo de resposta cresce multiplicativamente e produz o callback hell que trava a manutenção |
| MEDIUM | Relatório financeiro sem paginação | `src/AppManager.js:80-129` | Todos os cursos e todas as matrículas numa resposta só; o payload cresce com cursos × matrículas |
| LOW | `console.log` como logging | `src/utils.js:13`, `src/AppManager.js:45` | Mesma limitação do Projeto 1: sem níveis, sem estrutura |
| LOW | Mistura de idiomas inconsistente | `src/AppManager.js` (mensagens pt-BR, identificadores em inglês) | Não é falha funcional, é custo de manutenção: sem convenção única, cada novo trecho escolhe o idioma por conta própria |

#### Projeto 3 — `task-manager-api` (Flask + SQLAlchemy)

| Severidade | Achado | Localização | Por que é relevante |
|---|---|---|---|
| CRITICAL | `SECRET_KEY` e senha SMTP hardcoded | `app.py:13`, `services/notification_service.py:7-10` | O segredo que assina a aplicação (`'super-secret-key-123'`) e a credencial de e-mail (`taskmanager@gmail.com` / `senha123`) estão literais no código e no histórico do git: quem lê o repositório tem as duas |
| CRITICAL | Hashing de senha fraco e sem salt (MD5) | `models/user.py:27-32` | MD5 é criptograficamente quebrado e, sem salt, cede a rainbow table. Confirmado em execução: o hash devolvido pela API bateu com `hashlib.md5('1234')` calculado localmente |
| CRITICAL | Hash de senha vazado nas respostas da API | `models/user.py:16-25` (`to_dict`), servido em `routes/user_routes.py:33,85-86,129,209` | `to_dict()` inclui `password` e é usado em `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`. Combinado com o MD5 acima, entrega material pronto para ataque offline a qualquer cliente |
| HIGH | Regra de negócio duplicada dentro das rotas | `models/task.py:50-60` (`is_overdue`), reimplementada em `routes/task_routes.py:30-39,71-80,283-287`, `routes/user_routes.py:171-180`, `routes/report_routes.py:33-43,132-136` | "Task atrasada" é reescrita à mão 6 vezes em vez de reusar `Task.is_overdue()`: rota fazendo cálculo de domínio (violação de MVC) e risco real de a regra divergir em silêncio se alguém corrigir só um ponto |
| MEDIUM | Camada de serviço morta / nunca conectada | `services/notification_service.py` | `NotificationService` não é importado nem chamado por rota alguma: a estrutura de pastas anuncia uma feature que nunca roda. Confirmado em execução — criei uma task atribuída e nenhum log de envio apareceu |
| MEDIUM | Queries N+1 nas listagens e relatórios | `routes/task_routes.py:14-51`, `routes/user_routes.py:14-22`, `routes/report_routes.py:53-56,161-163` | `GET /tasks` faz uma query de usuário e outra de categoria por task (2N+1); `GET /users` carrega `u.tasks` por usuário e os relatórios repetem o padrão por usuário e por categoria |
| MEDIUM | Ausência de paginação | `routes/task_routes.py:11-14`, `routes/user_routes.py:10-12`, `routes/report_routes.py:12-101` | Listagens e relatórios varrem a tabela inteira — aqui agravado pelo N+1 acima, que multiplica o custo de cada linha |
| LOW | `print()` como logging | `routes/task_routes.py`, `routes/user_routes.py`, `services/notification_service.py`, `utils/helpers.py:39-41` | Terceira ocorrência do mesmo padrão nos 3 projetos: sem níveis, sem estrutura |
| LOW | Imports não utilizados | `routes/task_routes.py:7` (`json, os, sys, time`), `routes/user_routes.py:6` (`hashlib, json`), `routes/report_routes.py:7-8` (`format_date, calculate_percentage, json`), `models/task.py:3` (`json`), `utils/helpers.py:3-7` (`os, json, sys, math, hashlib`), `app.py:7` (`os, sys, json`) | Ruído que esconde as dependências reais de cada arquivo e engana quem lê o topo do módulo |
