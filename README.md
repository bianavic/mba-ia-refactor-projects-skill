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
- [5. Resultados](#5-resultados)
  - [5.1 Resumo das Auditorias](#51-resumo-das-auditorias)
  - [5.2 code-smells-project](#52-code-smells-project)
  - [5.3 ecommerce-api-legacy](#53-ecommerce-api-legacy)
  - [5.4 task-manager-api](#54-task-manager-api)
  - [5.5 Comparação Antes e Depois](#55-comparação-antes-e-depois)
  - [5.6 Comportamento entre Diferentes Stacks](#56-comportamento-entre-diferentes-stacks)
- [6. Estrutura Final do Projeto](#6-estrutura-final-do-projeto)
- [7. Referências](#7-referências)
- [8. Instruções Originais do Desafio](#8-instruções-originais-do-desafio)
  - [8.1 Objetivo](#81-objetivo)
  - [8.2 Contexto](#82-contexto)
  - [8.3 Tecnologias Obrigatórias](#83-tecnologias-obrigatórias)
  - [8.4 Requisitos](#84-requisitos)
  - [8.5 Entregável](#85-entregável)
  - [8.6 Estrutura do Repositório](#86-estrutura-do-repositório)
  - [8.7 Critérios de Aceite](#86-critérios-de-aceite)
  - [8.8 Dicas Finais](#87-dicas-finais)

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
| **Domínio** | LMS — E-learning (usuários, cursos, matrículas, pagamentos, checkout) |
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

## 3. Construção da Skill
## 4. Como Executar
## 5. Resultados
## 6. Estrutura Final do Projeto

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