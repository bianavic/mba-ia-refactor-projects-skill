# Criação de Skills — Refatoração Arquitetural Automatizada

## Índice

- [1. Visão Geral](#1-visão-geral)
- [2. Análise Manual](#2-análise-manual)
  - [2.1 code-smells-project](#21-code-smells-project)
  - [2.2 ecommerce-api-legacy](#22-ecommerce-api-legacy)
  - [2.3 task-manager-api](#23-task-manager-api)
  - [2.4 Observação transversal](#24-observação-transversal)
- [3. Construção da Skill](#3-construção-da-skill)
  - [3.1 Objetivo da Skill](#31-objetivo-da-skill)
  - [3.2 Estrutura da Skill](#32-estrutura-da-skill)
  - [3.3 SKILL.md](#33-skillmd)
  - [3.4 Arquivos de Referência](#34-arquivos-de-referência)
  - [3.5 Catálogo de Anti-patterns](#35-catálogo-de-anti-patterns)
  - [3.6 Estratégia Agnóstica de Tecnologia](#36-estratégia-agnóstica-de-tecnologia)
  - [3.7 Fluxo de Execução](#37-fluxo-de-execução)
  - [3.8 Desafios e Soluções](#38-desafios-e-soluções)
- [4. Como Executar](#4-como-executar)
  - [4.1 Pré-requisitos](#41-pré-requisitos)
  - [4.2 Projeto 1 — code-smells-project](#42-projeto-1--code-smells-project)
  - [4.3 Projeto 2 — ecommerce-api-legacy](#43-projeto-2--ecommerce-api-legacy)
  - [4.4 Projeto 3 — task-manager-api](#44-projeto-3--task-manager-api)
  - [4.5 Validação](#45-validação)
  - [4.6 Evidências de Execução](#46-evidências-de-execução)
- [5. Resultados](#5-resultados)
  - [5.1 Resumo das Auditorias](#51-resumo-das-auditorias)
  - [5.2 code-smells-project](#52-code-smells-project)
  - [5.3 ecommerce-api-legacy](#53-ecommerce-api-legacy)
  - [5.4 task-manager-api](#54-task-manager-api)
  - [5.5 Comparação Antes e Depois](#55-comparação-antes-e-depois)
  - [5.6 Comportamento entre Diferentes Stacks](#56-comportamento-entre-diferentes-stacks)
  - [5.7 Checklist de Validação Preenchido](#57-checklist-de-validação-preenchido)
  - [5.8 Bug Encontrado Após a Entrega](#58-bug-encontrado-após-a-entrega)
  - [5.9 Re-auditoria do code-smells-project](#59-re-auditoria-do-code-smells-project)
- [6. Estrutura Final do Projeto](#6-estrutura-final-do-projeto)
- [7. Referências](#7-referências)
- [8. Instruções Originais do Desafio](#8-instruções-originais-do-desafio)
  - [8.1 Objetivo](#81-objetivo)
  - [8.2 Contexto](#82-contexto)
  - [8.3 Tecnologias Obrigatórias](#83-tecnologias-obrigatórias)
  - [8.4 Requisitos](#84-requisitos)
  - [8.5 Entregável](#85-entregável)
  - [8.6 Estrutura do Repositório](#86-estrutura-do-repositório)
  - [8.7 Critérios de Aceite](#87-critérios-de-aceite)
  - [8.8 Dicas Finais](#88-dicas-finais)

## 1. Visão Geral
Ao longo do curso você aprendeu o que são Skills e como elas permitem que um agente de IA atue como um especialista em tarefas específicas. Agora imagine o seguinte cenário: você herdou 3 projetos legados com problemas de arquitetura, segurança e qualidade de código. Revisar e corrigir tudo manualmente levaria dias.

Neste desafio, você vai criar uma Skill que automatiza esse processo — analisando, auditando e refatorando qualquer projeto para o padrão MVC, independente da tecnologia.

## 2. Análise Manual

### 2.1 code-smells-project
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

#### [CRITICAL] SQL Injection generalizada
- **Arquivo:** `models.py:28,47-50,58-61,68,92,110,127-129,140,148-151,155,158-161,164-166,174,188,192,220,224,279-281,290-297`
- **Descrição:** praticamente todas as queries são montadas por concatenação de string (`"... WHERE id = " + str(id)`, `"VALUES ('" + nome + "', ...)"`), sem parâmetros preparados.
- **Impacto:** qualquer campo controlado pelo cliente (id, nome, email, termo de busca) permite injeção de SQL arbitrária — leitura, alteração ou destruição de dados. É o problema de maior impacto do projeto.
- **Validado em execução:** confirmado via `POST /admin/query` (achado abaixo), que expôs `SELECT nome, senha FROM usuarios` sem qualquer filtro.

#### [CRITICAL] Credenciais e segredo de aplicação hardcoded, e vazados em resposta
- **Arquivo:** `app.py:7-8`; `controllers.py:285-289`
- **Descrição:** `SECRET_KEY` fixo no código-fonte, `DEBUG=True` em produção, e o endpoint `/health` retorna `secret_key` e `debug` no corpo JSON da resposta.
- **Impacto:** o segredo usado para assinar sessões/tokens fica público no repositório *e* na própria API — invalida qualquer garantia de integridade de sessão.
- **Validado em execução:** `curl /health` retornou `"debug":true,"secret_key":"minha-chave-super-secreta-123"` no corpo da resposta.

#### [HIGH] God Class / ausência total de separação MVC
- **Arquivo:** `models.py` (1 arquivo, todos os domínios) + `controllers.py` (mistura roteamento, validação e "regras de negócio")
- **Descrição:** os 4 domínios (produtos, usuários, pedidos, itens) inteiros vivem em `models.py`; `controllers.py` mistura parsing de request, validação, SQL e simulação de envio de email/SMS/push (`controllers.py:208-210`).
- **Impacto:** impossível testar qualquer regra isoladamente; qualquer alteração em um domínio arrisca quebrar os outros três que compartilham o mesmo arquivo.

#### [MEDIUM] Queries N+1 no histórico de pedidos
- **Arquivo:** `models.py:171-233` (`get_pedidos_usuario`, `get_todos_pedidos`)
- **Descrição:** para cada pedido é aberto um cursor para buscar itens, e para cada item outro cursor para buscar o nome do produto — dentro de loops aninhados.
- **Impacto:** degrada rapidamente com o crescimento da base de pedidos; uma única listagem pode disparar dezenas de queries.

#### [MEDIUM] Ausência de paginação nas listagens
- **Arquivo:** `controllers.py:5-12,128-134,229-235`
- **Descrição:** `/produtos`, `/usuarios` e `/pedidos` retornam a tabela inteira sem `limit`/`offset`.
- **Impacto:** gargalo de performance e de payload à medida que a base cresce.

#### [LOW] `print()` como mecanismo de log
- **Arquivo:** `controllers.py` (praticamente todas as funções), `app.py:56,83-86`
- **Descrição:** uso de `print()` em vez do módulo `logging`.
- **Impacto:** sem níveis, sem estrutura, sem rotação — inviável em produção.

#### [LOW] Lista de categorias válidas hardcoded inline
- **Arquivo:** `controllers.py:52`
- **Descrição:** `categorias_validas = ["informatica", "moveis", ...]` embutida na função de criação.
- **Impacto:** qualquer nova categoria exige alterar código-fonte; deveria vir de configuração ou tabela.

</details>

### 2.2 ecommerce-api-legacy
| | |
|---|---|
| **Stack** | Node.js + Express 4.18.2, SQLite (`sqlite3`) |
| **Domínio** | LMS — E-learning (usuários, cursos, matrículas, pagamentos, auditoria) |
| **Arquivos** | 3 (`src/app.js`, `src/AppManager.js`, `src/utils.js`), ~180 linhas, sem separação de camadas |
| **Resumo** | CRITICAL: 2 · HIGH: 1 · MEDIUM: 2 · LOW: 2 — **Total: 7** ||

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

#### [CRITICAL] Segredos de produção hardcoded
- **Arquivo:** `utils.js:2-6`
- **Descrição:** `dbPass`, `paymentGatewayKey` (formato `pk_live_...`) e `smtpUser` estão fixos no código-fonte.
- **Impacto:** uma chave de gateway de pagamento "live" vazada no repositório é um incidente de segurança imediato, não hipotético.
- **Validado em execução:** o log do processo imprime a chave `pk_live_1234567890abcdef` a cada checkout.

#### [CRITICAL] Hashing de senha falso/quebrado
- **Arquivo:** `utils.js:17-23` (`badCrypto`), usado em `AppManager.js:68`
- **Descrição:** "hash" é apenas base64 do texto repetido 10.000 vezes e truncado — não é uma função de derivação de chave, é trivialmente reversível.
- **Impacto:** equivale a armazenar a senha em claro com um verniz cosmético; qualquer vazamento de dados expõe todas as credenciais.

#### [HIGH] God Class
- **Arquivo:** `AppManager.js:1-142`
- **Descrição:** uma única classe cria o schema, faz seed, define todas as rotas e executa a "lógica de pagamento", sem nenhuma camada intermediária.
- **Impacto:** corresponde exatamente ao exemplo de CRITICAL/HIGH do enunciado — arquitetura, roteamento e regra de negócio no mesmo lugar, impossível de testar em isolamento.

#### [MEDIUM] N+1 em cascata de callbacks no relatório financeiro
- **Arquivo:** `AppManager.js:80-129`
- **Descrição:** para cada curso é feita uma query de matrículas; para cada matrícula, uma de usuário e outra de pagamento — tudo aninhado em callbacks.
- **Impacto:** o tempo de resposta cresce multiplicativamente com o número de cursos × matrículas; também é a origem do "callback hell" que dificulta leitura e manutenção.

#### [MEDIUM] Estado mutável global no módulo utils
- **Arquivo:** `utils.js:9-10`
- **Descrição:** `globalCache` e `totalRevenue` são variáveis de módulo compartilhadas; `totalRevenue` sequer é atualizado em lugar algum.
- **Impacto:** estado global mutável em runtime concorrente (Node/Express) é fonte clássica de race conditions e comportamento não determinístico.

#### [LOW] `console.log` como logging
- **Arquivo:** `utils.js:13`, `AppManager.js:45`
- **Descrição:** sem structured logging, sem níveis.
- **Impacto:** mesma limitação do projeto 1 — inviável operar em produção.

#### [LOW] Mistura de idiomas inconsistente
- **Arquivo:** `AppManager.js` (mensagens em pt-BR, identificadores em inglês)
- **Descrição:** sem convenção única de idioma no código.
- **Impacto:** problema de padronização/manutenibilidade, não funcional.

</details>

### 2.3 task-manager-api
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

#### [CRITICAL] Hashing de senha fraco e sem salt
- **Arquivo:** `models/user.py:27-31`
- **Descrição:** `set_password`/`check_password` usam `hashlib.md5` puro, sem salt.
- **Impacto:** MD5 é criptograficamente quebrado e, sem salt, é trivial atacar com rainbow tables — mesma classe de falha dos outros dois projetos.
- **Validado em execução:** o hash retornado pela API bateu exatamente com `hashlib.md5('1234')` calculado localmente.

#### [CRITICAL] Hash de senha vazado em toda resposta de API
- **Arquivo:** `models/user.py:16-25` (`to_dict`), servido em `routes/user_routes.py:85-86,129,209`
- **Descrição:** `to_dict()` inclui o campo `password` (o hash) e é usado em `POST /users`, `PUT /users/<id>` e `POST /login`.
- **Impacto:** mesmo sendo "só" o hash, expõe material sensível desnecessariamente a qualquer cliente — combinado com o MD5 acima, facilita ataque offline.
- **Validado em execução:** `GET /users/1` e `POST /login` devolveram o campo `"password"` com o hash em claro no JSON.

#### [HIGH] Regra de negócio duplicada dentro das rotas em vez de centralizada
- **Arquivo:** `models/task.py:50-60` (`is_overdue`), reimplementada em `routes/task_routes.py:30-39,71-80`, `routes/user_routes.py:171-180`, `routes/report_routes.py:33-43,132-136`
- **Descrição:** a regra "task atrasada" (existe `due_date` no passado e status não é done/cancelled) é escrita manualmente 4 vezes em vez de reaproveitar `Task.is_overdue()`.
- **Impacto:** viola a responsabilidade de Controller/View do MVC (rotas fazendo cálculo de domínio) e cria risco real de a regra divergir silenciosamente entre os 4 pontos se alguém corrigir só um.

#### [MEDIUM] Camada de serviço morta / nunca conectada
- **Arquivo:** `services/notification_service.py`
- **Descrição:** `NotificationService` (envio de e-mail ao atribuir/atrasar task) não é importado nem chamado por nenhuma rota.
- **Impacto:** funcionalidade aparentemente pronta mas nunca exercitada — indica integração incompleta e é código morto que engana quem lê a estrutura de pastas achando que a feature existe.
- **Validado em execução:** criei uma task atribuída a um usuário e nenhum log de "Email enviado para..." apareceu — o serviço nunca é acionado.

#### [MEDIUM] Ausência de paginação
- **Arquivo:** `routes/task_routes.py:11-14`, `routes/user_routes.py:10-12`, `routes/report_routes.py:12-101`
- **Descrição:** listagens e relatórios varrem a tabela inteira.
- **Impacto:** mesmo problema de performance dos outros dois projetos, aqui agravado pelo relatório que já é O(n²) por causa do N+1 acima.

#### [LOW] `print()` como logging
- **Arquivo:** `routes/task_routes.py`, `routes/user_routes.py`, `services/notification_service.py`
- **Descrição:** uso de `print()` em vez de `logging`.
- **Impacto:** mesmo padrão recorrente nos 3 projetos — sem níveis, sem estrutura.

#### [LOW] Imports não utilizados
- **Arquivo:** `routes/task_routes.py:7` (`json, os, sys, time`), `app.py:7` (`sys, json`)
- **Descrição:** módulos importados e nunca referenciados.
- **Impacto:** ruído que dificulta entender as dependências reais de cada arquivo.
</details>

### 2.4 Observação transversal

Apesar de stacks e níveis de organização diferentes, os 3 projetos convergem para os mesmos grupos de problema, o que moldou diretamente o catálogo de anti-patterns da skill:

- **Segredos e criptografia:** todos os 3 têm segredo/`SECRET_KEY` hardcoded; 2 dos 3 (`code-smells-project`, `ecommerce-api-legacy`) têm senha em texto plano ou hash quebrado/reversível, e o `task-manager-api` usa MD5 sem salt — a mesma classe de falha (AP-03) em 3 implementações diferentes.
- **Vazamento de dado sensível via serialização:** os 3 projetos devolvem senha (plana ou hash) em pelo menos um endpoint de resposta.
- **Ausência total ou parcial de separação de camadas:** `code-smells-project` e `ecommerce-api-legacy` são monolíticos (God Class/God Module); `task-manager-api` já tem pastas `models/routes/services/utils`, mas a disciplina de responsabilidade por camada não é seguida — a regra de negócio vaza para as rotas do mesmo jeito.
- **Performance:** N+1 e ausência de paginação aparecem nos 3 projetos, sempre em endpoints de listagem/relatório.
- **Observabilidade:** os 3 usam `print()`/`console.log` como logging.

Essa repetição é o motivo pelo qual o catálogo de anti-patterns (seção 3.5) foi desenhado como uma lista de sinais de detecção agnósticos de linguagem, e não como regras específicas de Flask ou Express: o mesmo `AP-01` (SQL Injection) precisa reconhecer tanto `"...WHERE id = " + str(id)` em Python quanto template literals em JavaScript.

## 3. Construção da Skill

### 3.1 Objetivo da Skill

A skill `refactor-arch` foi desenhada para replicar, de forma automatizada, o processo de análise manual feito na seção 2: dado qualquer projeto backend, ela deve (1) detectar a stack e a arquitetura atual sem suposições prévias, (2) auditar o código contra um catálogo de anti-patterns e gerar um relatório estruturado, pausando para confirmação humana, e (3) refatorar o projeto para MVC preservando 100% do comportamento observável (endpoints, formatos de resposta, exceto correções de segurança intencionais como redação de senha).

### 3.2 Estrutura da Skill

```
.claude/skills/refactor-arch/
├── SKILL.md                                # visão geral + fluxo das 3 fases (carregado sempre)
└── references/                             # carregados sob demanda, por fase
    ├── project-analysis.md                 # Fase 1
    ├── anti-patterns-catalog.md            # Fase 2
    ├── audit-report-template.md            # Fase 2
    ├── architecture-guidelines.md          # Fase 3
    └── refactoring-playbook.md             # Fase 3
```

O design segue o princípio de *progressive disclosure*: o `SKILL.md` funciona como um índice/prompt enxuto (frontmatter + fluxo), e cada arquivo de referência só é lido quando a fase correspondente começa — a Fase 1 nunca precisa carregar o playbook de refatoração, por exemplo. Isso mantém o contexto necessário em cada etapa proporcional ao que ela realmente exige.

### 3.3 SKILL.md

O `SKILL.md` (código-fonte completo em [`code-smells-project/.claude/skills/refactor-arch/SKILL.md`](code-smells-project/.claude/skills/refactor-arch/SKILL.md)) contém:

- **Frontmatter** com `name: refactor-arch` (fixo, exigido pelo enunciado) e uma `description` em inglês escrita para casar com a forma como o usuário pediria a tarefa ("analyze, audit, or refactor a project's architecture"), já que a invocação da skill é dirigida pela similaridade entre a descrição e o pedido do usuário.
- A **escala de severidade** (CRITICAL/HIGH/MEDIUM/LOW), resumida no próprio `SKILL.md` e detalhada nos sinais de detecção em `anti-patterns-catalog.md`.
- O **fluxo das 3 fases**, cada uma com um formato de saída fixo (blocos `================================`) para garantir que o output seja parseável e consistente independentemente do projeto.
- Uma seção final de **"Non-negotiable rules"**: nunca modificar arquivo antes da confirmação da Fase 2; todo finding deve citar arquivo/linha reais (nunca "chutar"); nunca assumir Python/Flask; preservar comportamento observável; nunca reportar sucesso da Fase 3 com uma regressão conhecida.

### 3.4 Arquivos de Referência

| Arquivo | Fase | Área de conhecimento (seção 8.4) | Conteúdo |
|---|---|---|---|
| `project-analysis.md` | 1 | Análise de projeto | Heurísticas de detecção de linguagem (extensões/manifests), framework, banco de dados, domínio e classificação da arquitetura atual (monolítica / parcialmente em camadas / já em MVC) |
| `anti-patterns-catalog.md` | 2 | Catálogo de anti-patterns | 16 anti-patterns (AP-01–AP-16) com sinais de detecção agnósticos de linguagem, distribuídos nas 4 severidades, incluindo detecção de APIs deprecated |
| `audit-report-template.md` | 2 | Template de relatório | Formato exato do `ARCHITECTURE AUDIT REPORT` (cabeçalho, `## Summary`, `## Findings` ordenados por severidade, regras de preenchimento) |
| `architecture-guidelines.md` | 3 | Guidelines de arquitetura | Responsabilidades de Models/Views-Routes/Controllers, camadas de suporte opcionais (config, services, middlewares, entry point), layouts por stack (Flask, Express) e regra para projetos parcialmente em camadas |
| `refactoring-playbook.md` | 3 | Playbook de refatoração | 15 padrões de transformação (RP-01–RP-15, acima do mínimo de 8 exigido pela seção 8.4) com exemplos antes/depois em Python e Node.js, cada um referenciando o(s) AP-xx que resolve |

Cada finding do relatório de Fase 2 referencia um `AP-xx`, e cada `AP-xx` do catálogo é referenciado por um ou mais `RP-xx` do playbook — esse mapeamento cruzado é o que permite à Fase 3 decidir mecanicamente qual transformação aplicar a partir do próprio relatório da Fase 2, em vez de reinventar a correção a cada execução.

### 3.5 Catálogo de Anti-patterns

O catálogo tem 16 entradas (acima do mínimo de 8 exigido pela seção 8.4, "Requisitos da skill"), distribuídas assim:

- **CRITICAL (4):** AP-01 SQL Injection, AP-02 Segredos/credenciais hardcoded, AP-03 Hashing de senha quebrado/falso, AP-04 Dado sensível vazado via serialização.
- **HIGH (4):** AP-05 God Class, AP-06 Lógica de negócio duplicada, AP-07 Estado mutável global, AP-16 Persistência/ORM chamada direto na rota.
- **MEDIUM (4):** AP-08 N+1, AP-09 Ausência de paginação, AP-10 Camada de código morta/desconectada, AP-11 Uso de API deprecated.
- **LOW (4):** AP-12 Logging via print/console, AP-13 Configuração/valores mágicos hardcoded, AP-14 Imports não utilizados, AP-15 Idioma/nomenclatura inconsistente.

Os 15 primeiros foram escolhidos porque apareceram, na prática, em pelo menos um dos 3 projetos durante a análise manual (seção 2) — nenhum é hipotético. O AP-16 entrou depois, pelo mesmo critério e pelo motivo oposto: ele descreve um problema real que ficou no `task-manager-api` e atravessou a auditoria justamente por não estar catalogado ([seção 5.8](#58-bug-encontrado-após-a-entrega)). A detecção de API deprecated (AP-11) foi incluída como sua própria categoria (e não apenas um exemplo dentro de outra) porque o enunciado exige isso explicitamente; ela cobre tanto Python (`datetime.utcnow()`, `imp`, `flask.ext.*`) quanto Node.js (`new Buffer()`, `crypto.createCipher`), e foi validada na prática no `task-manager-api`, que usa `datetime.utcnow()` em 18 pontos do código.

### 3.6 Estratégia Agnóstica de Tecnologia

Três decisões de design garantem que a skill funcione igualmente bem em Python/Flask e Node.js/Express, sem hardcode de stack:

1. **Detecção, nunca suposição.** `project-analysis.md` define sinais por linguagem (manifests, extensões, imports no entry point) e instrui a Fase 1 a inferir a stack a cada execução — o `SKILL.md` reforça isso explicitamente na lista de "Non-negotiable rules" ("Do not assume Python/Flask: detect the stack fresh for every project this skill runs against").
2. **Sinais de detecção descritos por padrão, não por sintaxe de uma linguagem.** Cada `AP-xx` descreve o *padrão* (ex: "query montada por concatenação de string com valor controlado pelo cliente") e cita exemplos equivalentes nas duas linguagens, em vez de regex específico de uma stack.
3. **Playbook com exemplo antes/depois nas duas linguagens quando aplicável**, e instrução explícita para aplicar "o mesmo princípio" quando a stack real não corresponder a nenhum dos exemplos — cobrindo qualquer quarta linguagem que venha a ser usada no futuro.

A prova concreta dessa estratégia é a própria execução nos 3 projetos: a mesma skill, copiada sem alteração de `code-smells-project/` para `ecommerce-api-legacy/` (Node.js) e `task-manager-api/` (Python, mas parcialmente em camadas), produziu relatórios e refatorações corretos nas 3 stacks/níveis de organização (seção 5).

### 3.7 Fluxo de Execução

1. **Fase 1 — Análise:** lê `project-analysis.md`, detecta linguagem/framework/dependências/domínio/arquitetura, e imprime o bloco `PHASE 1: PROJECT ANALYSIS` no formato fixo definido no `SKILL.md`.
2. **Fase 2 — Auditoria:** lê `anti-patterns-catalog.md` e `audit-report-template.md`, varre cada arquivo-fonte identificado na Fase 1 contra os 15 `AP-xx`, exige no mínimo 5 findings (≥1 CRITICAL/HIGH, ≥2 MEDIUM, ≥2 LOW) com arquivo/linha reais, ordena por severidade e imprime o `ARCHITECTURE AUDIT REPORT`. Em seguida **para e pede confirmação explícita** — nenhum arquivo é tocado antes do `y`/`yes`/`proceed` do usuário.
3. **Fase 3 — Refatoração:** só começa após a confirmação; lê `architecture-guidelines.md` e `refactoring-playbook.md`, projeta o layout MVC adequado à stack detectada (adaptando, não reconstruindo, quando já existe alguma camada), aplica o `RP-xx` correspondente a cada finding confirmado, e valida o resultado (boot da aplicação + endpoints originais respondendo) antes de imprimir o bloco `PHASE 3: REFACTORING COMPLETE`.

### 3.8 Desafios e Soluções

- **Risco de finding fabricado ("alucinação" de linha/arquivo):** a regra mais repetida em todo o conjunto de arquivos é "nunca reportar um finding sem arquivo/linha real — reabra o arquivo se não tiver certeza". Isso foi reforçado tanto no catálogo quanto nas "Non-negotiable rules" do `SKILL.md`, e na prática os 3 relatórios em `reports/` citam ranges de linha específicos e verificáveis.
- **Projeto parcialmente em camadas (`task-manager-api`) exigindo tratamento diferente de um monolito:** um projeto que já tem `models/routes/services/utils` não deve ser reconstruído do zero — só as responsabilidades erradas dentro de cada camada precisam ser corrigidas. `architecture-guidelines.md` trata esse caso como uma categoria própria ("Partially-layered projects"), instruindo a manter os nomes de pasta existentes e apenas mover a lógica para o lugar certo — foi exatamente o que aconteceu na Fase 3 desse projeto: nenhuma camada existente foi renomeada ou reconstruída — só `config/` e `services/report_service.py` foram criados, o resto foram ajustes internos nos arquivos existentes (ver seção 5.5).
- **Preservar comportamento observável mesmo corrigindo falhas de segurança:** redigir o hash de senha da resposta de `/login` ou de `/users` é, por definição, uma mudança de response shape — mas é uma mudança *desejada*. A solução foi documentar essa exceção explicitamente em `architecture-guidelines.md` ("No endpoint may change its response shape except to redact a previously-leaked sensitive field").
- **Nomear o arquivo de template do relatório:** optou-se por `audit-report-template.md` (em vez de `report-template.md`) para deixar explícito, só pelo nome, que o arquivo é o template do relatório de *auditoria* da Fase 2 e não de qualquer outro tipo de relatório que a skill possa vir a gerar.
- **Tornar a Fase 3 mecânica e não ad hoc:** sem um mapeamento entre finding e correção, a Fase 3 dependeria de o agente "lembrar" a correção certa a cada execução. O esquema de IDs cruzados `AP-xx ↔ RP-xx` (seção 3.4) resolve isso: a Fase 3 lê a `Recommendation` de cada finding confirmado e aplica o `RP-xx` citado, o que tornou a refatoração consistente nas 3 execuções reais.

## 4. Como Executar

### 4.1 Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado e autenticado (`claude --version`).
- Repositório clonado localmente, com os 3 projetos em `code-smells-project/`, `ecommerce-api-legacy/` e `task-manager-api/`.
- Para os projetos Python (`code-smells-project`, `task-manager-api`): Python 3.10+ e as dependências de `requirements.txt` instaladas em um virtualenv (`pip install -r requirements.txt`).
- Para o projeto Node.js (`ecommerce-api-legacy`): Node.js 18+ e `npm install`.
- A skill já está presente em `.claude/skills/refactor-arch/` dentro de cada um dos 3 projetos (copiada de `code-smells-project/` para os outros dois, conforme exigido na seção 8.4.3).

> **Nota sobre a ferramenta de IA:** este projeto foi construído e testado com o Claude Code, que é a ferramenta recomendada — a skill `refactor-arch` já vem pronta no formato dele (`.claude/skills/refactor-arch/SKILL.md` + `references/`).
>
> Você pode usar outra ferramenta agêntica se preferir (Gemini CLI, OpenAI Codex — as duas alternativas aceitas pelo enunciado, seção 8.3). Atenção: a skill deste repositório é específica do formato do Claude Code. Se optar por outra ferramenta, é responsabilidade sua portar `SKILL.md` para o mecanismo equivalente dela (custom command, extensão, ou, na ausência de um equivalente direto, conduzir manualmente o mesmo fluxo de 3 fases a partir do conteúdo de `references/`) antes de começar.
>
> Consulte sempre a documentação oficial da ferramenta escolhida para os nomes corretos de arquivos, pastas e comandos de invocação. Independentemente da ferramenta, o fluxo (Análise → Auditoria → Refatoração) e os artefatos entregues — relatórios em `reports/`, código refatorado, `README.md` — são os mesmos descritos neste documento: só a máquina muda. A escolha da ferramenta não altera os [Critérios de Aceite](#87-critérios-de-aceite).

> **Nota:** a Fase 2 da skill apenas imprime o relatório no terminal — o `SKILL.md` não grava nenhum arquivo por conta própria. Salvar essa saída em `reports/audit-project-N.md` é um passo manual feito após cada execução, conforme pedido no próprio enunciado (seção 8.4.3), e não uma ação disparada automaticamente pelo agente.

> **Nota:** `pip install -r requirements.txt` (projetos Python) e `npm install` (projeto Node.js) são pré-requisitos manuais, executados uma única vez antes do primeiro `claude "/refactor-arch"` em cada projeto — a skill não instala dependências por conta própria, apenas analisa e refatora código já executável. Sem esse passo, tanto a Fase 2 (se o agente tentar rodar a aplicação para inspecioná-la) quanto a validação da Fase 3 (`python app.py` / `node src/app.js` + `curl`) falham com erro de módulo/pacote não encontrado.

### 4.2 Projeto 1 — code-smells-project

```bash
cd code-smells-project
pip install -r requirements.txt
claude "/refactor-arch"
```

Confirme a Fase 2 com `y` para prosseguir com a refatoração. O relatório desta execução está salvo em [`reports/audit-project-1.md`](reports/audit-project-1.md).

### 4.3 Projeto 2 — ecommerce-api-legacy

```bash
cd ecommerce-api-legacy
npm install
claude "/refactor-arch"
```

Relatório salvo em [`reports/audit-project-2.md`](reports/audit-project-2.md).

### 4.4 Projeto 3 — task-manager-api

```bash
cd task-manager-api
pip install -r requirements.txt/btw
claude "/refactor-arch"
```

Relatório salvo em [`reports/audit-project-3.md`](reports/audit-project-3.md).

### 4.5 Validação

Após a Fase 3 de cada projeto, a validação seguiu o checklist da seção 8.4 — **preenchido projeto a projeto na [seção 5.7](#57-checklist-de-validação-preenchido)**: inicializar a aplicação (`python app.py` ou `node src/app.js`) e exercitar cada endpoint original com `curl` (ou o arquivo `api.http` do `ecommerce-api-legacy`), comparando o status/response shape com o comportamento pré-refatoração — a única mudança de shape esperada é a remoção do campo de senha/hash das respostas que antes o vazavam.

Cada projeto tem um `manual-tests.sh` na sua própria pasta, cobrindo todos os endpoints reais (sucesso, validação, 404/409, e os casos de segurança citados no respectivo relatório de auditoria — ex.: tentativa de SQL injection no login do `code-smells-project`, gate do `ADMIN_TOKEN`): [`code-smells-project/manual-tests.sh`](code-smells-project/manual-tests.sh), [`ecommerce-api-legacy/manual-tests.sh`](ecommerce-api-legacy/manual-tests.sh), [`task-manager-api/manual-tests.sh`](task-manager-api/manual-tests.sh).

Cada projeto tem também um `arch-check.sh` na mesma pasta, que valida a estrutura em vez do comportamento: falha se algum arquivo de rota ainda chamar a persistência diretamente (AP-16). Os dois se complementam — ver [seção 5.8](#58-bug-encontrado-após-a-entrega): [`code-smells-project/arch-check.sh`](code-smells-project/arch-check.sh), [`ecommerce-api-legacy/arch-check.sh`](ecommerce-api-legacy/arch-check.sh), [`task-manager-api/arch-check.sh`](task-manager-api/arch-check.sh).

### 4.6 Evidências de Execução

Comandos para reproduzir localmente a validação de cada projeto e capturar evidência (boot da aplicação + o endpoint que corrige o finding CRITICAL mais grave do respectivo relatório de auditoria). `code-smells-project` e `task-manager-api` usam a mesma porta padrão (5000) — rode um projeto por vez, ou sobrescreva a porta de um deles via variável de ambiente (`PORT`/`FLASK_PORT`).

**Projeto 1 — code-smells-project (porta 5000)**

```bash
cd code-smells-project
python app.py
```
Log esperado: `Servidor iniciado em http://0.0.0.0:5000`, sem `SECRET_KEY` impresso.

![Boot do code-smells-project sem SECRET_KEY exposta](evidence/project1-boot.png)

```bash
# senha não deve mais vazar na listagem de usuários (AP-04 / RP-09)
curl -s -X POST localhost:5000/usuarios -H "Content-Type: application/json" \
  -d '{"nome":"Teste","email":"teste@ex.com","senha":"123456"}' | jq
curl -s localhost:5000/usuarios | python3 -m json.tool
# → nenhum objeto deve conter a chave "senha"
```

![Resposta de /usuarios sem o campo senha](evidence/project1-usuarios-sem-senha.png)

```bash
# endpoint admin agora bloqueado por padrão, sem ADMIN_TOKEN configurado (AP-01 / RP-01)
curl -s -X POST localhost:5000/admin/query -H "Content-Type: application/json" -d '{"sql":"SELECT 1"}'
# → 403 {"erro":"Endpoints administrativos desabilitados"}
```

![POST /admin/query bloqueado com 403](evidence/project1-admin-bloqueado.png)

**Projeto 2 — ecommerce-api-legacy (porta 3000)**

```bash
cd ecommerce-api-legacy
npm install
npm start   # ou: node src/app.js
```
Log esperado: `Frankenstein LMS rodando na porta 3000...`.

![Boot do ecommerce-api-legacy](evidence/project2-boot.png)

```bash
# checkout não deve mais imprimir o cartão em texto plano no log do servidor (AP-02 / RP-02)
curl -s -X POST localhost:3000/api/checkout -H "Content-Type: application/json" \
  -d '{"usr":"maria","eml":"maria@ex.com","pwd":"minhasenha","c_id":1,"card":"4111111111111111"}'
# → conferir no terminal do servidor: nenhum número de cartão impresso
```

![Resposta do checkout](evidence/project2-checkout-sem-cartao.png)

![Log do servidor durante o checkout, sem o número do cartão em texto plano](evidence/project2-checkout-sem-cartao-log.png)

**Projeto 3 — task-manager-api (porta 5000)**

```bash
cd task-manager-api
python seed.py   # dados de exemplo, opcional
python app.py
```

![Boot do task-manager-api](evidence/project3-boot.png)

```bash
# token de login real assinado, não mais "fake-jwt-token-<id>" (AP-02 / RP-02)
curl -s -X POST localhost:5000/login -H "Content-Type: application/json" \
  -d '{"email":"<email do seed>","password":"<senha do seed>"}' | python3 -m json.tool
```

![Login retornando token assinado real](evidence/project3-login-token.png)

```bash
# senha não deve mais vazar no detalhe de usuário (AP-04 / RP-09)
curl -s localhost:5000/users/1 | python3 -m json.tool
# → sem a chave "password"
```

![GET /users/1 sem o campo password](evidence/project3-users-sem-senha.png)

```bash
# paginação funcionando (AP-09 / RP-07)
curl -s "localhost:5000/tasks?page=1&per_page=2" | python3 -m json.tool
```

![GET /tasks paginado](evidence/project3-tasks-paginacao.png)

## 5. Resultados

### 5.1 Resumo das Auditorias

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|
| code-smells-project | 4 | 3 | 2 | 4 | **13** |
| ecommerce-api-legacy | 4 | 2 | 2 | 4 | **12** |
| task-manager-api | 4 | 2 | 4 | 4 | **14** |

Todos os 3 projetos superam o mínimo exigido (≥5 findings, ≥1 CRITICAL/HIGH, ≥2 MEDIUM, ≥2 LOW).

### 5.2 code-smells-project

Relatório completo: [`reports/audit-project-1.md`](reports/audit-project-1.md).

Principais achados e correções aplicadas na Fase 3 (commit [`1d8e0fa`](https://github.com/bianavic/mba-ia-refactor-projects-skill/commit/1d8e0fa)): SQL Injection generalizada em `models.py` → queries parametrizadas; endpoint `/admin/query` que executava SQL arbitrário sem autenticação → protegido por middleware `requer_admin`; `SECRET_KEY` hardcoded vazado via `/health` → movido para `config/settings.py` via variável de ambiente; senhas em texto plano armazenadas e devolvidas pela API → hashing + remoção do campo das respostas; conexão de banco global mutável → isolada em `models/db.py`; lógica duplicada, N+1 e ausência de paginação corrigidas nos novos `controllers/` e `models/`.

### 5.3 ecommerce-api-legacy

Relatório completo: [`reports/audit-project-2.md`](reports/audit-project-2.md).

Principais achados e correções (commit [`f5c6fca`](https://github.com/bianavic/mba-ia-refactor-projects-skill/commit/f5c6fca)): segredos de produção e chave de gateway de pagamento hardcoded → `src/config/index.js` via `.env`; hashing de senha falso (base64 repetido) → `scrypt`; número de cartão logado em texto plano → mascarado no logger estruturado (`src/utils/logger.js`); `AppManager` (God Class) → dividido em `models/`, `controllers/`, `services/`, `routes/`; exclusão de usuário sem cascata → cascata explícita no model; N+1 no relatório financeiro → consultas agrupadas.

**Vulnerabilidade de dependência conhecida (fora do escopo do catálogo de anti-patterns):** `npm audit` reporta 1 vulnerabilidade moderada em `qs` (DoS via `isBuffer`, [GHSA-4mjr-xmp4-gh2g](https://github.com/advisories/GHSA-4mjr-xmp4-gh2g)) — uma categoria diferente da que a skill audita (CVE de dependência de terceiros, não anti-pattern no código-fonte do projeto), por isso não consta em `reports/audit-project-2.md`.

**Status:** não corrigido automaticamente.

`npm audit fix` não resolve a vulnerabilidade porque `express@4.22.1` declara `qs: "~6.14.0"`, restringindo a resolução à série 6.14.x. A versão corrigida (`qs@6.16.0`) só é liberada a partir do `express@5.1.0`, que relaxa essa dependência para `qs: "^6.14.0"` — mas migrar de Express 4→5 é uma mudança de versão major, fora do escopo de uma refatoração estrutural que deve preservar 100% do comportamento observável, e exigiria validação de compatibilidade própria antes de ser aplicada.

### 5.4 task-manager-api

Relatório completo: [`reports/audit-project-3.md`](reports/audit-project-3.md).

Principais achados e correções (commit [`5ef74b3`](https://github.com/bianavic/mba-ia-refactor-projects-skill/commit/5ef74b3)): hash de senha MD5 sem salt → hashing do Werkzeug; hash de senha devolvido em toda resposta de usuário → removido da serialização pública; `SECRET_KEY`/credenciais SMTP hardcoded e `debug=True` em todas as interfaces → configuração via ambiente; token de login falso (`'fake-jwt-token-' + id`) → token assinado com `itsdangerous`; regra "task atrasada" duplicada em 6 lugares → centralizada em `Task.is_overdue()`; `notification_service` morto (nunca importado, com credenciais hardcoded) → removido; N+1 nos relatórios → consultas agregadas em `services/report_service.py` (camada nova); `datetime.utcnow()` deprecated (18 ocorrências) → substituído.

### 5.5 Comparação Antes e Depois

**code-smells-project** — de 4 arquivos monolíticos para MVC completo:

```
Antes                        Depois
app.py                        app.py                       (composition root)
controllers.py                config/settings.py
models.py                     controllers/{admin,order,product,system,user}_controller.py
database.py                   models/{db,order,product,user}_model.py
                               middlewares/{auth,error_handler}.py
                               routes/routes.py
```

**ecommerce-api-legacy** — de 1 God Class para MVC completo:

```
Antes                         Depois
src/app.js                    src/app.js                   (composition root)
src/AppManager.js             src/config/index.js
src/utils.js                  src/controllers/{checkout,report,user}Controller.js
                               src/models/{auditLog,course,enrollment,payment,user}Model.js
                               src/services/{cache,paymentGateway}Service.js
                               src/middlewares/errorHandler.js
                               src/routes/index.js
                               src/utils/{crypto,logger}.js
```

**task-manager-api** — camadas já existentes, ajustadas *in place* (adições da Fase 3: `config/`, um novo service, e — no fechamento do bug da seção 5.8 — `controllers/`):

```
Antes (parcial)                        Depois
app.py                                  app.py                        (SECRET_KEY/debug via env)
models/{user,task,category}.py          models/{user,task,category}.py (hashing correto, sem duplicação)
routes/{task,user,report}_routes.py     routes/{task,user,report}_routes.py (parse → 1 chamada de controller/service → resposta)
services/notification_service.py        controllers/{task,user}_controller.py (novo — fecha o AP-16, ver 5.8)
utils/helpers.py                        config/settings.py            (novo)
                                         services/report_service.py    (novo — agregação + CRUD de categorias)
                                         middlewares/error_handler.py  (novo — ajuste pós-Fase 3, ver 5.7 nota 4)
                                         (notification_service.py removido — código morto)
```

### 5.6 Comportamento entre Diferentes Stacks

- **Python/Flask monolítico (`code-smells-project`):** a skill reconstruiu a árvore de diretórios do zero (config/models/controllers/routes/middlewares), já que não havia nenhuma separação prévia para preservar.
- **Node.js/Express monolítico (`ecommerce-api-legacy`):** mesma estratégia de reconstrução total, mas a implementação de cada camada seguiu as convenções idiomáticas de Node (callbacks/módulos CommonMark, `express.Router()`) em vez de espelhar literalmente a estrutura Python — confirmando que a detecção de stack (seção 3.6) direciona corretamente o `architecture-guidelines.md` para o bloco "Node.js / Express" em vez do bloco "Python / Flask".
- **Python/Flask parcialmente em camadas (`task-manager-api`):** a skill não recriou a estrutura de pastas — identificou corretamente que `models/routes/services/utils` já existiam e limitou a Fase 3 a mover lógica de negócio das rotas para o model/service correto, removendo apenas a camada morta (`notification_service.py`) e adicionando uma camada nova apenas onde não havia nenhuma equivalente (`report_service.py`). Esse foi o teste mais direto de que a regra "adaptar, não reconstruir" (seção 3.8) funciona na prática.
- Em todos os 3 casos, a mesma invocação (`claude "/refactor-arch"`) e o mesmo `SKILL.md` produziram um fluxo de 3 fases correto sem qualquer ajuste manual entre execuções — a única diferença entre projetos foi o conteúdo específico do relatório e da refatoração, nunca o processo.

### 5.7 Checklist de Validação Preenchido

Checklist da seção 8.4 ("Validação"), preenchido para cada projeto após a Fase 3. Cada item marcado é verificável no repositório (arquivo citado, relatório em `reports/` ou evidência em `evidence/`, seção 4.6).

**Projeto 1 — code-smells-project (Python/Flask)**

```markdown
### Fase 1 — Análise
- [x] Linguagem detectada corretamente         → Python
- [x] Framework detectado corretamente         → Flask 3.1.1 (+ flask-cors)
- [x] Domínio da aplicação descrito            → E-commerce (produtos, usuários, pedidos, itens_pedido)
- [x] Número de arquivos condiz com a realidade → 4 (app.py, controllers.py, models.py, database.py)

### Fase 2 — Auditoria
- [x] Relatório segue o template de referência  → reports/audit-project-1.md
- [x] Cada finding tem arquivo e linhas exatos  → ex.: models.py:28,47-50,109-111
- [x] Findings ordenados CRITICAL → LOW
- [x] Mínimo de 5 findings identificados        → 13 (4 CRITICAL · 3 HIGH · 2 MEDIUM · 4 LOW)
- [–] Detecção de APIs deprecated (se aplicável) → não aplicável: nenhuma API deprecated no código original
- [x] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC  → config/ models/ controllers/ routes/ middlewares/
- [x] Configuração extraída (sem hardcoded)     → config/settings.py (SECRET_KEY via env)
- [x] Models criados para abstrair dados        → models/{db,order,product,user}_model.py
- [x] Views/Routes separadas                    → routes/routes.py
- [x] Controllers concentram o fluxo            → controllers/{admin,order,product,system,user}_controller.py ⁵
- [x] Error handling centralizado               → middlewares/error_handler.py
- [x] Entry point claro                         → app.py (composition root)
- [x] Aplicação inicia sem erros                → evidence/project1-boot.png
- [x] Endpoints originais respondem             → seção 4.6 (evidence/project1-usuarios-sem-senha.png, project1-admin-bloqueado.png)
```

⁵ Na entrega original, `admin_controller.py` era exceção a este item: chamava `models.db.get_db()`/`cursor.execute()` diretamente, e o endpoint `POST /admin/query` continuava executando qualquer SQL enviado pelo cliente (a autenticação adicionada na Fase 3 cobria só a metade da recomendação original da seção 5.2). Uma segunda auditoria encontrou isso e mais 5 achados introduzidos pela própria Fase 3 — ver [seção 5.9](#59-re-auditoria-do-code-smells-project).

**Projeto 2 — ecommerce-api-legacy (Node.js/Express)**

```markdown
### Fase 1 — Análise
- [x] Linguagem detectada corretamente         → JavaScript / Node.js
- [x] Framework detectado corretamente         → Express 4.18.2
- [x] Domínio da aplicação descrito            → LMS com fluxo de checkout (cursos, matrículas, pagamentos)
- [x] Número de arquivos condiz com a realidade → 3 (src/app.js, src/AppManager.js, src/utils.js)

### Fase 2 — Auditoria
- [x] Relatório segue o template de referência  → reports/audit-project-2.md ¹
- [x] Cada finding tem arquivo e linhas exatos  → ex.: src/utils.js:2-6, src/AppManager.js:45
- [x] Findings ordenados CRITICAL → LOW
- [x] Mínimo de 5 findings identificados        → 12 (4 CRITICAL · 2 HIGH · 2 MEDIUM · 4 LOW)
- [–] Detecção de APIs deprecated (se aplicável) → não aplicável: nenhuma API deprecated no código original
- [x] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC  → src/{config,models,controllers,services,routes,middlewares,utils}
- [x] Configuração extraída (sem hardcoded)     → src/config/index.js + .env (.env.example versionado)
- [x] Models criados para abstrair dados        → src/models/{auditLog,course,enrollment,payment,user}Model.js
- [x] Views/Routes separadas                    → src/routes/index.js (express.Router)
- [x] Controllers concentram o fluxo            → src/controllers/{checkout,report,user}Controller.js
- [x] Error handling centralizado               → src/middlewares/errorHandler.js (app.use na app.js)
- [x] Entry point claro                         → src/app.js (composition root)
- [x] Aplicação inicia sem erros                → evidence/project2-boot.png
- [x] Endpoints originais respondem             → seção 4.6 + api.http (evidence/project2-checkout-sem-cartao.png e -log.png)
```

¹ O relatório do projeto 2 traz cabeçalhos extras de agrupamento (`## HIGH`, `## MEDIUM`, `## LOW`) que não existem no `audit-report-template.md` nem nos relatórios 1 e 3. É uma variação cosmética da saída daquela execução; a estrutura obrigatória (cabeçalho, `## Summary`, blocos de finding com File/Description/Impact/Recommendation, total e prompt de confirmação) está integralmente presente, e o arquivo foi mantido como a saída literal da Fase 2, sem edição posterior.

**Projeto 3 — task-manager-api (Python/Flask, parcialmente em camadas)**

```markdown
### Fase 1 — Análise
- [x] Linguagem detectada corretamente         → Python
- [x] Framework detectado corretamente         → Flask 3.0.0 + Flask-SQLAlchemy 3.1.1
- [x] Domínio da aplicação descrito            → Task Manager (tasks, users, categories, reports)
- [x] Número de arquivos condiz com a realidade → 15 arquivos .py (app.py, database.py, seed.py + models/ routes/ services/ utils/)

### Fase 2 — Auditoria
- [x] Relatório segue o template de referência  → reports/audit-project-3.md
- [x] Cada finding tem arquivo e linhas exatos  → ex.: models/user.py:27-32, routes/user_routes.py:210
- [x] Findings ordenados CRITICAL → LOW
- [x] Mínimo de 5 findings identificados        → 14 (4 CRITICAL · 2 HIGH · 4 MEDIUM · 4 LOW)
- [x] Detecção de APIs deprecated incluída      → [MEDIUM] datetime.utcnow() em 18 ocorrências
- [x] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC  → camadas existentes mantidas (models/ routes/ services/ utils/) + config/ novo ²
- [x] Configuração extraída (sem hardcoded)     → config/settings.py (SECRET_KEY, DEBUG, HOST, PORT via env)
- [x] Models criados para abstrair dados        → models/{user,task,category}.py (regra de negócio movida para cá)
- [x] Views/Routes separadas                    → routes/{task,user,report}_routes.py (blueprints)
- [x] Controllers concentram o fluxo            → controllers/{task,user}_controller.py + services/report_service.py ³
- [x] Error handling centralizado               → middlewares/error_handler.py ⁴
- [x] Entry point claro                         → app.py (registra blueprints, config e error handlers)
- [x] Aplicação inicia sem erros                → evidence/project3-boot.png
- [x] Endpoints originais respondem             → seção 4.6 (evidence/project3-login-token.png, project3-users-sem-senha.png, project3-tasks-paginacao.png)
```

² Conforme a regra "Partially-layered projects" do `architecture-guidelines.md` (seção 3.8): projeto que já tem camadas não é reconstruído do zero — a Fase 3 corrigiu as responsabilidades dentro das camadas existentes em vez de renomear pastas.

³ Na entrega original, este projeto não tinha ganhado uma pasta `controllers/` — a separação vinha só de mover a regra de negócio das rotas para `models/`/`services/`, com o blueprint ainda chamando `Task.query`/`db.session.*` diretamente (ver o bug descrito na seção 5.8). Isso foi corrigido depois: `controllers/task_controller.py` e `controllers/user_controller.py` agora concentram parse → validação → persistência para tasks e usuários, e `services/report_service.py` foi estendido para cobrir também o CRUD de categorias — os blueprints ficaram só com parse do request → uma chamada → resposta, fechando o `arch-check.sh` (seção 5.8).

⁴ Este foi o único item do checklist que a Fase 3 original não entregou: o projeto tratava erros com `try/except` repetido rota a rota, e a skill preservou esse padrão em vez de centralizá-lo. O handler central foi adicionado depois, em ajuste manual de fechamento da entrega, para alinhar o projeto 3 aos outros dois — ele converte `HTTPException` e exceções não tratadas em JSON preservando os status codes originais (404, 405, 400, 500), sem alterar nenhuma resposta já existente nas rotas.

### 5.8 Bug Encontrado Após a Entrega

**O bug.** A primeira refatoração do `task-manager-api` (commit [`5ef74b3`](https://github.com/bianavic/mba-ia-refactor-projects-skill/commit/5ef74b3)) manteve chamadas de persistência (`.query()`, `db.session.*`, `Model.get_by_id()`) direto nas rotas, mesmo já existindo `models/`, `routes/` e `services/`. O caso mais claro era `report_routes.py:16`, que chamava `User.get_by_id(user_id)` sem passar por nenhuma camada intermediária.

**Causa raiz (dupla).** O `architecture-guidelines.md` liberava explicitamente rotas com persistência inline em projetos já em camadas: a regra "Partially-layered projects" mandava não criar `controllers/` quando as rotas "já cumprem esse papel", e o critério para "já cumprem" era ausência de *duplicação* (AP-06), não ausência de acesso a dados. Como as queries eram únicas por rota, a regra deixava de ser uma permissão e virava uma proibição de criar o controller. Somado a isso, o catálogo de anti-patterns não tinha nenhuma entrada para o padrão — então a Fase 2 sequer o reportava como finding.

**Por que a validação não pegou.** A validação seguiu o checklist da seção 8.4, preenchido projeto a projeto na [seção 5.7](#57-checklist-de-validação-preenchido), e cada projeto tem um `manual-tests.sh` na sua própria pasta cobrindo todos os endpoints reais via HTTP (sucesso, validação, 404/409 e os casos de segurança citados no respectivo relatório de auditoria). Mas esses são testes de caixa-preta: a resposta HTTP de uma rota que consulta o ORM diretamente é idêntica à de uma rota que delega a um controller/service. As evidências da seção 4.6 têm a mesma limitação. O bug só apareceu em revisão externa do código.

**Correção aplicada.**

1. `architecture-guidelines.md` — a exceção foi removida: chamada de ORM/query dentro de rota é sempre violação de Views/Routes, inclusive em projeto que já tem camadas.
2. `anti-patterns-catalog.md` — criado o **AP-16 (Persistence/ORM Calls Inline in Routes)**, severidade HIGH, que cobre também finders de Model (`Model.get_by_id`, `Model.find_by_x`), não apenas ORM cru. Entrou como HIGH porque é violação forte de MVC pela escala da 8.2 — como LOW, seria detectado e despriorizado no mesmo relatório.
3. `SKILL.md` — a checagem virou passo obrigatório da Fase 3 (passo 3.6) nas 3 cópias vendorizadas da skill, para que execuções futuras não dependam nem de o catálogo citar o padrão exato nem de revisão humana. É um passo mecânico, não um julgamento da IA.
4. `refactoring-playbook.md` — criado o **RP-14 (Move persistence out of routes)**, com o antes/depois da transformação, para que a Fase 3 não tenha que reinventar a correção.
5. `arch-check.sh` — a mesma checagem mecanizada, um script por projeto, ao lado do `manual-tests.sh` de cada um: o `manual-tests.sh` prova o comportamento via HTTP, o `arch-check.sh` prova a estrutura lendo o código. Sai com código diferente de zero em qualquer ocorrência.

```bash
cd code-smells-project    && ./arch-check.sh
cd ../ecommerce-api-legacy && ./arch-check.sh
cd ../task-manager-api     && ./arch-check.sh
```

**Status.** Os 3 projetos passam. O `task-manager-api` foi o último a fechar: as rotas foram refatoradas para `controllers/task_controller.py`, `controllers/user_controller.py` e `services/report_service.py` (categorias), e `./arch-check.sh` agora retorna `PASS: no route in task-manager-api touches persistence directly.` — auditoria de acompanhamento em [`reports/audit-project-3-part2.md`](reports/audit-project-3-part2.md).

### 5.9 Re-auditoria do code-smells-project

**O que motivou.** Uma segunda execução da Fase 2 no `code-smells-project`, feita após a entrega original (seção 5.2), revisitou os 13 achados de então e encontrou que dois dos CRITICAL/HIGH tinham sido corrigidos só pela metade, além de 5 achados novos — introduzidos pela própria Fase 3, não pelo código original.

**Achados que sobreviveram parcialmente à Fase 3 original.**
1. **[CRITICAL]** `POST /admin/query` — a correção original só adicionou autenticação (`requer_admin`); qualquer chamador com o token continuava podendo executar SQL arbitrário, incluindo `DROP TABLE` ou exclusão em massa.
2. **[HIGH]** `admin_controller.py` continuava chamando `models.db.get_db()`/`cursor.execute()` diretamente — a mesma violação de "Controllers concentram o fluxo" da seção 5.7, só que movida de `app.py` (entrega original) para dentro do controller, sem nunca ter passado por um model.

**Achados novos, introduzidos pela própria Fase 3.**
3. **[HIGH]** paginação (`page`/`per_page`) reimplementada de forma idêntica em 3 controllers (`product`, `order`, `user`) em vez de um helper compartilhado.
4. **[MEDIUM]** N+1 na criação de pedidos — `order_model.criar()` buscava um produto por item em vez de uma query `IN (...)`.
5. **[MEDIUM]** `/produtos/busca` sem paginação, ao contrário de `/produtos`.
6. **[LOW]** limiares/taxas de desconto do relatório de vendas hardcoded na função.
7. **[LOW]** parâmetro `id` sobrescrevendo o builtin do Python em 3 handlers de produto.

**Por que a validação original (seção 5.7) não pegou isso.** O checklist da seção 8.4 valida uma execução da Fase 2 seguida de uma Fase 3 — não prevê uma segunda passada para confirmar que a correção resolveu o espírito da recomendação, não só a letra. O achado 1 é o mesmo tipo de lacuna descrita na seção 5.8 para o projeto 3: a recomendação original dizia "delete estes endpoints, ou proteja com autenticação **e** nunca exponha execução de SQL bruto sobre HTTP" — a Fase 3 aplicou a primeira parte e ignorou a segunda. Os achados 3-7 simplesmente não existiam na auditoria original: foram introduzidos pela refatoração (paginação nova, endpoint de busca novo), então só uma re-auditoria depois da Fase 3 poderia pegá-los.

**Correção aplicada.**
1. `models/admin_model.py` criado — `reset_database()` e `executar_query()` movidos para lá; `executar_query()` agora rejeita qualquer instrução que não comece com `SELECT`.
2. `controllers/admin_controller.py` — não importa mais `models.db`; delega tudo ao model novo.
3. `utils/pagination.py` criado com `parse_pagination()`; os 3 controllers passaram a usá-lo em vez de reimplementar o parsing.
4. `models/order_model.py` — `criar()` busca todos os produtos em uma única query `WHERE id IN (...)` em vez de uma por item.
5. `models/product_model.py` / `controllers/product_controller.py` — `buscar()` (endpoint `/produtos/busca`) ganhou `page`/`per_page`.
6. `config/settings.py` — faixas de desconto extraídas para `FAIXAS_DESCONTO_FATURAMENTO`.
7. `routes/routes.py` / `controllers/product_controller.py` — parâmetro `id` renomeado para `produto_id`.

Relatório completo da re-auditoria: [`reports/audit-project-1-part2.md`](reports/audit-project-1-part2.md).

```bash
cd code-smells-project
./arch-check.sh
# PASS: no route in code-smells-project touches persistence directly.

# SQL destrutivo agora é bloqueado mesmo com token de admin válido:
curl -s -X POST http://localhost:5000/admin/query -H "X-Admin-Token: <token>" \
  -H "Content-Type: application/json" -d '{"sql":"DROP TABLE produtos"}'
# {"erro":"Somente instruções SELECT são permitidas nesta ferramenta"}
```

**Status.** Os 7 achados fechados; `manual-tests.sh` e `arch-check.sh` passam sem regressão; nenhum endpoint (método + caminho) mudou — o único comportamento alterado foi o caminho destrutivo de `/admin/query`, que era justamente o objetivo da correção.

## 6. Estrutura Final do Projeto

```
mba-ia-refactor-projects-skill/
├── README.md
│
├── code-smells-project/                   # Projeto 1 — Python/Flask (E-commerce)
│   ├── .claude/skills/refactor-arch/      # SKILL.md + references/
│   ├── app.py                             # composition root
│   ├── config/settings.py
│   ├── controllers/
│   ├── models/
│   ├── middlewares/
│   ├── routes/
│   ├── requirements.txt
│   ├── manual-tests.sh                    # curl de validação manual (seção 4.5)
│   └── arch-check.sh                      # checagem estrutural AP-16 (seções 4.5 e 5.8)
│
├── ecommerce-api-legacy/                  # Projeto 2 — Node.js/Express (LMS)
│   ├── .claude/skills/refactor-arch/      # cópia da skill
│   ├── src/
│   │   ├── app.js                         # composition root
│   │   ├── config/
│   │   ├── controllers/
│   │   ├── models/
│   │   ├── services/
│   │   ├── middlewares/
│   │   ├── routes/
│   │   └── utils/
│   ├── package.json
│   ├── manual-tests.sh                    # curl de validação manual (seção 4.5)
│   └── arch-check.sh                      # checagem estrutural AP-16 (seções 4.5 e 5.8)
│
├── task-manager-api/                      # Projeto 3 — Python/Flask (Task Manager)
│   ├── .claude/skills/refactor-arch/      # cópia da skill
│   ├── app.py                             # composition root
│   ├── config/settings.py                 # novo
│   ├── controllers/                       # novo — task_controller.py, user_controller.py (fecha o AP-16, seção 5.8)
│   ├── middlewares/error_handler.py       # novo — handler central de erros
│   ├── models/
│   ├── routes/
│   ├── services/                          # report_service.py estendido (+ categorias); notification_service.py removido
│   ├── tests/                             # novo — pytest unitário dos controllers (task/user)
│   ├── utils/
│   ├── requirements.txt                   # inclui pytest
│   ├── manual-tests.sh                    # curl de validação manual (seção 4.5)
│   └── arch-check.sh                      # checagem estrutural AP-16 (seções 4.5 e 5.8)
│
├── reports/
│   ├── audit-project-1.md
│   ├── audit-project-2.md
│   └── audit-project-3.md
│
└── evidence/                              # screenshots citados na seção 4.6
    ├── project1-boot.png
    ├── project1-usuarios-sem-senha.png
    ├── project1-admin-bloqueado.png
    ├── project2-boot.png
    ├── project2-checkout-sem-cartao.png
    ├── project2-checkout-sem-cartao-log.png
    ├── project3-boot.png
    ├── project3-login-token.png
    ├── project3-users-sem-senha.png
    └── project3-tasks-paginacao.png
```

## 7. Referências

- [Claude Code: Skills](https://docs.anthropic.com/en/docs/claude-code/skills) — Documentação oficial sobre como criar e estruturar Skills
- [Claude Code: Overview](https://docs.anthropic.com/en/docs/claude-code/overview) — Visão geral do Claude Code e suas capacidades
- [The Complete Guide to Building Skills for Claude (PDF)](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf) — Guia completo da Anthropic sobre construção de Skills
- [Equipping Agents for the Real World with Agent Skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills) — Blog oficial da Anthropic sobre Agent Skills

---

## 8. Instruções Originais do Desafio

### 8.1 Objetivo

Você deve entregar uma Skill capaz de:

- Analisar uma codebase detectando linguagem, framework e arquitetura atual
- Identificar anti-patterns e code smells, classificando por severidade com arquivo e linha exatos
- Gerar um relatório de auditoria estruturado com todos os achados
- Refatorar o projeto para o padrão MVC (Model-View-Controller), eliminando os problemas encontrados
- Validar o resultado garantindo que a aplicação continua funcionando após as mudanças

A skill deve ser agnóstica de tecnologia, funcionando com diferentes linguagens e frameworks.

### 8.2 Contexto

#### Definição de Severidades

Para padronizar a sua auditoria e os relatórios gerados pela IA, utilize a seguinte escala de classificação baseada em problemas de MVC e SOLID:

- **CRITICAL:** Falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis (ex: credenciais hardcoded, SQL Injection) ou violam completamente a separação de responsabilidades (ex: "God Class" contendo banco de dados, lógicas complexas e roteamento no mesmo arquivo).
- **HIGH:** Fortes violações do padrão MVC ou princípios SOLID que dificultam muito a manutenção e testes (ex: lógicas de negócio pesadas presas dentro de Controllers, forte acoplamento sem Injeção de Dependência, ou uso de estado global mutável em toda a aplicação).
- **MEDIUM:** Problemas de padronização, duplicação de código ou gargalos de performance moderada (ex: Queries N+1 no banco de dados, uso inadequado de middlewares, validações ausentes nas rotas).
- **LOW:** Melhorias de legibilidade, nomenclatura de variáveis ruins, ou "magic numbers" soltos pelo código.

#### Exemplo de Uso no CLI

```bash
# Executar a skill no projeto com problemas
cd code-smells-project
claude "/refactor-arch"
```

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:      Flask 3.1.1
Dependencies:  flask-cors
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica — tudo em 4 arquivos, sem separação de camadas
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~800 lines of code

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 2 | LOW: 3

## Findings

### [CRITICAL] God Class / God Method
File: models.py:1-350
Description: Arquivo único contém toda lógica de negócio, queries SQL, validação e formatação para 4 domínios diferentes.
Impact: Impossível testar em isolamento, qualquer mudança afeta tudo.
Recommendation: Separar em models e controllers por domínio.

### [CRITICAL] Hardcoded Credentials
File: app.py:8
Description: SECRET_KEY hardcoded como 'minha-chave-super-secreta-123'
...

================================
Total: 14 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
```

```
[... refatoração executada ...]

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
src/
├── config/settings.py
├── models/
│   ├── produto_model.py
│   └── usuario_model.py
├── views/
│   └── routes.py
├── controllers/
│   ├── produto_controller.py
│   └── pedido_controller.py
├── middlewares/error_handler.py
└── app.py (composition root)

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
```

### 8.3 Tecnologias obrigatórias

- **Ferramenta:** uma das três opções abaixo (não são aceitas outras ferramentas):
  - Claude Code
  - Gemini CLI
  - OpenAI Codex
- **Recurso:** Custom Skills (ou o equivalente na ferramenta escolhida)
- **Formato dos arquivos de referência:** Markdown
- **Projetos-alvo:** Python/Flask (2 projetos) e Node.js/Express (1 projeto) (fornecidos no repositório base)

> **Nota sobre a ferramenta:** Os exemplos deste documento usam o Claude Code (`.claude/skills/`) como referência, pois é a ferramenta utilizada no curso. Se você optar por Gemini CLI ou Codex, adapte o nome da pasta e o comando de invocação conforme a convenção dela — o conceito de skill e a estrutura interna (SKILL.md + arquivos de referência) permanecem os mesmos.

### 8.4 Requisitos

#### 1. Análise Manual dos Projetos

Antes de criar a skill, você deve entender os problemas que ela vai resolver.

**Tarefas:**

- Analisar o projeto `code-smells-project/` (Python/Flask — API de E-commerce)
- Analisar o projeto `ecommerce-api-legacy/` (Node.js/Express — LMS API com fluxo de checkout)
- Analisar o projeto `task-manager-api/` (Python/Flask — API de Task Manager)

Para cada projeto, identificar e documentar no mínimo 5 problemas, incluindo pelo menos:

- 1 de severidade CRITICAL ou HIGH
- 2 de severidade MEDIUM
- 2 de severidade LOW

Documentar os achados na seção "Análise Manual" do seu `README.md`

> **Dica:** Não precisa encontrar todos os problemas — foque nos que têm maior impacto arquitetural. Use os projetos como insumo para entender quais padrões sua skill precisa detectar.

> **Por que 3 projetos?** Dois são Python/Flask (com níveis de organização diferentes) e um é Node.js/Express. Sua skill precisa funcionar nos 3 para provar que é verdadeiramente agnóstica de tecnologia — lidando tanto com código completamente desestruturado quanto com projetos que já possuem alguma separação de camadas.

#### 2. Criação da Skill

Agora que você conhece os problemas, crie uma skill que os detecte, gere um relatório de auditoria e corrija automaticamente.

**Tarefas:**

Criar a skill dentro do projeto `code-smells-project/` e implementar o SKILL.md com 3 fases sequenciais:

- **Fase 1 — Análise:** Detectar stack, mapear arquitetura atual, imprimir resumo
- **Fase 2 — Auditoria:** Cruzar código contra catálogo de anti-patterns, gerar relatório, pedir confirmação
- **Fase 3 — Refatoração:** Reestruturar para o padrão MVC, validar que funciona

Criar arquivos de referência em Markdown que forneçam à skill o conhecimento necessário para executar as 3 fases. Os arquivos devem cobrir **obrigatoriamente** as seguintes áreas de conhecimento:

| Área de conhecimento | O que deve conter |
|---|---|
| Análise de projeto | Heurísticas para detecção de linguagem, framework, banco de dados e mapeamento de arquitetura |
| Catálogo de anti-patterns | Anti-patterns com sinais de detecção e classificação de severidade |
| Template de relatório | Formato padronizado do relatório de auditoria (Fase 2) |
| Guidelines de arquitetura | Regras do padrão MVC alvo (camadas Models, Views/Routes e Controllers, responsabilidades de cada uma) |
| Playbook de refatoração | Padrões concretos de transformação para cada anti-pattern (com exemplos de código) |

> **Nota:** Você tem liberdade para organizar os arquivos de referência como preferir — pode usar os nomes e a quantidade de arquivos que fizer sentido para sua skill. O importante é que todas as 5 áreas de conhecimento estejam cobertas. O nome da skill (`refactor-arch`) e o arquivo `SKILL.md` são obrigatórios e não devem ser alterados. O path da skill segue a convenção da ferramenta escolhida (no Claude Code, por exemplo, é `.claude/skills/refactor-arch/`).

**Requisitos da skill:**

- Deve ser agnóstica de tecnologia — deve funcionar corretamente nos 3 projetos fornecidos, independente da stack ou nível de organização
- O catálogo de anti-patterns deve conter no mínimo 8 anti-patterns com severidade distribuída (CRITICAL, HIGH, MEDIUM, LOW)
- O catálogo deve incluir detecção de APIs deprecated — identificar uso de APIs obsoletas e recomendar o equivalente moderno
- O playbook deve ter no mínimo 8 padrões de transformação com exemplos de código antes/depois
- A Fase 2 deve pausar e pedir confirmação antes de modificar qualquer arquivo
- A Fase 3 deve validar o resultado (boot da aplicação + endpoints funcionando)

#### 3. Execução da Skill

Execute sua skill nos 3 projetos e valide que ela funciona em todas as stacks.

##### Projeto 1 — code-smells-project (Python/Flask)

Invocar a skill no Claude Code:

```bash
claude "/refactor-arch"
```

> **Nota:** O comando acima é o exemplo com Claude Code. Se você estiver usando Gemini CLI ou Codex, utilize o comando equivalente para invocar uma skill na sua ferramenta.

- Verificar que a Fase 1 detecta corretamente a stack e imprime o resumo
- Verificar que a Fase 2 encontra no mínimo 5 dos problemas documentados na sua análise manual
- Confirmar a execução da Fase 3
- Verificar que a Fase 3:
  - Cria a estrutura de diretórios baseada em MVC
  - A aplicação inicia sem erros
  - Os endpoints originais continuam respondendo
- Salvar o relatório de auditoria (output da Fase 2) em `reports/audit-project-1.md`
- Commitar o código refatorado do projeto no repositório

##### Projeto 2 — ecommerce-api-legacy (Node.js/Express)

Prove que sua skill é reutilizável em outro projeto de backend, mas com stack diferente.

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `ecommerce-api-legacy/`
- Invocar a skill:

```bash
cd ../ecommerce-api-legacy
claude "/refactor-arch"
```

- Verificar que as 3 fases executam corretamente neste projeto
- Salvar o relatório em `reports/audit-project-2.md`
- Commitar o código refatorado do projeto no repositório

##### Projeto 3 — task-manager-api (Python/Flask)

Agora o teste com um projeto Python/Flask que já possui alguma organização de camadas (models, routes, services, utils).

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `task-manager-api/`
- Invocar a skill:

```bash
cd ../task-manager-api
claude "/refactor-arch"
```

- Verificar que:
  - A Fase 1 detecta corretamente Python/Flask como stack e identifica o domínio de Task Manager
  - A Fase 2 identifica problemas mesmo em um projeto parcialmente organizado
  - A Fase 3 melhora a estrutura sem quebrar a aplicação (todos os endpoints devem continuar respondendo)
- Salvar o relatório em `reports/audit-project-3.md`
- Commitar o código refatorado do projeto no repositório

> **Nota:** Este projeto já possui alguma separação de camadas, mas isso não significa que a arquitetura está adequada. A skill deve identificar tanto problemas de código (segurança, performance, qualidade) quanto oportunidades de melhoria arquitetural. Se houver mudanças estruturais necessárias, a skill deve propô-las e executá-las.

##### Validação

Para cada projeto refatorado, valide o seguinte checklist:

```markdown
## Checklist de Validação

### Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade

### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente
```

> **Dica:** Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

### 8.5 Entregável

Repositório público no GitHub (fork do repositório base) contendo:

- Skill completa em `.claude/skills/refactor-arch/` (dentro dos 3 projetos)
- Código refatorado dos 3 projetos (resultado da execução da Fase 3, commitado no repositório)
- Relatórios de auditoria em `reports/` (3 arquivos)
- `README.md` atualizado

### 8.6 Estrutura do repositório

Faça um fork do repositório base contendo os três projetos com code smells.

> **Nota:** A estrutura abaixo usa Claude Code como exemplo (`.claude/skills/`). Se estiver usando outra ferramenta, adapte os caminhos conforme a convenção dela.

```
desafio-skills/
├── README.md                              # Sua documentação
│
├── code-smells-project/                   # Projeto 1 — Python/Flask (API de E-commerce)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← SUA SKILL AQUI
│   │           ├── SKILL.md
│   │           └── (arquivos de referência)
│   ├── app.py
│   ├── controllers.py
│   ├── models.py
│   ├── database.py
│   └── requirements.txt
│
├── ecommerce-api-legacy/                  # Projeto 2 — Node.js/Express (LMS API com checkout)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── src/
│   │   ├── app.js
│   │   ├── AppManager.js
│   │   └── utils.js
│   ├── api.http
│   └── package.json
│
├── task-manager-api/                      # Projeto 3 — Python/Flask (API de Task Manager)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── app.py
│   ├── database.py
│   ├── seed.py
│   ├── requirements.txt
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── utils/
│
└── reports/                               # Relatórios gerados
    ├── audit-project-1.md                 # Saída da Fase 2 no projeto 1
    ├── audit-project-2.md                 # Saída da Fase 2 no projeto 2
    └── audit-project-3.md                 # Saída da Fase 2 no projeto 3
```

**O que você vai criar:**

- `.claude/skills/refactor-arch/` — A skill completa (SKILL.md + arquivos de referência)
- Código refatorado dos 3 projetos — resultado da execução da Fase 3, commitado no repositório
- `reports/audit-project-{1,2,3}.md` — Relatório de auditoria de cada projeto
- `README.md` — Documentação do seu processo

**O que já vem pronto:**

- `code-smells-project/` — API de E-commerce Python/Flask com code smells intencionais
- `ecommerce-api-legacy/` — LMS API Node.js/Express (com fluxo de checkout) e problemas de implementação
- `task-manager-api/` — API de Task Manager Python/Flask com organização parcial e problemas de segurança/qualidade

> **Dica:** Cada projeto contém problemas intencionais de diferentes severidades (CRITICAL, HIGH, MEDIUM, LOW), incluindo falhas de segurança, violações arquiteturais e problemas de qualidade de código. Parte do desafio é identificá-los por conta própria através da análise manual do código.

#### README.md deve conter

**A) Seção "Análise Manual":**

- Lista dos problemas identificados manualmente em cada projeto
- Classificação por severidade
- Justificativa de por que cada problema é relevante

**B) Seção "Construção da Skill":**

- Decisões de design: como estruturou o SKILL.md e os arquivos de referência
- Quais anti-patterns incluiu no catálogo e por quê
- Como garantiu que a skill é agnóstica de tecnologia
- Desafios encontrados e como resolveu

**C) Seção "Resultados":**

- Resumo dos relatórios de auditoria dos 3 projetos (quantos findings por severidade em cada)
- Comparação antes/depois da estrutura de cada projeto
- Checklist de validação preenchido para cada projeto
- Screenshots ou logs mostrando as aplicações rodando após refatoração
- Observações sobre como a skill se comportou em stacks diferentes

**D) Seção "Como Executar":**

- Pré-requisitos (a ferramenta escolhida — Claude Code, Gemini CLI ou Codex — instalada e configurada)
- Comandos para executar a skill em cada projeto
- Como validar que a refatoração funcionou

#### Ordem de execução sugerida

**1. Analisar os projetos manualmente**

Leia o código dos três projetos e documente os problemas encontrados.

**2. Criar a skill**

Escreva o SKILL.md e os arquivos de referência.

**3. Executar nos 3 projetos**

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

Salve a saída da Fase 2 de cada projeto em `reports/audit-project-{1,2,3}.md`.

**4. Iterar**

Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

### 8.7 Critérios de Aceite

A skill deve atingir os seguintes mínimos em **todos os 3 projetos**:

| Critério | Requisito |
|---|---|
| Fase 1 detecta stack corretamente | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 encontra >= 5 findings | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 inclui pelo menos 1 CRITICAL ou HIGH | OBRIGATÓRIO (3/3 projetos) |
| Fase 3 aplicação funciona após refatoração | OBRIGATÓRIO (3/3 projetos) |

**IMPORTANTE:** Todos os critérios devem ser atingidos nos 3 projetos, não apenas em um!

> **Sobre o projeto 3 (task-manager-api):** Este projeto já possui alguma organização. "aplicação funciona" significa que a API inicia sem erros e todos os endpoints continuam respondendo corretamente.

### 8.8 Dicas Finais

- **Comece pela análise manual** — entender os problemas profundamente é essencial para criar uma skill que os detecte.
- **O SKILL.md é um prompt** — ele instrui o agente sobre o que fazer, enquanto os arquivos de referência fornecem o conhecimento de domínio.
- **Seja específico nos sinais de detecção** — "código ruim" não ajuda; "query SQL dentro de loop for" é acionável.
- **Teste incrementalmente** — não tente criar a skill perfeita de primeira.
- **A skill deve ser copiável** — se ela só funciona em um projeto específico, está acoplada demais. Teste nos 3 projetos para validar.
- **Projetos diferentes exigem adaptação** — a Fase 3 de um projeto já parcialmente organizado não vai ter as mesmas transformações de um monolito. Sua skill deve se adaptar ao contexto.
- **Pedir confirmação na Fase 2 é obrigatório** — o humano deve revisar o relatório antes de qualquer modificação.
- **Consulte as referências do curso** — revise a documentação oficial da ferramenta escolhida e os materiais das aulas para relembrar a estrutura e anatomia de uma skill.