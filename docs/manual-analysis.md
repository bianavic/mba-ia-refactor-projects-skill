# Análise Manual

[← README](../README.md) · [Design da Skill](skill-design.md) · [Resultados](results.md) · [Evolução do Uso de IA](ai-evolution.md) · [Estrutura do Projeto](project-structure.md) · [Enunciado Original](challenge-original.md)

> Detalhamento completo dos 21 achados (7 por projeto) da análise manual que precedeu a skill — moldou diretamente o catálogo de anti-patterns ([seção B no README](../README.md#2-construção-da-skill)). O resumo condensado, com uma tabela por projeto, está na [seção 1 do README](../README.md#1-análise-manual).

---

## 1.1 code-smells-project
| | |
|---|---|
| **Stack** | Flask 3.1.1 + flask-cors, SQLite (`loja.db`) |
| **Domínio** | E-commerce (produtos, usuários, pedidos, itens_pedido) |
| **Arquivos** | 4 (`app.py`, `controllers.py`, `models.py`, `database.py`), ~600 linhas, sem separação de camadas |
| **Resumo** | CRITICAL: 2 · HIGH: 1 · MEDIUM: 2 · LOW: 2 — **Total: 7** |

| Severidade | Achado | Localização |
|---|---|---|
| CRITICAL | SQL Injection generalizada | `models.py` (~20 pontos) |
| CRITICAL | Credenciais/segredo hardcoded e vazados em resposta | `app.py:7-8`, `controllers.py:285-289` |
| HIGH | God Class / ausência total de separação MVC | `models.py`, `controllers.py` |
| MEDIUM | Queries N+1 no histórico de pedidos | `models.py:171-233` |
| MEDIUM | Ausência de paginação nas listagens | `controllers.py:5-12,128-134,229-235` |
| LOW | `print()` como log | `controllers.py`, `app.py:56,83-86` |
| LOW | Categorias válidas hardcoded inline | `controllers.py:52` |

<details>
<summary><strong>Detalhamento dos 7 achados</strong></summary>

### [CRITICAL] SQL Injection generalizada
- **Arquivo:** `models.py:28,47-50,58-61,68,92,110,127-129,140,148-151,155,158-161,164-166,174,188,192,220,224,279-281,290-297`
- **Descrição:** praticamente todas as queries são montadas por concatenação de string (`"... WHERE id = " + str(id)`, `"VALUES ('" + nome + "', ...)"`), sem parâmetros preparados.
- **Impacto:** qualquer campo controlado pelo cliente (id, nome, email, termo de busca) permite injeção de SQL arbitrária — leitura, alteração ou destruição de dados. É o problema de maior impacto do projeto.
- **Validado em execução:** confirmado via `POST /admin/query` (achado abaixo), que expôs `SELECT nome, senha FROM usuarios` sem qualquer filtro.

### [CRITICAL] Credenciais e segredo de aplicação hardcoded, e vazados em resposta
- **Arquivo:** `app.py:7-8`; `controllers.py:285-289`
- **Descrição:** `SECRET_KEY` fixo no código-fonte, `DEBUG=True` em produção, e o endpoint `/health` retorna `secret_key` e `debug` no corpo JSON da resposta.
- **Impacto:** o segredo usado para assinar sessões/tokens fica público no repositório *e* na própria API — invalida qualquer garantia de integridade de sessão.
- **Validado em execução:** `curl /health` retornou `"debug":true,"secret_key":"minha-chave-super-secreta-123"` no corpo da resposta.

### [HIGH] God Class / ausência total de separação MVC
- **Arquivo:** `models.py` (1 arquivo, todos os domínios) + `controllers.py` (mistura roteamento, validação e "regras de negócio")
- **Descrição:** os 4 domínios (produtos, usuários, pedidos, itens) inteiros vivem em `models.py`; `controllers.py` mistura parsing de request, validação, SQL e simulação de envio de email/SMS/push (`controllers.py:208-210`).
- **Impacto:** impossível testar qualquer regra isoladamente; qualquer alteração em um domínio arrisca quebrar os outros três que compartilham o mesmo arquivo.

### [MEDIUM] Queries N+1 no histórico de pedidos
- **Arquivo:** `models.py:171-233` (`get_pedidos_usuario`, `get_todos_pedidos`)
- **Descrição:** para cada pedido é aberto um cursor para buscar itens, e para cada item outro cursor para buscar o nome do produto — dentro de loops aninhados.
- **Impacto:** degrada rapidamente com o crescimento da base de pedidos; uma única listagem pode disparar dezenas de queries.

### [MEDIUM] Ausência de paginação nas listagens
- **Arquivo:** `controllers.py:5-12,128-134,229-235`
- **Descrição:** `/produtos`, `/usuarios` e `/pedidos` retornam a tabela inteira sem `limit`/`offset`.
- **Impacto:** gargalo de performance e de payload à medida que a base cresce.

### [LOW] `print()` como mecanismo de log
- **Arquivo:** `controllers.py` (praticamente todas as funções), `app.py:56,83-86`
- **Descrição:** uso de `print()` em vez do módulo `logging`.
- **Impacto:** sem níveis, sem estrutura, sem rotação — inviável em produção.

### [LOW] Lista de categorias válidas hardcoded inline
- **Arquivo:** `controllers.py:52`
- **Descrição:** `categorias_validas = ["informatica", "moveis", ...]` embutida na função de criação.
- **Impacto:** qualquer nova categoria exige alterar código-fonte; deveria vir de configuração ou tabela.

</details>

## 1.2 ecommerce-api-legacy
| | |
|---|---|
| **Stack** | Node.js + Express 4.18.2, SQLite (`sqlite3`) |
| **Domínio** | LMS — E-learning (usuários, cursos, matrículas, pagamentos, auditoria) |
| **Arquivos** | 3 (`src/app.js`, `src/AppManager.js`, `src/utils.js`), ~180 linhas, sem separação de camadas |
| **Resumo** | CRITICAL: 2 · HIGH: 1 · MEDIUM: 2 · LOW: 2 — **Total: 7** |

| Severidade | Achado | Localização |
|---|---|---|
| CRITICAL | Segredos de produção hardcoded | `utils.js:2-6` |
| CRITICAL | Hashing de senha falso/quebrado | `utils.js:17-23` |
| HIGH | God Class | `AppManager.js:1-142` |
| MEDIUM | N+1 em cascata de callbacks no relatório financeiro | `AppManager.js:80-129` |
| MEDIUM | Estado mutável global no módulo utils | `utils.js:9-10` |
| LOW | `console.log` como logging | `utils.js:13`, `AppManager.js:45` |
| LOW | Mistura de idiomas inconsistente | `AppManager.js` |

<details>
<summary><strong>Detalhamento dos 7 achados</strong></summary>

### [CRITICAL] Segredos de produção hardcoded
- **Arquivo:** `utils.js:2-6`
- **Descrição:** `dbPass`, `paymentGatewayKey` (formato `pk_live_...`) e `smtpUser` estão fixos no código-fonte.
- **Impacto:** uma chave de gateway de pagamento "live" vazada no repositório é um incidente de segurança imediato, não hipotético.
- **Validado em execução:** o log do processo imprime a chave `pk_live_1234567890abcdef` a cada checkout.

### [CRITICAL] Hashing de senha falso/quebrado
- **Arquivo:** `utils.js:17-23` (`badCrypto`), usado em `AppManager.js:68`
- **Descrição:** "hash" é apenas base64 do texto repetido 10.000 vezes e truncado — não é uma função de derivação de chave, é trivialmente reversível.
- **Impacto:** equivale a armazenar a senha em claro com um verniz cosmético; qualquer vazamento de dados expõe todas as credenciais.

### [HIGH] God Class
- **Arquivo:** `AppManager.js:1-142`
- **Descrição:** uma única classe cria o schema, faz seed, define todas as rotas e executa a "lógica de pagamento", sem nenhuma camada intermediária.
- **Impacto:** corresponde exatamente ao exemplo de CRITICAL/HIGH do enunciado — arquitetura, roteamento e regra de negócio no mesmo lugar, impossível de testar em isolamento.

### [MEDIUM] N+1 em cascata de callbacks no relatório financeiro
- **Arquivo:** `AppManager.js:80-129`
- **Descrição:** para cada curso é feita uma query de matrículas; para cada matrícula, uma de usuário e outra de pagamento — tudo aninhado em callbacks.
- **Impacto:** o tempo de resposta cresce multiplicativamente com o número de cursos × matrículas; também é a origem do "callback hell" que dificulta leitura e manutenção.

### [MEDIUM] Estado mutável global no módulo utils
- **Arquivo:** `utils.js:9-10`
- **Descrição:** `globalCache` e `totalRevenue` são variáveis de módulo compartilhadas; `totalRevenue` sequer é atualizado em lugar algum.
- **Impacto:** estado global mutável em runtime concorrente (Node/Express) é fonte clássica de race conditions e comportamento não determinístico.

### [LOW] `console.log` como logging
- **Arquivo:** `utils.js:13`, `AppManager.js:45`
- **Descrição:** sem structured logging, sem níveis.
- **Impacto:** mesma limitação do projeto 1 — inviável operar em produção.

### [LOW] Mistura de idiomas inconsistente
- **Arquivo:** `AppManager.js` (mensagens em pt-BR, identificadores em inglês)
- **Descrição:** sem convenção única de idioma no código.
- **Impacto:** problema de padronização/manutenibilidade, não funcional.

</details>

## 1.3 task-manager-api
| | |
|---|---|
| **Stack** | Flask + Flask-SQLAlchemy, SQLite (`tasks.db`) |
| **Domínio** | Task Manager (users, tasks, categories) |
| **Arquivos** | já possui separação em pastas (`models/`, `routes/`, `services/`, `utils/`), mas a separação é apenas estrutural — a disciplina de responsabilidades por camada não é respeitada |
| **Resumo** | CRITICAL: 2 · HIGH: 1 · MEDIUM: 2 · LOW: 2 — **Total: 7** |

| Severidade | Achado | Localização |
|---|---|---|
| CRITICAL | Hashing de senha fraco e sem salt (MD5) | `models/user.py:27-31` |
| CRITICAL | Hash de senha vazado em toda resposta de API | `models/user.py:16-25` |
| HIGH | Regra de negócio duplicada nas rotas em vez de centralizada | `models/task.py:50-60` + 3 rotas |
| MEDIUM | Camada de serviço morta / nunca conectada | `services/notification_service.py` |
| MEDIUM | Ausência de paginação | `routes/task_routes.py`, `routes/user_routes.py`, `routes/report_routes.py` |
| LOW | `print()` como logging | `routes/*`, `services/notification_service.py` |
| LOW | Imports não utilizados | `routes/task_routes.py:7`, `app.py:7` |

<details>
<summary><strong>Detalhamento dos 7 achados</strong></summary>

### [CRITICAL] Hashing de senha fraco e sem salt
- **Arquivo:** `models/user.py:27-31`
- **Descrição:** `set_password`/`check_password` usam `hashlib.md5` puro, sem salt.
- **Impacto:** MD5 é criptograficamente quebrado e, sem salt, é trivial atacar com rainbow tables — mesma classe de falha dos outros dois projetos.
- **Validado em execução:** o hash retornado pela API bateu exatamente com `hashlib.md5('1234')` calculado localmente.

### [CRITICAL] Hash de senha vazado em toda resposta de API
- **Arquivo:** `models/user.py:16-25` (`to_dict`), servido em `routes/user_routes.py:85-86,129,209`
- **Descrição:** `to_dict()` inclui o campo `password` (o hash) e é usado em `POST /users`, `PUT /users/<id>` e `POST /login`.
- **Impacto:** mesmo sendo "só" o hash, expõe material sensível desnecessariamente a qualquer cliente — combinado com o MD5 acima, facilita ataque offline.
- **Validado em execução:** `GET /users/1` e `POST /login` devolveram o campo `"password"` com o hash em claro no JSON.

### [HIGH] Regra de negócio duplicada dentro das rotas em vez de centralizada
- **Arquivo:** `models/task.py:50-60` (`is_overdue`), reimplementada em `routes/task_routes.py:30-39,71-80`, `routes/user_routes.py:171-180`, `routes/report_routes.py:33-43,132-136`
- **Descrição:** a regra "task atrasada" (existe `due_date` no passado e status não é done/cancelled) é escrita manualmente 4 vezes em vez de reaproveitar `Task.is_overdue()`.
- **Impacto:** viola a responsabilidade de Controller/View do MVC (rotas fazendo cálculo de domínio) e cria risco real de a regra divergir silenciosamente entre os 4 pontos se alguém corrigir só um.

### [MEDIUM] Camada de serviço morta / nunca conectada
- **Arquivo:** `services/notification_service.py`
- **Descrição:** `NotificationService` (envio de e-mail ao atribuir/atrasar task) não é importado nem chamado por nenhuma rota.
- **Impacto:** funcionalidade aparentemente pronta mas nunca exercitada — indica integração incompleta e é código morto que engana quem lê a estrutura de pastas achando que a feature existe.
- **Validado em execução:** criei uma task atribuída a um usuário e nenhum log de "Email enviado para..." apareceu — o serviço nunca é acionado.

### [MEDIUM] Ausência de paginação
- **Arquivo:** `routes/task_routes.py:11-14`, `routes/user_routes.py:10-12`, `routes/report_routes.py:12-101`
- **Descrição:** listagens e relatórios varrem a tabela inteira.
- **Impacto:** mesmo problema de performance dos outros dois projetos, aqui agravado pelo relatório que já é O(n²) por causa do N+1 acima.

### [LOW] `print()` como logging
- **Arquivo:** `routes/task_routes.py`, `routes/user_routes.py`, `services/notification_service.py`
- **Descrição:** uso de `print()` em vez de `logging`.
- **Impacto:** mesmo padrão recorrente nos 3 projetos — sem níveis, sem estrutura.

### [LOW] Imports não utilizados
- **Arquivo:** `routes/task_routes.py:7` (`json, os, sys, time`), `app.py:7` (`sys, json`)
- **Descrição:** módulos importados e nunca referenciados.
- **Impacto:** ruído que dificulta entender as dependências reais de cada arquivo.
</details>

## 1.4 Observação transversal

Apesar de stacks e níveis de organização diferentes, os 3 projetos convergem para os mesmos grupos de problema, o que moldou diretamente o catálogo de anti-patterns da skill:

- **Segredos e criptografia:** todos os 3 têm segredo/`SECRET_KEY` hardcoded; 2 dos 3 (`code-smells-project`, `ecommerce-api-legacy`) têm senha em texto plano ou hash quebrado/reversível, e o `task-manager-api` usa MD5 sem salt — a mesma classe de falha (AP-03) em 3 implementações diferentes.
- **Vazamento de dado sensível via serialização:** os 3 projetos devolvem senha (plana ou hash) em pelo menos um endpoint de resposta.
- **Ausência total ou parcial de separação de camadas:** `code-smells-project` e `ecommerce-api-legacy` são monolíticos (God Class/God Module); `task-manager-api` já tem pastas `models/routes/services/utils`, mas a disciplina de responsabilidade por camada não é seguida — a regra de negócio vaza para as rotas do mesmo jeito.
- **Performance:** N+1 e ausência de paginação aparecem nos 3 projetos, sempre em endpoints de listagem/relatório.
- **Observabilidade:** os 3 usam `print()`/`console.log` como logging.

Essa repetição é o motivo pelo qual o catálogo de anti-patterns ([seção 2 do README](../README.md#2-construção-da-skill)) foi desenhado como uma lista de sinais de detecção agnósticos de linguagem, e não como regras específicas de Flask ou Express: o mesmo `AP-01` (SQL Injection) precisa reconhecer tanto `"...WHERE id = " + str(id)` em Python quanto template literals em JavaScript.
