# Refatoração Arquitetural Automatizada — `refactor-arch`

> Enunciado original preservado em [`docs/original-challenge.md`](docs/original-challenge.md).

## Sumário

1. [Análise Manual](#1-análise-manual)
2. [Construção da Skill](#2-construção-da-skill)
3. [Resultados](#3-resultados)
4. [Como Executar](#4-como-executar)

## 1. Análise Manual

Os três projetos foram lidos à mão antes de a skill existir: 8 achados no primeiro e 9 em cada um dos
outros (o enunciado pede no mínimo 5, com ao menos 1 CRITICAL ou HIGH, 2 MEDIUM e 2 LOW). As linhas se referem ao código original
do boilerplate, antes da Fase 3. Descrição, impacto e validação em execução de cada achado estão em
[`docs/manual-analysis.md`](docs/manual-analysis.md).

### 1.1 `code-smells-project` — Python/Flask, e-commerce

4 arquivos, ~780 linhas, camadas separadas só por arquivo (sem pastas de camada) · CRITICAL 3 · HIGH 1 · MEDIUM 2 · LOW 2

| Severidade | Achado | Local | Por que importa |
|---|---|---|---|
| CRITICAL | SQL Injection generalizada | `models.py` (ex.: `:47-50`, `:109-111`, `:289-299`) | Campos do cliente (nome, descrição, categoria, e-mail, senha, ids do pedido, busca) são concatenados no SQL: sem autenticação, dá para entrar sem senha, ler qualquer tabela, alterar todos os produtos e criar uma conta admin. |
| CRITICAL | `SECRET_KEY` hardcoded e devolvida em `/health` | `app.py:7-8,88`, `controllers.py:285-289` | O segredo que assina sessões está no repositório e no corpo de uma resposta pública; `DEBUG=True` fixo. |
| CRITICAL | Senha em texto plano, devolvida nas respostas | `database.py:31,75-83`, `models.py:83,99,105-111,122-128` | Gravada como digitada, comparada em claro no SQL e incluída no JSON de `GET /usuarios`: uma chamada entrega a credencial de todas as contas. |
| HIGH | God Class / sem separação MVC | `models.py`, `controllers.py` | Os 4 domínios vivem num arquivo e os controllers misturam parsing, validação, SQL e notificação; nada é testável isoladamente. É HIGH, não CRITICAL, porque rotas, controllers e SQL já estão em arquivos separados. |
| MEDIUM | N+1 no histórico de pedidos | `models.py:171-233` | Um cursor por pedido e outro por item, em loops aninhados: uma listagem dispara dezenas de queries. |
| MEDIUM | Listagens sem paginação | `controllers.py:5-12,128-134,229-235` | `/produtos`, `/usuarios` e `/pedidos` devolvem a tabela inteira. |
| LOW | `print()` como log | `controllers.py:8,11,57,61,106,161,179,182,208-210,219,248,250`, `app.py:56,83-86` | Sem nível, estrutura nem rotação. |
| LOW | Categorias válidas hardcoded | `controllers.py:52` | Uma categoria nova exige mudar o código. |

### 1.2 `ecommerce-api-legacy` — Node.js/Express, LMS com checkout

3 arquivos, ~180 linhas, sem separação de camadas · CRITICAL 4 · HIGH 1 · MEDIUM 2 · LOW 2

| Severidade | Achado | Local | Por que importa |
|---|---|---|---|
| CRITICAL | Segredos de produção hardcoded | `src/utils.js:2-5` | Usuário e senha do banco e a chave `pk_live_…` do gateway estão no código; a chave ainda vai para o log a cada checkout (`src/AppManager.js:45`). |
| CRITICAL | Hash de senha falso | `src/utils.js:17-23`, usado em `src/AppManager.js:68` | `badCrypto` devolve os 2 primeiros caracteres do base64 da senha repetidos: senhas que começam igual têm o mesmo "hash", e quem lê a tabela recupera o começo da senha decodificando o base64. |
| CRITICAL | Número completo do cartão no log | `src/AppManager.js:33,45` | Cada checkout imprime o cartão inteiro, sem máscara, junto com a chave do gateway: dado PCI-DSS em todo destino de log. |
| CRITICAL | God Class | `src/AppManager.js:4-139` | Schema, seed, rotas e regra de pagamento na mesma classe, sem camada intermediária: é o exemplo de CRITICAL do enunciado. |
| HIGH | Estado global mutável | `src/utils.js:9-10,14`, `src/AppManager.js:2` | `globalCache` acumula uma entrada por usuário, compartilhada por todas as requisições, sem limite nem expiração; `totalRevenue` é exportado por valor e nunca é atualizado. |
| MEDIUM | N+1 em cascata no relatório financeiro | `src/AppManager.js:80-129` | Uma query por curso, e por matrícula uma de usuário e outra de pagamento, aninhadas em callbacks. |
| MEDIUM | Relatório financeiro sem paginação | `src/AppManager.js:80-129` | Todos os cursos e todas as matrículas numa resposta; o payload cresce com cursos × matrículas. |
| LOW | `console.log` como log | `src/utils.js:13`, `src/AppManager.js:45` | Sem nível nem estrutura. |
| LOW | Idiomas misturados | `src/AppManager.js` | Mensagens em pt-BR e identificadores em inglês, sem convenção. |

### 1.3 `task-manager-api` — Python/Flask, gerenciador de tarefas

15 arquivos, ~1160 linhas, já com `models/`, `routes/`, `services/` e `utils/` · CRITICAL 3 · HIGH 1 · MEDIUM 3 · LOW 2

| Severidade | Achado | Local | Por que importa |
|---|---|---|---|
| CRITICAL | `SECRET_KEY` e senha SMTP hardcoded | `app.py:13`, `services/notification_service.py:7-10` | O segredo da aplicação e a credencial de e-mail estão literais no código e no histórico do git. |
| CRITICAL | Senha com MD5 sem salt | `models/user.py:27-32` | MD5 é quebrado e, sem salt, cai em rainbow table. |
| CRITICAL | Hash de senha devolvido nas respostas | `models/user.py:16-25` (`to_dict`), servido em `routes/user_routes.py:33,85-86,129,209` | `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login` entregam o hash a qualquer cliente; somado ao MD5, facilita o ataque offline. |
| HIGH | Regra `is_overdue` duplicada nas rotas | `models/task.py:50-60`, reescrita em `routes/task_routes.py:30-39,71-80,283-287`, `routes/user_routes.py:171-180`, `routes/report_routes.py:33-43,132-136` | As pastas existem, mas a regra de domínio vive nas rotas, escrita 6 vezes, e pode divergir quando alguém corrigir só uma cópia. |
| MEDIUM | Serviço de notificação nunca usado | `services/notification_service.py` | Parece uma funcionalidade pronta, mas nenhuma rota o importa; engana quem lê a estrutura. |
| MEDIUM | Queries N+1 nas listagens e relatórios | `routes/task_routes.py:14-51`, `routes/user_routes.py:14-22`, `routes/report_routes.py:53-56,161-163` | `GET /tasks` faz uma query de usuário e outra de categoria por task (2N+1). |
| MEDIUM | Listagens e relatórios sem paginação | `routes/task_routes.py:11-14`, `routes/user_routes.py:10-12`, `routes/report_routes.py:12-101` | Varrem a tabela inteira a cada chamada. |
| LOW | `print()` como log | `routes/task_routes.py`, `routes/user_routes.py`, `services/notification_service.py`, `utils/helpers.py:39-41` | Sem nível nem estrutura. |
| LOW | Imports não utilizados | `routes/task_routes.py:7` (`json, os, sys, time`), `routes/user_routes.py:6` (`hashlib, json`), `routes/report_routes.py:7-8` (`format_date, calculate_percentage, json`), `models/task.py:3` (`json`), `utils/helpers.py:3-7` (`os, json, sys, math, hashlib`), `app.py:7` (`os, sys, json`) | Ruído que esconde as dependências reais de cada arquivo. |

### 1.4 Padrões que se repetem

Apesar de stacks e níveis de organização diferentes, os três projetos convergem para os mesmos grupos de problema, o que moldou diretamente o catálogo de anti-patterns da skill:

- **Segredos e criptografia:** todos os 3 têm segredo/`SECRET_KEY` hardcoded; 2 dos 3 (`code-smells-project`, `ecommerce-api-legacy`) têm senha em texto plano ou hash quebrado/reversível, e o `task-manager-api` usa MD5 sem salt — a mesma classe de falha (catalogada depois como AP-03) em 3 implementações diferentes.
- **Vazamento de dado sensível:** `code-smells-project` e `task-manager-api` devolvem senha (plana ou hash) em respostas de endpoint (catalogado depois como AP-04); no `ecommerce-api-legacy` o dado vazado é o número completo do cartão e a chave de pagamento no log (AP-18).
- **Ausência total ou parcial de separação de camadas:** só o `ecommerce-api-legacy` é monolítico (uma God Class com banco, rotas e regra). O `code-smells-project` separa por arquivo (`app.py`, `controllers.py`, `models.py`), mas a responsabilidade vaza: há SQL em `app.py` e nos controllers e regra de domínio em `models.py`. O `task-manager-api` já tem pastas `models/routes/services/utils`, mas a disciplina de responsabilidade por camada não é seguida — a regra de negócio vaza para as rotas do mesmo jeito.
- **Performance:** N+1 e ausência de paginação aparecem nos 3 projetos, sempre em endpoints de listagem/relatório.
- **Observabilidade:** os 3 usam `print()`/`console.log` como logging.

Essa repetição é o motivo pelo qual o catálogo de anti-patterns foi desenhado como uma lista de sinais de detecção agnósticos de linguagem, e não como regras específicas de Flask ou Express: o mesmo `AP-01` (SQL Injection) precisa reconhecer tanto `"...WHERE id = " + str(id)` em Python quanto template literals em JavaScript.

## 2. Construção da Skill

## 3. Resultados

## 4. Como Executar
